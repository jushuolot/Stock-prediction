"""P6 brief_merge 与 auto_refresh 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.brief_merge import build_merged_briefs_markdown, collect_briefs_for_watchlist
from src.ui.auto_refresh import should_auto_refresh


class BriefMergeTests(unittest.TestCase):
    def test_collect_and_merge(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        briefs = collect_briefs_for_watchlist(wl, lambda c: "# 简报\n内容" if c == "600519" else None)
        self.assertIn("600519", briefs)
        md = build_merged_briefs_markdown(wl, briefs, query_label="t")
        self.assertIn("自选股分析合集", md)
        self.assertIn("600519", md)


class AutoRefreshTests(unittest.TestCase):
    def test_should_not_refresh_too_soon(self):
        self.assertFalse(should_auto_refresh(now=100.0, last=90.0, interval_minutes=5))

    def test_should_refresh_after_interval(self):
        self.assertTrue(should_auto_refresh(now=400.0, last=100.0, interval_minutes=5))

    def test_first_run(self):
        self.assertTrue(should_auto_refresh(now=1.0, last=None, interval_minutes=5))


if __name__ == "__main__":
    unittest.main()
