"""P83 风险汇总推送单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.daily_digest import (
    build_watchlist_digest,
    format_risk_digest_section,
)
from src.analysis.watch_alerts import compute_watch_alerts


class RiskDigestTests(unittest.TestCase):
    wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "涨",
            "updated_at": "2026-06-07 10:00:00",
        },
        "601398": {
            "pct": -1.0,
            "score": 35.0,
            "one_line": "弱",
            "updated_at": "2026-06-07 10:00:00",
        },
    }

    def test_risk_section_with_triggered_flags(self):
        alerts = compute_watch_alerts(
            self.wl,
            self.snaps,
            pct_up=5.0,
            score_low=40.0,
        )
        section = format_risk_digest_section(self.wl, self.snaps, alerts)
        self.assertIn("## 风险雷达摘要", section)
        self.assertIn("共 **", section)
        self.assertIn("600519", section)

    def test_risk_section_empty_without_alerts(self):
        self.assertEqual(format_risk_digest_section(self.wl, self.snaps, []), "")

    def test_build_digest_includes_risk_when_alerts(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        md = build_watchlist_digest(self.wl, self.snaps, alerts=alerts)
        self.assertIn("## 提醒摘要", md)
        self.assertIn("## 风险雷达摘要", md)
        idx_alert = md.index("## 提醒摘要")
        idx_risk = md.index("## 风险雷达摘要")
        idx_use = md.index("## 使用说明")
        self.assertLess(idx_alert, idx_risk)
        self.assertLess(idx_risk, idx_use)

    def test_build_digest_omits_risk_without_alerts(self):
        md = build_watchlist_digest(self.wl, self.snaps, alerts=[])
        self.assertNotIn("## 风险雷达摘要", md)

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

    def test_cron_dry_run_includes_risk_summary(self):
        store = {
            "watchlist": self.wl,
            "latest": {
                "watch_snapshots": self.snaps,
                "user_prefs": {"alert_pct_up": 5.0, "alert_score_low": 40.0},
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "user_history.json"
            path.write_text(json.dumps(store), encoding="utf-8")
            from io import StringIO

            buf = StringIO()
            with patch("sys.stdout", buf):
                rc = self._run_cron(path, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("alerts=", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
