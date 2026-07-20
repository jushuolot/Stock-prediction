"""P31 自选笔记导出单元测试。"""

from __future__ import annotations

import json
import unittest

from src.analysis.daily_digest import build_watchlist_digest, format_notes_digest_section
from src.util.watchlist_backup import build_watch_backup, backup_to_json_bytes
from src.util.watchlist_export import watchlist_to_csv_bytes


class NotesExportTests(unittest.TestCase):
    wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
    snaps = {
        "600519": {"pct": 1.2, "score": 70.0, "one_line": "强势"},
        "601398": {"pct": -0.5, "score": 45.0, "one_line": "震荡"},
    }
    notes = {"600519": "核心持仓", "601398": "观察"}

    def test_digest_includes_notes_section(self):
        md = build_watchlist_digest(self.wl, self.snaps, watch_notes=self.notes)
        self.assertIn("## 自选笔记", md)
        self.assertIn("核心持仓", md)
        self.assertIn("600519", md)

    def test_digest_omits_empty_notes(self):
        md = build_watchlist_digest(self.wl, self.snaps, watch_notes={})
        self.assertNotIn("## 自选笔记", md)
        self.assertEqual(format_notes_digest_section(self.wl, {}), "")

    def test_csv_includes_notes_column(self):
        csv = watchlist_to_csv_bytes(self.wl, self.snaps, watch_notes=self.notes)
        text = csv.decode("utf-8-sig")
        self.assertIn("笔记", text)
        self.assertIn("核心持仓", text)

    def test_backup_includes_watch_notes(self):
        payload = build_watch_backup(
            watchlist=self.wl,
            watch_snapshots=self.snaps,
            watch_notes=self.notes,
        )
        data = json.loads(backup_to_json_bytes(payload).decode("utf-8"))
        self.assertEqual(data["watch_notes"], self.notes)


if __name__ == "__main__":
    unittest.main()
