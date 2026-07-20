"""P86 合并导出包逻辑单元测试。"""

from __future__ import annotations

import io
import unittest
import zipfile

from src.analysis.priority_queue import rank_watchlist_priority
from src.analysis.watch_alerts import compute_watch_alerts
from src.export.priority_bundle import (
    build_priority_export_bundle_md,
    build_priority_export_bundle_zip,
)


class ExportBundleTests(unittest.TestCase):
    wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "强",
            "fin_summary": "白酒",
            "updated_at": "2026-06-07 10:00:00",
        },
        "601398": {
            "pct": -1.0,
            "score": 35.0,
            "one_line": "弱",
            "updated_at": "2026-06-07 10:00:00",
        },
    }

    def test_combined_md_has_three_parts(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts)
        md = build_priority_export_bundle_md(
            self.wl,
            self.snaps,
            ranks=ranks,
            alerts=alerts,
            query_label="2026-06-07",
        )
        self.assertIn("# 📋 今日作战清单", md)
        self.assertIn("# 自选股今日速览", md)
        self.assertIn("机构式一页纸", md)
        self.assertIn("600519", md)
        self.assertIn("合并导出", md)

    def test_zip_contains_expected_files(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts)
        data, fname = build_priority_export_bundle_zip(
            self.wl,
            self.snaps,
            ranks=ranks,
            alerts=alerts,
            query_label="2026-06-07",
        )
        self.assertTrue(fname.endswith(".zip"))
        self.assertTrue(data.startswith(b"PK"))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
        self.assertIn("今日作战清单.md", names)
        self.assertIn("自选股速览.md", names)
        self.assertIn("一页纸_600519.md", names)
        self.assertTrue(any(n.startswith("合并导出_") and n.endswith(".md") for n in names))

    def test_top_priority_onepager_code(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts)
        top = ranks[0]
        md = build_priority_export_bundle_md(
            self.wl,
            self.snaps,
            priority=top,
            alerts=alerts,
            query_label="test",
        )
        self.assertIn(top.code, md)


if __name__ == "__main__":
    unittest.main()
