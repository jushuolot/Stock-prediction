"""P46 价格目标提醒单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.watch_alerts import compute_price_target_alerts, compute_watch_alerts
from src.util.price_targets import get_targets, normalize_price_targets, set_targets


class PriceTargetTests(unittest.TestCase):
    wl = [{"名称": "A", "代码": "1"}, {"名称": "B", "代码": "2"}]
    snaps = {
        "1": {"price": 105.0, "pct": 1.0, "score": 50.0},
        "2": {"price": 88.0, "pct": -2.0, "score": 45.0},
    }

    def test_normalize_targets(self):
        raw = {"1": {"above": 100, "below": ""}, "2": {"below": 90}}
        norm = normalize_price_targets(raw)
        self.assertEqual(norm["1"]["above"], 100.0)
        self.assertIsNone(norm["1"]["below"])
        self.assertEqual(norm["2"]["below"], 90.0)

    def test_set_and_get(self):
        t = set_targets({}, "1", above=110.0, below=95.0)
        self.assertEqual(get_targets(t, "1")["above"], 110.0)
        t2 = set_targets(t, "1", above=None, below=None)
        self.assertNotIn("1", t2)

    def test_above_trigger(self):
        targets = {"1": {"above": 100.0, "below": None}}
        alerts = compute_price_target_alerts(self.wl, self.snaps, targets)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].kind, "target_above")
        self.assertIn("105", alerts[0].message)

    def test_below_trigger(self):
        targets = {"2": {"above": None, "below": 90.0}}
        alerts = compute_price_target_alerts(self.wl, self.snaps, targets)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].kind, "target_below")

    def test_merged_in_compute_watch_alerts(self):
        targets = {"1": {"above": 100.0, "below": None}}
        alerts = compute_watch_alerts(self.wl, self.snaps, price_targets=targets)
        kinds = {a.kind for a in alerts}
        self.assertIn("target_above", kinds)


if __name__ == "__main__":
    unittest.main()
