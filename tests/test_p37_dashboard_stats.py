"""P37 dashboard_stats 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.dashboard_stats import compute_dashboard_stats


class DashboardStatsTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "1"},
        {"名称": "B", "代码": "2"},
        {"名称": "C", "代码": "3"},
    ]
    snaps = {
        "1": {"pct": 6.0, "score": 70.0},
        "2": {"pct": -3.0, "score": 35.0},
        "3": {"pct": 0.0, "score": 50.0},
    }

    def test_aggregate_counts(self):
        stats = compute_dashboard_stats(
            self.wl,
            self.snaps,
            pct_up=5.0,
            pct_down=-5.0,
            score_low=40.0,
            score_high=65.0,
        )
        self.assertEqual(stats.watch_count, 3)
        self.assertEqual(stats.snapshot_count, 3)
        self.assertEqual(stats.scored_count, 3)
        self.assertAlmostEqual(stats.avg_score, (70.0 + 35.0 + 50.0) / 3)
        self.assertEqual(stats.up_count, 1)
        self.assertEqual(stats.down_count, 1)
        self.assertEqual(stats.flat_count, 1)

    def test_alert_count(self):
        stats = compute_dashboard_stats(
            self.wl,
            self.snaps,
            pct_up=5.0,
            pct_down=-5.0,
            score_low=40.0,
            score_high=65.0,
        )
        self.assertGreaterEqual(stats.alert_count, 3)

    def test_empty_watchlist(self):
        stats = compute_dashboard_stats([], {})
        self.assertEqual(stats.watch_count, 0)
        self.assertIsNone(stats.avg_score)
        self.assertEqual(stats.alert_count, 0)

    def test_partial_snapshots(self):
        stats = compute_dashboard_stats(self.wl, {"1": self.snaps["1"]})
        self.assertEqual(stats.snapshot_count, 1)
        self.assertEqual(stats.scored_count, 1)
        self.assertAlmostEqual(stats.avg_score, 70.0)


if __name__ == "__main__":
    unittest.main()
