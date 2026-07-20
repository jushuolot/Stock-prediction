"""P80 每日作战清单单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.battle_plan import build_battle_plan
from src.analysis.dashboard_stats import compute_dashboard_stats
from src.analysis.watch_alerts import compute_watch_alerts


class BattlePlanTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
    ]
    snaps = {
        "600519": {"pct": 6.0, "score": 70.0, "updated_at": "2026-06-07 10:00:00"},
        "000858": {"pct": -3.0, "score": 38.0, "updated_at": "2026-06-07 10:00:00"},
    }

    def test_markdown_has_sections(self):
        md = build_battle_plan(self.wl, self.snaps, query_label="2026-06-07")
        self.assertIn("# 📋 今日作战清单", md)
        self.assertIn("## 盘面概况", md)
        self.assertIn("## 待办提醒", md)
        self.assertIn("## 今日行动（Top 3）", md)

    def test_includes_alerts(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        md = build_battle_plan(self.wl, self.snaps, alerts=alerts)
        self.assertIn("茅台", md)
        self.assertIn("600519", md)

    def test_top_three_actions(self):
        stats = compute_dashboard_stats(self.wl, self.snaps, score_low=40.0)
        md = build_battle_plan(self.wl, self.snaps, stats=stats)
        lines = [ln for ln in md.splitlines() if ln.startswith(("1.", "2.", "3."))]
        self.assertEqual(len(lines), 3)

    def test_empty_watchlist(self):
        md = build_battle_plan([], {})
        self.assertIn("自选 0 只", md)
        self.assertIn("Top 3", md)


if __name__ == "__main__":
    unittest.main()
