"""P89 首页作战入口单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.watch_alerts import compute_watch_alerts
from src.ui.priority_home import (
    PRIORITY_HOME_TITLE,
    PRIORITY_HOME_TOP_N,
    build_priority_home_labels,
    compute_priority_home_ranks,
    should_show_priority_home,
)


class PriorityHomeTests(unittest.TestCase):
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
            "updated_at": "2026-06-07 10:00:00",
        },
        "000858": {
            "pct": -4.0,
            "score": 35.0,
            "one_line": "弱",
            "updated_at": "2026-06-07 10:00:00",
        },
        "601398": {
            "pct": 0.5,
            "score": 55.0,
            "one_line": "平",
            "updated_at": "2026-06-07 10:00:00",
        },
    }

    def _session(self) -> dict:
        return {
            "watchlist": self.wl,
            "watch_snapshots": self.snaps,
            "alert_pct_up": 5.0,
            "alert_score_low": 40.0,
        }

    def test_title_constant(self):
        self.assertEqual(PRIORITY_HOME_TITLE, "今日先看这3只")
        self.assertEqual(PRIORITY_HOME_TOP_N, 3)

    def test_compute_top_three(self):
        ranks = compute_priority_home_ranks(self._session(), top_n=3)
        self.assertLessEqual(len(ranks), 3)
        self.assertGreaterEqual(len(ranks), 1)
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        hot_codes = {a.code for a in alerts}
        self.assertTrue(any(r.code in hot_codes for r in ranks))

    def test_build_labels_format(self):
        ranks = compute_priority_home_ranks(self._session())
        labels = build_priority_home_labels(ranks)
        self.assertLessEqual(len(labels), 3)
        self.assertIn("label", labels[0])
        self.assertIn("600519", labels[0]["label"])
        self.assertTrue(labels[0]["reason"].strip())

    def test_should_show_with_watchlist(self):
        self.assertTrue(should_show_priority_home(self._session()))

    def test_should_not_show_empty(self):
        self.assertFalse(should_show_priority_home({"watchlist": [], "watch_snapshots": {}}))
        self.assertFalse(should_show_priority_home({"watchlist": self.wl, "watch_snapshots": {}}))


if __name__ == "__main__":
    unittest.main()
