"""新鲜度校验与多源优选单元测试。"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch

import pandas as pd

from src.providers import fresh_fetch

_CN_TZ = timezone(timedelta(hours=8))


def _df_on(d: date) -> pd.DataFrame:
    return pd.DataFrame({"日期": [pd.Timestamp(d)], "收盘": [100.0]})


class TestFreshFetch(unittest.TestCase):
    def test_expected_bar_monday_morning(self):
        now = datetime(2026, 6, 8, 10, 0, tzinfo=_CN_TZ)  # Mon
        lo, hi = fresh_fetch.expected_latest_bar_date(now=now)
        self.assertEqual(lo, date(2026, 6, 5))  # Fri
        self.assertEqual(hi, date(2026, 6, 8))

    def test_expected_bar_monday_after_close(self):
        now = datetime(2026, 6, 8, 16, 0, tzinfo=_CN_TZ)
        lo, hi = fresh_fetch.expected_latest_bar_date(now=now)
        self.assertEqual(lo, date(2026, 6, 8))
        self.assertEqual(hi, date(2026, 6, 8))

    def test_expected_bar_saturday(self):
        now = datetime(2026, 6, 6, 12, 0, tzinfo=_CN_TZ)  # Sat
        lo, hi = fresh_fetch.expected_latest_bar_date(now=now)
        self.assertEqual(lo, date(2026, 6, 5))
        self.assertEqual(hi, date(2026, 6, 5))

    def test_is_bar_fresh_rejects_stale_yahoo_day(self):
        now = datetime(2026, 6, 8, 16, 0, tzinfo=_CN_TZ)
        self.assertFalse(fresh_fetch.is_bar_fresh(date(2026, 6, 5), now=now))
        self.assertTrue(fresh_fetch.is_bar_fresh(date(2026, 6, 8), now=now))

    def test_is_bar_fresh_before_close_accepts_yesterday(self):
        now = datetime(2026, 6, 8, 10, 0, tzinfo=_CN_TZ)
        self.assertTrue(fresh_fetch.is_bar_fresh(date(2026, 6, 5), now=now))

    def test_fetch_a_kline_fresh_skips_stale_yahoo(self):
        now = datetime(2026, 6, 8, 16, 0, tzinfo=_CN_TZ)
        fresh_df = _df_on(date(2026, 6, 8))
        stale_df = _df_on(date(2026, 6, 5))

        with (
            patch.object(fresh_fetch, "_try_em_kline", return_value=None),
            patch.object(fresh_fetch, "_try_sina_kline", return_value=None),
            patch.object(fresh_fetch, "_try_tencent_kline", return_value=(fresh_df, "腾讯财经")),
            patch.object(fresh_fetch, "_try_yahoo_kline", return_value=(stale_df, "Yahoo Finance")),
        ):
            df, src = fresh_fetch.fetch_a_kline_fresh(
                "600519",
                kline="日线",
                start=date(2026, 5, 1),
                end=date(2026, 6, 8),
                now=now,
            )
        self.assertEqual(src, "腾讯财经")
        self.assertEqual(fresh_fetch.last_bar_date(df), date(2026, 6, 8))

    def test_fetch_a_kline_fresh_raises_when_all_stale(self):
        now = datetime(2026, 6, 8, 16, 0, tzinfo=_CN_TZ)
        with (
            patch.object(fresh_fetch, "_try_em_kline", return_value=None),
            patch.object(fresh_fetch, "_try_sina_kline", return_value=None),
            patch.object(fresh_fetch, "_try_tencent_kline", return_value=None),
            patch.object(fresh_fetch, "_try_yahoo_kline", return_value=None),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                fresh_fetch.fetch_a_kline_fresh(
                    "600519",
                    kline="日线",
                    start=date(2026, 5, 1),
                    end=date(2026, 6, 8),
                    now=now,
                )
        self.assertIn("新鲜", str(ctx.exception))

    def test_is_ranking_fresh_with_probe(self):
        now = datetime(2026, 6, 8, 16, 0, tzinfo=_CN_TZ)
        ranking = pd.DataFrame(
            {
                "代码": ["600519", "600000", "000001"],
                "最新价": [1700.0, 10.0, 12.0],
                "涨跌幅%": [1.0, -0.5, 0.2],
            }
        )
        with patch("src.providers.tencent.fetch_quote_date", return_value=date(2026, 6, 8)):
            self.assertTrue(fresh_fetch.is_ranking_fresh(ranking, now=now))
        with patch("src.providers.tencent.fetch_quote_date", return_value=date(2026, 6, 5)):
            with patch.object(fresh_fetch, "fetch_a_kline_fresh", side_effect=RuntimeError("stale")):
                self.assertFalse(fresh_fetch.is_ranking_fresh(ranking, now=now))

    def test_market_data_uses_fresh_layer(self):
        from src.providers import market_data

        fresh_df = _df_on(date(2026, 6, 8))
        with patch(
            "src.providers.fresh_fetch.fetch_a_kline_fresh",
            return_value=(fresh_df, "东方财富"),
        ) as mock_fresh:
            df, src = market_data.fetch_kline_multi(
                kind="A",
                code="600519",
                kline="日线",
                start=date(2026, 5, 1),
                end=date(2026, 6, 8),
            )
        mock_fresh.assert_called_once()
        self.assertEqual(src, "东方财富")
        self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
