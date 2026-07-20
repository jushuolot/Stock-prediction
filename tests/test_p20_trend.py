"""P20 历史趋势单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.trend_summary import (
    collect_trend_points,
    format_trend_markdown,
    trend_delta,
)


class TrendSummaryTests(unittest.TestCase):
    def _sample_store(self):
        log = [
            {
                "id": "a1",
                "at": "2026年06月06日 10:00:00",
                "kind": "insight",
                "label": "一键分析 茅台",
                "stocks": "600519,茅台",
            },
            {
                "id": "a2",
                "at": "2026年06月05日 10:00:00",
                "kind": "watchlist",
                "label": "刷新摘要",
                "stocks": "600519",
            },
        ]
        snaps = [
            {
                "id": "a1",
                "state": {"watch_snapshots": {"600519": {"pct": 2.5, "score": 58.0}}},
            },
            {
                "id": "a2",
                "state": {"watch_snapshots": {"600519": {"pct": -1.0, "score": 52.0}}},
            },
        ]
        return log, snaps

    def test_collect_points_newest_first(self):
        log, snaps = self._sample_store()
        points = collect_trend_points(log, snaps, "600519", limit=5)
        self.assertEqual(len(points), 2)
        self.assertAlmostEqual(points[0].pct or 0, 2.5)
        self.assertAlmostEqual(points[0].score or 0, 58.0)
        self.assertEqual(points[0].at, "2026年06月06日 10:00:00")

    def test_delta_and_markdown(self):
        log, snaps = self._sample_store()
        points = collect_trend_points(log, snaps, "600519")
        score_d, pct_d = trend_delta(points)
        self.assertAlmostEqual(score_d or 0, 6.0)
        self.assertAlmostEqual(pct_d or 0, 3.5)
        md = format_trend_markdown(points, ticker="600519")
        self.assertIn("600519", md)
        self.assertIn("评分变化", md)

    def test_no_match(self):
        log, snaps = self._sample_store()
        self.assertEqual(collect_trend_points(log, snaps, "999999"), [])


if __name__ == "__main__":
    unittest.main()
