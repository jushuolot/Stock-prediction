import unittest
from datetime import date

import numpy as np
import pandas as pd

from src.analysis.market_outlook import (
    IndexSnapshot,
    _crash_prob_from_signals,
    _outlook_labels,
    analyze_stock_long_term,
    compute_market_breadth,
)


class TestMarketOutlook(unittest.TestCase):
    def test_crash_prob_high_in_bear(self):
        indices = [
            IndexSnapshot(
                "000001.SS", "上证指数", "A股", 3000, -5.0, -8.0, -10.0, False, "空头", 1.5
            ),
            IndexSnapshot(
                "^GSPC", "标普500", "美股", 5000, -3.0, -4.0, -6.0, False, "空头", 1.2
            ),
        ]
        prob, drivers = _crash_prob_from_signals(indices, breadth_adv=30.0)
        self.assertGreaterEqual(prob, 45)
        self.assertTrue(drivers)

    def test_crash_prob_lower_in_bull(self):
        indices = [
            IndexSnapshot(
                "000001.SS", "上证指数", "A股", 3200, 2.0, 5.0, -1.0, True, "多头", 1.0
            ),
        ]
        prob, _ = _crash_prob_from_signals(indices, breadth_adv=65.0)
        self.assertLess(prob, 40)

    def test_outlook_labels(self):
        o2, o48, label = _outlook_labels(60, [])
        self.assertEqual(label, "偏高")
        self.assertIn("偏空", o2)

    def test_stock_long_term_uptrend(self):
        n = 90
        close = 10.0 + np.cumsum(np.random.default_rng(1).normal(0.05, 0.2, n))
        df = pd.DataFrame({"收盘": close, "成交量": np.full(n, 1e6), "日期": range(n)})
        lo = analyze_stock_long_term(df, code="600519", name="茅台")
        self.assertIsNotNone(lo)
        assert lo is not None
        self.assertGreaterEqual(lo.trend_score, 50)

    def test_breadth_from_ranking(self):
        df = pd.DataFrame({"涨跌幅%": [1, 2, -1, 3, -2, 0.5]})
        adv, _ = compute_market_breadth(lambda: (df, "test"))
        self.assertAlmostEqual(adv or 0, 66.7, delta=1)


if __name__ == "__main__":
    unittest.main()
