"""P77 一页纸 cron/webhook 推送单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.institutional_onepager import build_onepager_push_summary
from src.analysis.watch_alerts import compute_watch_alerts, top_alert_ticker


class OnepagerPushTests(unittest.TestCase):
    wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "强势",
            "fin_summary": "白酒 · ROE20%",
        },
        "601398": {"pct": -1.0, "score": 50.0, "one_line": "平", "fin_summary": "银行 · ROE10%"},
    }

    def test_top_alert_ticker_hot_first(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0)
        top = top_alert_ticker(alerts)
        self.assertIsNotNone(top)
        assert top is not None
        self.assertEqual(top.code, "600519")
        self.assertEqual(top.level, "hot")

    def test_onepager_push_summary_markdown(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0)
        top = top_alert_ticker(alerts)
        self.assertIsNotNone(top)
        assert top is not None
        md = build_onepager_push_summary(
            name=top.name,
            code=top.code,
            snap=self.snaps[top.code],
            alert_message=top.message,
        )
        self.assertIn("机构式一页纸", md)
        self.assertIn("600519", md)
        self.assertIn("触发提醒", md)

    def test_digest_includes_onepager_section(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0)
        top = top_alert_ticker(alerts)
        self.assertIsNotNone(top)
        assert top is not None
        section = build_onepager_push_summary(
            name=top.name,
            code=top.code,
            snap=self.snaps[top.code],
            alert_message=top.message,
        )
        md = build_watchlist_digest(self.wl, self.snaps, alerts=alerts, onepager_section=section)
        self.assertIn("## 机构式一页纸", md)
        self.assertIn("## 使用说明", md)
        idx_one = md.index("## 机构式一页纸")
        idx_use = md.index("## 使用说明")
        self.assertLess(idx_one, idx_use)

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

    def test_cron_dry_run_with_onepager(self):
        store = {
            "watchlist": self.wl,
            "latest": {"watch_snapshots": self.snaps, "user_prefs": {"alert_pct_up": 5.0}},
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "user_history.json"
            path.write_text(json.dumps(store), encoding="utf-8")
            rc = self._run_cron(path, "--dry-run", "--with-onepager")
        self.assertEqual(rc, 0)

    def test_cron_onepager_skipped_without_alerts(self):
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
            rc = self._run_cron(path, "--dry-run", "--with-onepager")
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
