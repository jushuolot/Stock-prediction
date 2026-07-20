import unittest
from datetime import date

import numpy as np
import pandas as pd

from src.analysis.tomorrow_picks import (
    PATTERN_BREAKOUT,
    PATTERN_CONTINUATION,
    PATTERN_PULLBACK,
    analyze_tomorrow_from_kline,
    tomorrow_trading_date,
)


def _fake_kline(n: int = 80, *, last_pct: float = 1.5) -> pd.DataFrame:
    close = 10.0 + np.cumsum(np.random.default_rng(42).normal(0.02, 0.15, n))
    close[-1] = close[-2] * (1 + last_pct / 100.0)
    vol = np.full(n, 1e6)
    vol[-1] = 1.8e6
    return pd.DataFrame({"收盘": close, "成交量": vol})


class TestTomorrowPicks(unittest.TestCase):
    def test_tomorrow_date_skips_weekend(self):
        fri = date(2025, 6, 6)
        self.assertEqual(tomorrow_trading_date(from_day=fri), "2025-06-09")

    def test_continuation_scores_high(self):
        df = _fake_kline(last_pct=2.0)
        ta = analyze_tomorrow_from_kline(df, today_pct=2.0, turnover_pct=4.0)
        self.assertIsNotNone(ta)
        assert ta is not None
        self.assertGreaterEqual(ta.tomorrow_score, 58)
        self.assertIn(ta.pattern, (PATTERN_CONTINUATION, PATTERN_PULLBACK, PATTERN_BREAKOUT))

    def test_pullback_in_uptrend(self):
        df = _fake_kline(last_pct=-1.2)
        ta = analyze_tomorrow_from_kline(df, today_pct=-1.2, turnover_pct=2.0)
        self.assertIsNotNone(ta)
        assert ta is not None
        self.assertGreaterEqual(ta.tomorrow_score, 58)

    def test_limit_up_penalized(self):
        df = _fake_kline(last_pct=10.0)
        ta = analyze_tomorrow_from_kline(df, today_pct=10.0, turnover_pct=5.0)
        cont = analyze_tomorrow_from_kline(_fake_kline(last_pct=2.0), today_pct=2.0, turnover_pct=4.0)
        self.assertIsNotNone(cont)
        if ta is not None and cont is not None:
            self.assertLess(ta.tomorrow_score, cont.tomorrow_score)

    def test_too_short_returns_none(self):
        df = pd.DataFrame({"收盘": [1, 2, 3], "成交量": [1, 1, 1]})
        self.assertIsNone(analyze_tomorrow_from_kline(df, today_pct=1.0))


if __name__ == "__main__":
    unittest.main()
