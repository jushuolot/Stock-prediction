"""P47 数据新鲜度徽章单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.util.freshness_badge import (
    freshness_badge,
    is_stale,
    normalize_stale_hours,
    parse_snapshot_time,
    snapshot_price,
)


class FreshnessTests(unittest.TestCase):
    def test_normalize_stale_hours(self):
        self.assertEqual(normalize_stale_hours(None), 24.0)
        self.assertEqual(normalize_stale_hours(48), 48.0)
        self.assertEqual(normalize_stale_hours(999), 168.0)

    def test_parse_snapshot_time(self):
        ts = parse_snapshot_time("2026年06月06日 12:30:45")
        self.assertIsNotNone(ts)
        self.assertEqual(ts.hour, 12)

    def test_is_stale(self):
        now = datetime(2026, 6, 6, 12, 0, 0)
        fresh = (now - timedelta(hours=2)).strftime("%Y年%m月%d日 %H:%M:%S")
        old = (now - timedelta(hours=30)).strftime("%Y年%m月%d日 %H:%M:%S")
        self.assertFalse(is_stale(fresh, stale_hours=24, now=now))
        self.assertTrue(is_stale(old, stale_hours=24, now=now))
        self.assertTrue(is_stale("", stale_hours=24, now=now))

    def test_freshness_badge(self):
        now = datetime(2026, 6, 6, 12, 0, 0)
        fresh = (now - timedelta(hours=1)).strftime("%Y年%m月%d日 %H:%M:%S")
        old = (now - timedelta(hours=48)).strftime("%Y年%m月%d日 %H:%M:%S")
        self.assertEqual(freshness_badge(fresh, stale_hours=24, now=now), "")
        self.assertIn("stale", freshness_badge(old, stale_hours=24, now=now))

    def test_snapshot_price(self):
        self.assertEqual(snapshot_price({"price": 10.5}), 10.5)
        self.assertEqual(snapshot_price({"收盘": 9.0}), 9.0)
        self.assertIsNone(snapshot_price({}))


if __name__ == "__main__":
    unittest.main()
