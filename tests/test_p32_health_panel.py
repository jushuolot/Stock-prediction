"""P32 健康面板逻辑单元测试。"""

from __future__ import annotations

import unittest

from src.ui.health_panel import (
    format_cache_stats_line,
    format_last_refresh_label,
    format_push_log_tail,
)
from src.util.fetch_cache import cache_stats, clear_fetch_cache, set_cached_snapshots


class HealthPanelHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_fetch_cache()

    def tearDown(self) -> None:
        clear_fetch_cache()

    def test_last_refresh_label(self):
        self.assertEqual(
            format_last_refresh_label({"query_label_watch": "2024-01-01 09:00:00"}),
            "2024-01-01 09:00:00",
        )
        self.assertEqual(
            format_last_refresh_label({"_auto_refresh_at": "2024-01-02 10:00:00"}),
            "2024-01-02 10:00:00",
        )
        self.assertEqual(format_last_refresh_label({}), "—")

    def test_cache_stats_line_empty(self):
        self.assertIn("0 条", format_cache_stats_line(cache_stats(now=1000.0)))

    def test_cache_stats_line_with_entries(self):
        set_cached_snapshots(["600519", "601398"], {"600519": {"pct": 1.0}}, now=1000.0)
        stats = cache_stats(now=1030.0)
        line = format_cache_stats_line(stats)
        self.assertIn("1 批", line)
        self.assertIn("30s", line)

    def test_push_log_tail(self):
        rows = [
            {"at": "t1", "channel": "webhook", "ok": True, "detail": "ok"},
            {"at": "t2", "channel": "email", "ok": False, "detail": "fail"},
        ]
        tail = format_push_log_tail(rows, limit=5)
        self.assertEqual(len(tail), 2)
        self.assertIn("✓", tail[0])
        self.assertIn("✗", tail[1])


if __name__ == "__main__":
    unittest.main()
