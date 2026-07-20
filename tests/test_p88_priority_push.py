"""P88 作战优先级 digest/webhook 推送单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.priority_queue import (
    format_priority_digest_section,
    rank_watchlist_priority,
)
from src.analysis.watch_alerts import compute_watch_alerts


class PriorityPushTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
        {"名称": "工行", "代码": "601398"},
    ]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "强",
            "fin_summary": "白酒",
            "updated_at": "2026-06-07 10:00:00",
        },
        "000858": {
            "pct": -4.0,
            "score": 35.0,
            "one_line": "弱",
            "fin_summary": "白酒",
            "updated_at": "2026-06-07 10:00:00",
        },
        "601398": {
            "pct": 0.5,
            "score": 55.0,
            "one_line": "平",
            "fin_summary": "银行",
            "updated_at": "2026-06-07 10:00:00",
        },
    }

    def test_format_priority_digest_top_three(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts, top_n=3)
        section = format_priority_digest_section(ranks, top_n=3)
        self.assertIn("## 今日优先关注 Top 3", section)
        self.assertIn("600519", section)
        self.assertIn("000858", section)
        self.assertEqual(len(ranks), 3)

    def test_format_priority_digest_empty(self):
        self.assertEqual(format_priority_digest_section([]), "")

    def test_digest_includes_priority_section(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts, top_n=3)
        section = format_priority_digest_section(ranks, top_n=3)
        md = build_watchlist_digest(self.wl, self.snaps, alerts=alerts, priority_section=section)
        self.assertIn("## 今日优先关注 Top 3", md)
        self.assertIn("## 使用说明", md)
        idx_prio = md.index("## 今日优先关注 Top 3")
        idx_use = md.index("## 使用说明")
        self.assertLess(idx_prio, idx_use)

    def test_digest_omits_priority_when_empty(self):
        md = build_watchlist_digest(self.wl, self.snaps, priority_section="")
        self.assertNotIn("## 今日优先关注 Top 3", md)

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

    def test_cron_dry_run_with_priority_flag(self):
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
                rc = self._run_cron(path, "--dry-run", "--with-priority")
        self.assertEqual(rc, 0)
        self.assertIn("with_priority=True", buf.getvalue())

    def test_cron_priority_env_var(self):
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
            with patch.dict("os.environ", {"STOCK_PUSH_PRIORITY": "1"}):
                with patch("sys.stdout", buf):
                    rc = self._run_cron(path, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("with_priority=True", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
