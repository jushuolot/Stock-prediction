"""P70 组合涨跌贡献单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.contribution import (
    compute_portfolio_contribution,
    contribution_table_rows,
)


class ContributionTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "1"},
        {"名称": "B", "代码": "2"},
    ]

    def test_equal_weight_portfolio_pct(self):
        snaps = {"1": {"pct": 10.0}, "2": {"pct": -4.0}}
        portfolio, rows = compute_portfolio_contribution(self.wl, snaps, {})
        self.assertAlmostEqual(portfolio or 0.0, 3.0, places=5)
        by_code = {r.code: r for r in rows}
        self.assertAlmostEqual(by_code["1"].contribution_pts or 0.0, 5.0, places=5)
        self.assertAlmostEqual(by_code["2"].contribution_pts or 0.0, -2.0, places=5)

    def test_custom_weights(self):
        snaps = {"1": {"pct": 10.0}, "2": {"pct": 5.0}}
        weights = {"1": 75.0, "2": 25.0}
        portfolio, rows = compute_portfolio_contribution(self.wl, snaps, weights)
        self.assertAlmostEqual(portfolio or 0.0, 8.75, places=5)
        by_code = {r.code: r for r in rows}
        self.assertAlmostEqual(by_code["1"].weight_pct, 75.0, places=5)
        self.assertAlmostEqual(by_code["1"].contribution_pts or 0.0, 7.5, places=5)
        self.assertAlmostEqual(by_code["2"].contribution_pts or 0.0, 1.25, places=5)

    def test_share_pct_sums_near_hundred(self):
        snaps = {"1": {"pct": 8.0}, "2": {"pct": -2.0}}
        portfolio, rows = compute_portfolio_contribution(self.wl, snaps, {})
        shares = [r.share_pct for r in rows if r.share_pct is not None]
        self.assertAlmostEqual(sum(shares), 100.0, places=4)

    def test_missing_pct_excluded_from_portfolio(self):
        snaps = {"1": {"pct": 6.0}, "2": {}}
        portfolio, rows = compute_portfolio_contribution(self.wl, snaps, {})
        self.assertAlmostEqual(portfolio or 0.0, 3.0, places=5)
        by_code = {r.code: r for r in rows}
        self.assertIsNone(by_code["2"].contribution_pts)

    def test_table_rows(self):
        snaps = {"1": {"pct": 4.0}, "2": {"pct": 2.0}}
        portfolio, table = contribution_table_rows(self.wl, snaps, {"1": 60.0, "2": 40.0})
        self.assertAlmostEqual(portfolio or 0.0, 3.2, places=5)
        self.assertEqual(len(table), 2)
        self.assertIn("贡献点", table[0])
        self.assertIn("贡献占比%", table[0])

    def test_empty_watchlist(self):
        portfolio, rows = compute_portfolio_contribution([], {}, {})
        self.assertIsNone(portfolio)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
