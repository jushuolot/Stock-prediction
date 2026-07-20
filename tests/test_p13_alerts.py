"""P13 watch_alerts 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.watch_alerts import compute_watch_alerts
from src.util.score_badge import pct_badge, score_badge


class WatchAlertTests(unittest.TestCase):
    def test_hot_and_low_score(self):
        wl = [{"名称": "X", "代码": "1"}]
        snaps = {"1": {"pct": 6.0, "score": 35.0}}
        alerts = compute_watch_alerts(wl, snaps, pct_up=5.0, score_low=40.0)
        self.assertGreaterEqual(len(alerts), 2)

    def test_badges(self):
        self.assertIn("🔺", pct_badge(6.0))
        self.assertIn("🟢", score_badge(70.0))


if __name__ == "__main__":
    unittest.main()
