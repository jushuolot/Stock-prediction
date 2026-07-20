import unittest

from src.analysis.daily_picks import DailyPick, SIGNAL_BUY, SIGNAL_WATCH
from src.analysis.quantum_style import (
    enrich_pick_dict,
    gate_picks_by_regime,
    regime_from_outlook,
)


class TestQuantumStyle(unittest.TestCase):
    def test_defense_regime(self):
        r = regime_from_outlook({"crash_prob_1_2w_pct": 60, "outlook_2w": "偏空"})
        self.assertEqual(r.label, "防守")
        self.assertEqual(r.max_buy_signals, 0)
        self.assertLess(r.risk_budget, 0.5)

    def test_offense_regime(self):
        r = regime_from_outlook(
            {"crash_prob_1_2w_pct": 25, "outlook_2w": "震荡偏多", "breadth_adv_pct": 60}
        )
        self.assertEqual(r.label, "进攻")
        self.assertGreaterEqual(r.risk_budget, 0.85)

    def test_gate_demotes_buys_in_defense(self):
        r = regime_from_outlook({"crash_prob_1_2w_pct": 70, "outlook_2w": "弱势"})
        picks = [
            DailyPick("600519", "茅台", 80, 1.0, SIGNAL_BUY, "1–3天", "[趋势延续] x"),
            DailyPick("000001", "平安", 75, 2.0, SIGNAL_BUY, "1–3天", "[突破在即] y"),
        ]
        gated = gate_picks_by_regime(picks, r)
        self.assertTrue(all(p.signal == SIGNAL_WATCH for p in gated))
        self.assertLessEqual(len(gated), r.max_a_picks)

    def test_enrich_has_thesis(self):
        r = regime_from_outlook({"crash_prob_1_2w_pct": 40, "outlook_2w": "震荡"})
        d = enrich_pick_dict(
            {
                "code": "600519",
                "name": "茅台",
                "signal": "明日偏多",
                "reason": "[强势回踩] 测试",
                "pct": -1.0,
                "score": 72,
            },
            r,
        )
        self.assertIn("thesis", d)
        self.assertIn("invalidate", d)
        self.assertIn("size_hint", d)


if __name__ == "__main__":
    unittest.main()
