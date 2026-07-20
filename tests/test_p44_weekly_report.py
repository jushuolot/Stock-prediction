"""P44 周报生成单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime

from src.analysis.weekly_report import build_weekly_report, filter_log_last_days


class WeeklyReportTests(unittest.TestCase):
    def _sample_log(self):
        return [
            {
                "at": "2026年06月06日 10:00:00",
                "kind": "insight",
                "label": "一键分析 茅台",
                "conclusions_summary": "偏强",
            },
            {
                "at": "2026年05月28日 09:00:00",
                "kind": "movers",
                "label": "刷新榜单",
                "conclusions_summary": "",
            },
        ]

    def test_filter_last_7_days(self):
        log = self._sample_log()
        now = datetime(2026, 6, 6, 12, 0, 0)
        recent = filter_log_last_days(log, days=7, now=now)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["kind"], "insight")

    def test_build_report_sections(self):
        log = self._sample_log()
        wl = [{"名称": "茅台", "代码": "600519"}]
        snaps = {"600519": {"pct": 2.5, "score": 62.0}}
        now = datetime(2026, 6, 6, 12, 0, 0)
        md = build_weekly_report(log, wl, snaps, days=7, now=now)
        self.assertIn("# 分析周报", md)
        self.assertIn("查询概览", md)
        self.assertIn("自选股快照", md)
        self.assertIn("600519", md)
        self.assertIn("异动溯源", md)

    def test_empty_log_still_has_watch_stats(self):
        wl = [{"名称": "X", "代码": "1"}]
        snaps = {"1": {"pct": 0.0, "score": 55.0}}
        md = build_weekly_report([], wl, snaps, now=datetime(2026, 6, 6))
        self.assertIn("自选 **1** 只", md)
        self.assertIn("该周期内暂无查询记录", md)


if __name__ == "__main__":
    unittest.main()
