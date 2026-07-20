"""P35 提醒规则模板单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.watch_alerts import compute_watch_alerts
from src.util.alert_profiles import (
    ALERT_PROFILES,
    alert_profile_thresholds,
    apply_alert_profile,
    get_alert_profile,
    profile_caption,
)


class AlertProfileTests(unittest.TestCase):
    wl = [{"名称": "X", "代码": "1"}]
    snaps = {"1": {"pct": 4.0, "score": 52.0}}

    def test_profiles_registered(self):
        ids = {p.id for p in ALERT_PROFILES}
        self.assertEqual(ids, {"conservative", "balanced", "aggressive"})
        labels = {p.label for p in ALERT_PROFILES}
        self.assertEqual(labels, {"保守", "均衡", "激进"})

    def test_get_profile(self):
        prof = get_alert_profile("balanced")
        self.assertIsNotNone(prof)
        self.assertEqual(prof.label, "均衡")
        self.assertIsNone(get_alert_profile("unknown"))

    def test_apply_profile_to_dict(self):
        state: dict = {
            "alert_pct_up": 1.0,
            "alert_pct_down": -1.0,
            "alert_score_low": 10.0,
            "alert_score_high": 90.0,
        }
        applied = apply_alert_profile(state, "aggressive")
        self.assertIsNotNone(applied)
        self.assertEqual(state["alert_pct_up"], 3.0)
        self.assertEqual(state["alert_pct_down"], -3.0)
        self.assertEqual(state["alert_score_low"], 50.0)
        self.assertEqual(state["alert_score_high"], 55.0)

    def test_thresholds_shape(self):
        prof = get_alert_profile("conservative")
        assert prof is not None
        th = alert_profile_thresholds(prof)
        self.assertEqual(
            set(th.keys()),
            {"alert_pct_up", "alert_pct_down", "alert_score_low", "alert_score_high"},
        )

    def test_aggressive_triggers_more_than_conservative(self):
        aggr = get_alert_profile("aggressive")
        cons = get_alert_profile("conservative")
        assert aggr is not None and cons is not None
        aggr_th = alert_profile_thresholds(aggr)
        cons_th = alert_profile_thresholds(cons)
        aggr_alerts = compute_watch_alerts(
            self.wl,
            self.snaps,
            pct_up=aggr_th["alert_pct_up"],
            pct_down=aggr_th["alert_pct_down"],
            score_low=aggr_th["alert_score_low"],
            score_high=aggr_th["alert_score_high"],
        )
        cons_alerts = compute_watch_alerts(
            self.wl,
            self.snaps,
            pct_up=cons_th["alert_pct_up"],
            pct_down=cons_th["alert_pct_down"],
            score_low=cons_th["alert_score_low"],
            score_high=cons_th["alert_score_high"],
        )
        self.assertGreaterEqual(len(aggr_alerts), len(cons_alerts))

    def test_profile_caption(self):
        prof = get_alert_profile("balanced")
        assert prof is not None
        cap = profile_caption(prof)
        self.assertIn("5", cap)
        self.assertIn("均衡", prof.label)


if __name__ == "__main__":
    unittest.main()
