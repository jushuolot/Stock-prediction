"""P21 JSON 备份/导入单元测试。"""

from __future__ import annotations

import json
import unittest

from src.util.watchlist_backup import (
    SCHEMA,
    apply_backup_merge,
    backup_to_json_bytes,
    build_watch_backup,
    merge_watchlist,
    parse_backup_bytes,
)


class WatchBackupTests(unittest.TestCase):
    def test_build_and_parse(self):
        payload = build_watch_backup(
            watchlist=[{"名称": "A", "代码": "1", "类型": "A"}],
            watch_snapshots={"1": {"pct": 1.0, "score": 50.0}},
            watch_groups={"核心": ["1"]},
        )
        self.assertEqual(payload["schema"], SCHEMA)
        raw = backup_to_json_bytes(payload)
        parsed = parse_backup_bytes(raw)
        self.assertEqual(parsed["watchlist"][0]["代码"], "1")

    def test_merge_does_not_wipe(self):
        existing = [{"名称": "旧", "代码": "100", "类型": "A"}]
        incoming = [{"名称": "新", "代码": "200", "类型": "A"}]
        merged = merge_watchlist(existing, incoming)
        self.assertEqual(len(merged), 2)
        codes = {x["代码"] for x in merged}
        self.assertEqual(codes, {"100", "200"})

    def test_apply_backup_merge(self):
        wl, snaps, groups, notes, stats = apply_backup_merge(
            watchlist=[{"名称": "旧", "代码": "1", "类型": "A"}],
            watch_snapshots={"1": {"score": 40.0}},
            watch_groups={},
            watch_notes={"1": "旧笔记"},
            backup={
                "schema": SCHEMA,
                "watchlist": [{"名称": "新", "代码": "2", "类型": "A"}],
                "watch_snapshots": {"2": {"score": 55.0}},
                "watch_groups": {"观察": ["2"]},
                "watch_notes": {"2": "新笔记"},
            },
        )
        self.assertEqual(len(wl), 2)
        self.assertIn("2", snaps)
        self.assertIn("观察", groups)
        self.assertEqual(notes, {"1": "旧笔记", "2": "新笔记"})
        self.assertEqual(stats["watchlist_added"], 1)

    def test_invalid_schema(self):
        raw = json.dumps({"schema": "other"}).encode("utf-8")
        with self.assertRaises(ValueError):
            parse_backup_bytes(raw)


if __name__ == "__main__":
    unittest.main()
