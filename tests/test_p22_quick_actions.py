"""P22 快捷筛选单元测试。"""

from __future__ import annotations

import unittest

from src.ui.quick_actions import (
    QUICK_FILTERS,
    filter_watchlist_by_preset,
    format_ticker_list,
    preset_filter_summary,
)


class QuickActionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wl = [
            {"名称": "茅台", "代码": "600519"},
            {"名称": "工行", "代码": "601398"},
            {"名称": "宁德", "代码": "300750"},
        ]
        self.snaps = {
            "600519": {"pct": 4.2, "score": 72.0, "one_line": "强势"},
            "601398": {"pct": -4.5, "score": 38.0, "one_line": "偏弱"},
            "300750": {"pct": 1.0, "score": 55.0, "one_line": ""},
        }

    def test_pct_up_filter(self):
        matched = filter_watchlist_by_preset(self.wl, self.snaps, "pct_up_3")
        codes = [m["代码"] for m in matched]
        self.assertEqual(codes, ["600519"])

    def test_score_gt_70(self):
        matched = filter_watchlist_by_preset(self.wl, self.snaps, "score_gt_70")
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["代码"], "600519")

    def test_has_brief(self):
        matched = filter_watchlist_by_preset(self.wl, self.snaps, "has_brief")
        codes = {m["代码"] for m in matched}
        self.assertEqual(codes, {"600519", "601398"})

    def test_format_ticker_list(self):
        self.assertEqual(format_ticker_list(self.wl), "600519, 601398, 300750")
        self.assertIn("600519", format_ticker_list(self.wl, line_break=True))

    def test_preset_summary_rows(self):
        rows = preset_filter_summary(self.wl, self.snaps, "pct_down_3")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["代码"], "601398")
        self.assertIn("-4.50%", rows[0]["涨跌幅"])

    def test_unknown_preset_returns_all(self):
        self.assertEqual(
            filter_watchlist_by_preset(self.wl, self.snaps, "nope"),
            self.wl,
        )

    def test_quick_filters_registered(self):
        ids = {f.id for f in QUICK_FILTERS}
        self.assertIn("pct_up_3", ids)
        self.assertIn("score_gt_70", ids)


if __name__ == "__main__":
    unittest.main()
