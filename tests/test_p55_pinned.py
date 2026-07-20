"""P55 分析结果置顶单元测试。"""

from __future__ import annotations

import unittest

from src.util.pinned_tickers import (
    apply_pinned_order,
    is_pinned,
    normalize_pinned_tickers,
    pin_ticker,
    unpin_ticker,
)
from src.util.watchlist_export import sort_watchlist


class PinnedTickersTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "1"},
        {"名称": "B", "代码": "2"},
        {"名称": "C", "代码": "3"},
    ]
    snaps = {
        "1": {"pct": 1.0, "score": 50.0},
        "2": {"pct": 5.0, "score": 70.0},
        "3": {"pct": -2.0, "score": 40.0},
    }

    def test_normalize_pinned(self):
        self.assertEqual(normalize_pinned_tickers(None), [])
        self.assertEqual(normalize_pinned_tickers(["2", "2", "", "1"]), ["2", "1"])

    def test_pin_unpin(self):
        p = pin_ticker([], "2")
        self.assertEqual(p, ["2"])
        p2 = pin_ticker(p, "1")
        self.assertEqual(p2, ["2", "1"])
        self.assertTrue(is_pinned(p2, "2"))
        self.assertEqual(unpin_ticker(p2, "2"), ["1"])

    def test_apply_pinned_order_preserves_pin_sequence(self):
        sorted_wl = sort_watchlist(self.wl, self.snaps, by="评分", descending=True)
        ordered = apply_pinned_order(sorted_wl, ["3", "1"])
        codes = [x["代码"] for x in ordered]
        self.assertEqual(codes[:2], ["3", "1"])
        self.assertEqual(codes[2:], ["2"])

    def test_pinned_stays_on_top_after_sort(self):
        sorted_wl = sort_watchlist(self.wl, self.snaps, by="涨跌幅", descending=True)
        ordered = apply_pinned_order(sorted_wl, ["1"])
        self.assertEqual(ordered[0]["代码"], "1")
        self.assertEqual([x["代码"] for x in ordered[1:]], ["2", "3"])


if __name__ == "__main__":
    unittest.main()
