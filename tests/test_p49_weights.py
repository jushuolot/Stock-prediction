"""P49 组合权重视图单元测试。"""

from __future__ import annotations

import unittest

from src.util.watch_weights import (
    get_weight,
    normalize_watch_weights,
    pie_slices_for_watchlist,
    set_weight,
)


class WatchWeightsTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "1"},
        {"名称": "B", "代码": "2"},
        {"名称": "C", "代码": "3"},
    ]

    def test_normalize_weights(self):
        raw = {"1": 30, "2": "bad", "3": -1, "": 10}
        norm = normalize_watch_weights(raw)
        self.assertEqual(norm["1"], 30.0)
        self.assertNotIn("2", norm)
        self.assertNotIn("3", norm)

    def test_set_and_get(self):
        w = set_weight({}, "1", 25.0)
        self.assertEqual(get_weight(w, "1"), 25.0)
        w2 = set_weight(w, "1", None)
        self.assertNotIn("1", w2)

    def test_equal_weight_when_empty(self):
        slices = pie_slices_for_watchlist(self.wl, {})
        self.assertEqual(len(slices), 3)
        total = sum(s["pct"] for s in slices)
        self.assertAlmostEqual(total, 100.0, places=5)
        for s in slices:
            self.assertAlmostEqual(s["pct"], 100.0 / 3, places=5)
            self.assertIsNone(s["raw"])

    def test_normalize_custom_weights(self):
        weights = {"1": 50.0, "2": 50.0}
        slices = pie_slices_for_watchlist(self.wl, weights)
        by_code = {s["code"]: s for s in slices}
        self.assertAlmostEqual(by_code["1"]["pct"], 50.0, places=5)
        self.assertAlmostEqual(by_code["2"]["pct"], 50.0, places=5)
        self.assertEqual(by_code["3"]["pct"], 0.0)

    def test_partial_weights_normalize(self):
        weights = {"1": 30.0, "2": 70.0}
        slices = pie_slices_for_watchlist(self.wl[:2], weights)
        total = sum(s["pct"] for s in slices)
        self.assertAlmostEqual(total, 100.0, places=5)


if __name__ == "__main__":
    unittest.main()
