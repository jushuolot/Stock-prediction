"""P26 批量操作单元测试。"""

from __future__ import annotations

import unittest

from src.util.batch_watch_ops import (
    batch_add_to_group,
    batch_remove_from_groups,
    batch_remove_from_watchlist,
    codes_in_watchlist,
    normalize_ticker_codes,
)


class BatchWatchOpsTests(unittest.TestCase):
    def test_normalize_ticker_codes(self):
        self.assertEqual(normalize_ticker_codes(["600519", "600519", ""]), ["600519"])

    def test_batch_remove_watchlist(self):
        wl = [{"代码": "600519"}, {"代码": "601398"}, {"代码": "000858"}]
        new_wl, removed = batch_remove_from_watchlist(wl, ["600519", "000858", "999"])
        self.assertEqual(removed, ["600519", "000858"])
        self.assertEqual([x["代码"] for x in new_wl], ["601398"])

    def test_batch_add_to_group(self):
        groups: dict[str, list[str]] = {"核心": ["600519"]}
        groups = batch_add_to_group(groups, ["601398", "600519"], "核心")
        self.assertEqual(sorted(groups["核心"]), ["600519", "601398"])

    def test_batch_remove_from_groups(self):
        groups = {"A": ["1", "2"], "B": ["1"]}
        cleaned = batch_remove_from_groups(groups, ["1"])
        self.assertEqual(cleaned, {"A": ["2"]})

    def test_codes_in_watchlist(self):
        wl = [{"代码": "600519"}, {"代码": "601398"}]
        self.assertEqual(codes_in_watchlist(wl, ["600519", "999"]), ["600519"])


if __name__ == "__main__":
    unittest.main()
