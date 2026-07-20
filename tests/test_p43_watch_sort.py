"""P43 自选股排序偏好单元测试。"""

from __future__ import annotations

import unittest

from src.util.watch_sort import (
    apply_watch_sort_to_session,
    normalize_watch_sort,
    pref_sort_by,
    prefs_from_ui,
    ui_sort_by,
)
from src.util.watchlist_export import sort_watchlist


class WatchSortTests(unittest.TestCase):
    wl = [
        {"名称": "B", "代码": "2"},
        {"名称": "A", "代码": "1"},
        {"名称": "C", "代码": "3"},
    ]
    snaps = {
        "1": {"pct": 1.0, "score": 50.0},
        "2": {"pct": 5.0, "score": 70.0},
        "3": {"pct": -2.0, "score": 40.0},
    }

    def test_normalize_defaults(self):
        self.assertEqual(normalize_watch_sort(None), {"by": "name", "desc": False})
        self.assertEqual(normalize_watch_sort({"by": "bogus"}), {"by": "name", "desc": False})

    def test_ui_pref_roundtrip(self):
        for ui in ("代码", "涨跌幅", "评分"):
            pref = pref_sort_by(ui)
            self.assertEqual(ui_sort_by(pref), ui)

    def test_prefs_from_ui(self):
        self.assertEqual(prefs_from_ui("评分", True), {"by": "score", "desc": True})
        self.assertEqual(prefs_from_ui("涨跌幅", False), {"by": "pct", "desc": False})

    def test_apply_to_session(self):
        ui = apply_watch_sort_to_session({"by": "score", "desc": True})
        self.assertEqual(ui["by_ui"], "评分")
        self.assertTrue(ui["desc"])

    def test_sort_by_score_desc(self):
        sorted_wl = sort_watchlist(self.wl, self.snaps, by="评分", descending=True)
        codes = [x["代码"] for x in sorted_wl]
        self.assertEqual(codes, ["2", "1", "3"])

    def test_sort_by_name_asc(self):
        sorted_wl = sort_watchlist(self.wl, self.snaps, by="代码", descending=False)
        codes = [x["代码"] for x in sorted_wl]
        self.assertEqual(codes, ["1", "2", "3"])


if __name__ == "__main__":
    unittest.main()
