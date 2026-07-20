"""P19 自选股分组单元测试。"""

from __future__ import annotations

import unittest

from src.util.watch_groups import (
    assign_ticker_to_group,
    filter_watchlist_by_group,
    group_names,
    groups_for_ticker,
    normalize_watch_groups,
    remove_ticker_from_all_groups,
)


class WatchGroupsTests(unittest.TestCase):
    def test_normalize_and_filter(self):
        groups = normalize_watch_groups({"核心": ["600519", "600519"], "": ["x"]})
        self.assertEqual(groups["核心"], ["600519"])
        wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "工行", "代码": "601398"}]
        filtered = filter_watchlist_by_group(wl, groups, "核心")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["代码"], "600519")
        self.assertEqual(len(filter_watchlist_by_group(wl, groups, "全部")), 2)

    def test_assign_and_query(self):
        groups: dict[str, list[str]] = {}
        groups = assign_ticker_to_group(groups, ticker="000001", group_name="观察")
        self.assertIn("000001", groups["观察"])
        groups = assign_ticker_to_group(groups, ticker="000001", group_name="核心")
        self.assertNotIn("000001", groups.get("观察", []))
        self.assertIn("000001", groups["核心"])
        self.assertEqual(groups_for_ticker(groups, "000001"), ["核心"])
        self.assertEqual(group_names(groups), ["核心", "观察"] if "观察" in groups else ["核心"])

    def test_remove_from_groups(self):
        groups = {"A": ["1", "2"], "B": ["1"]}
        cleaned = remove_ticker_from_all_groups(groups, "1")
        self.assertEqual(cleaned, {"A": ["2"]})


if __name__ == "__main__":
    unittest.main()
