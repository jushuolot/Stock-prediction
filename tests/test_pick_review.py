import unittest
from datetime import date, timedelta

import pandas as pd

from src.analysis.pick_review import (
    _forward_returns_from_kline,
    extract_pattern,
    pattern_score_adjustments_from_log,
    strategy_hints_from_reviews,
    Pick3dReview,
)


class TestPickReview(unittest.TestCase):
    def test_extract_pattern(self):
        self.assertEqual(extract_pattern("[趋势延续] 明日看延续"), "趋势延续")
        self.assertEqual(extract_pattern("", "买入"), "买入")

    def test_forward_returns(self):
        base = date(2025, 6, 1)
        dates = [base + timedelta(days=i) for i in range(6)]
        closes = [10.0, 10.0, 10.5, 10.2, 10.8, 11.0]
        df = pd.DataFrame({"日期": dates, "收盘": closes})
        out = _forward_returns_from_kline(df, base, horizon=3)
        self.assertAlmostEqual(out["pick_close"] or 0, 10.0)
        self.assertAlmostEqual(out["d1"] or 0, 0.0, places=1)
        self.assertAlmostEqual(out["d2"] or 0, 5.0, places=1)
        self.assertAlmostEqual(out["max"] or 0, 5.0, places=1)

    def test_pattern_adj_from_log(self):
        log = [
            {"pattern": "趋势延续", "verified": True, "hit": False},
            {"pattern": "趋势延续", "verified": True, "hit": False},
            {"pattern": "趋势延续", "verified": True, "hit": True},
            {"pattern": "突破在即", "verified": True, "hit": True},
        ]
        adj = pattern_score_adjustments_from_log(log)
        self.assertIn("趋势延续", adj)
        self.assertLess(adj["趋势延续"], 0)

    def test_strategy_hints(self):
        reviews = [
            Pick3dReview("2025-06-01", "600519", "茅台", "趋势延续", 10.0, 1.0, None, None, 1.0, True, ""),
            Pick3dReview("2025-06-01", "000001", "平安", "趋势延续", 10.0, -2.0, None, None, -2.0, False, ""),
        ]
        hints = strategy_hints_from_reviews(reviews)
        self.assertTrue(any("跑赢率" in h for h in hints))


if __name__ == "__main__":
    unittest.main()
