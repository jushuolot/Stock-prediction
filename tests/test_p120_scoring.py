import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from src.analysis.daily_picks import (
    GLOBAL_PCT_ABS_MAX,
    DailyPick,
    _is_weird_global_ticker,
    rank_global_from_ranking,
)
from src.analysis.stock_quality import QualityVerdict
from src.analysis.tomorrow_picks import (
    PATTERN_BREAKOUT,
    _a_buy_threshold,
    _fund_tag_from_quality,
    analyze_tomorrow_from_kline,
)


def _fake_kline(n: int = 80, *, last_pct: float = 1.5) -> pd.DataFrame:
    close = 10.0 + np.cumsum(np.random.default_rng(7).normal(0.02, 0.15, n))
    close[-1] = close[-2] * (1 + last_pct / 100.0)
    vol = np.full(n, 1e6)
    vol[-1] = 2.0e6
    return pd.DataFrame({"收盘": close, "成交量": vol})


class TestP120GlobalSanitize(unittest.TestCase):
    def test_weird_hk_warrant_code(self):
        self.assertTrue(_is_weird_global_ticker("55224.HK", "某权证", "港股"))

    def test_normal_hk_code_ok(self):
        self.assertFalse(_is_weird_global_ticker("00700", "腾讯", "港股"))

    def test_global_pct_abs_max_constant(self):
        self.assertEqual(GLOBAL_PCT_ABS_MAX, 50.0)

    @patch("src.analysis.global_anomaly.analyze_one_mover_fast")
    def test_rank_global_skips_absurd_pct(self, mock_fast):
        mock_fast.return_value = MagicMock(anomaly_score=80.0, capital=MagicMock(as_dict=lambda: {}))
        df = pd.DataFrame(
            [
                {"代码": "00700", "名称": "腾讯", "涨跌幅%": 915.0, "最新价": 300.0},
                {"代码": "09988", "名称": "阿里", "涨跌幅%": 3.5, "最新价": 80.0},
            ]
        )
        picks, stats = rank_global_from_ranking(df, market_label="港股", max_picks=2)
        self.assertEqual(len(picks), 1)
        self.assertEqual(picks[0].code, "09988")
        self.assertGreaterEqual(int(stats.get("skipped_anomaly") or 0), 1)


class TestP120TomorrowScoring(unittest.TestCase):
    def test_breakout_score_capped(self):
        df = _fake_kline(last_pct=3.0)
        ta = analyze_tomorrow_from_kline(df, today_pct=3.0, turnover_pct=5.0)
        self.assertIsNotNone(ta)
        assert ta is not None
        if ta.pattern == PATTERN_BREAKOUT:
            self.assertLessEqual(ta.tomorrow_score, 86.0)

    def test_overall_score_cap_86(self):
        df = _fake_kline(last_pct=2.0)
        ta = analyze_tomorrow_from_kline(df, today_pct=2.0, turnover_pct=6.0)
        self.assertIsNotNone(ta)
        assert ta is not None
        self.assertLessEqual(ta.tomorrow_score, 86.0)

    def test_301_buy_threshold_stricter(self):
        qv_ok = QualityVerdict(
            ok=True, score_delta=2.0, tags=("公募基金新进",), reject_reason="",
            shareholder=None, fund_holdings=None, total_cap_yuan=None, pe_ttm=None,
        )
        qv_weak = QualityVerdict(
            ok=True, score_delta=0.0, tags=(), reject_reason="",
            shareholder=None, fund_holdings=None, total_cap_yuan=None, pe_ttm=None,
        )
        self.assertTrue(_a_buy_threshold("301418", 83.0, qv_ok))
        self.assertFalse(_a_buy_threshold("301418", 83.0, qv_weak))
        self.assertFalse(_a_buy_threshold("301418", 80.0, qv_ok))

    def test_fund_tag_from_quality(self):
        qv = QualityVerdict(
            ok=True, score_delta=3.0,
            tags=("创业板", "公募基金新进", "基金增仓"),
            reject_reason="", shareholder=None, fund_holdings=None,
            total_cap_yuan=None, pe_ttm=None,
        )
        self.assertIn("基金", _fund_tag_from_quality(qv) or "")

    def test_daily_pick_fund_tag_field(self):
        p = DailyPick(
            code="600519", name="茅台", score=80.0, pct=1.0,
            signal="买入", hold_days="3天", reason="test",
            fund_tag="公募基金新进",
        )
        self.assertEqual(p.as_dict().get("fund_tag"), "公募基金新进")


if __name__ == "__main__":
    unittest.main()
