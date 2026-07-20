"""P92 一键全开推送（STOCK_PUSH_ALL / --push-all）单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.institutional_onepager import build_onepager_push_summary
from src.analysis.priority_queue import (
    format_priority_digest_section,
    rank_watchlist_priority,
)
from src.analysis.watch_alerts import compute_watch_alerts, top_alert_ticker


class PushAllTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
    ]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "强",
            "fin_summary": "白酒",
        },
        "000858": {
            "pct": -4.0,
            "score": 35.0,
            "one_line": "弱",
            "fin_summary": "白酒",
        },
    }

    def _run_cron(self, path: Path, *extra_args: str) -> tuple[int, str]:
        from scripts import push_digest_cron

        argv = ["push_digest_cron.py", *extra_args]
        from io import StringIO

        buf = StringIO()
        with patch.object(push_digest_cron, "history_file_path", return_value=path):
            old = sys.argv
            try:
                sys.argv = argv
                with patch("sys.stdout", buf):
                    rc = push_digest_cron.main()
            finally:
                sys.argv = old
        return rc, buf.getvalue()

    def test_push_all_flag_enables_sections(self):
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
            rc, out = self._run_cron(path, "--dry-run", "--push-all")
        self.assertEqual(rc, 0)
        self.assertIn("push_all=True", out)
        self.assertIn("with_onepager=True", out)
        self.assertIn("with_priority=True", out)

    def test_push_all_env_var(self):
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
            with patch.dict("os.environ", {"STOCK_PUSH_ALL": "1"}):
                rc, out = self._run_cron(path, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("push_all=True", out)
        self.assertIn("with_onepager=True", out)
        self.assertIn("with_priority=True", out)

    def test_digest_push_all_sections_present(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts, top_n=3)
        priority_section = format_priority_digest_section(ranks, top_n=3)
        top = top_alert_ticker(alerts)
        self.assertIsNotNone(top)
        assert top is not None
        onepager_section = build_onepager_push_summary(
            name=top.name,
            code=top.code,
            snap=self.snaps[top.code],
            alert_message=top.message,
        )
        md = build_watchlist_digest(
            self.wl,
            self.snaps,
            alerts=alerts,
            priority_section=priority_section,
            onepager_section=onepager_section,
        )
        self.assertIn("## 提醒摘要", md)
        self.assertIn("## 今日优先关注 Top 3", md)
        self.assertIn("## 机构式一页纸", md)


if __name__ == "__main__":
    unittest.main()
