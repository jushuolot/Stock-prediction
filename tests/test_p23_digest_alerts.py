"""P23 定时摘要含提醒单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.daily_digest import build_watchlist_digest, format_alerts_digest_section
from src.analysis.watch_alerts import compute_watch_alerts


class DigestAlertsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
        self.snaps = {
            "600519": {"pct": 6.0, "score": 70.0, "one_line": "涨"},
            "601398": {"pct": -1.0, "score": 50.0, "one_line": "平"},
        }

    def test_alerts_section_markdown(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0)
        section = format_alerts_digest_section(alerts)
        self.assertIn("## 提醒摘要", section)
        self.assertIn("600519", section)
        self.assertIn("🔥", section)

    def test_build_digest_includes_alerts(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0)
        md = build_watchlist_digest(self.wl, self.snaps, alerts=alerts)
        self.assertIn("## 提醒摘要", md)
        self.assertIn("600519", md)
        self.assertIn("## 使用说明", md)

    def test_build_digest_no_alerts_omits_section(self):
        md = build_watchlist_digest(self.wl, self.snaps, alerts=[])
        self.assertNotIn("## 提醒摘要", md)

    def test_empty_alerts_section(self):
        self.assertEqual(format_alerts_digest_section([]), "")

    def _run_cron(self, path: Path, *extra_args: str) -> int:
        from scripts import push_digest_cron

        argv = ["push_digest_cron.py", *extra_args]
        with patch.object(push_digest_cron, "history_file_path", return_value=path):
            old = sys.argv
            try:
                sys.argv = argv
                return push_digest_cron.main()
            finally:
                sys.argv = old

    def test_alerts_only_skips_when_empty(self):
        store = {
            "watchlist": self.wl,
            "latest": {
                "watch_snapshots": {"600519": {"pct": 1.0, "score": 50.0}},
                "user_prefs": {},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "user_history.json"
            path.write_text(json.dumps(store), encoding="utf-8")
            rc = self._run_cron(path, "--alerts-only")
        self.assertEqual(rc, 0)

    def test_dry_run_with_alerts_in_digest(self):
        store = {
            "watchlist": self.wl,
            "latest": {"watch_snapshots": self.snaps, "user_prefs": {"alert_pct_up": 5.0}},
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "user_history.json"
            path.write_text(json.dumps(store), encoding="utf-8")
            rc = self._run_cron(path, "--dry-run")
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
