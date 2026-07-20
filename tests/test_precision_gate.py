import unittest

from src.analysis.precision_gate import evaluate_precision


class TestPrecisionGate(unittest.TestCase):
    def test_chase_blocked(self):
        v = evaluate_precision(
            pattern="趋势延续",
            pct=10.0,
            adj_score=80,
            amount=2e8,
            pattern_adj={},
            quality_delta=2,
            want_buy=True,
        )
        self.assertFalse(v.ok)

    def test_weak_pattern_blocked(self):
        v = evaluate_precision(
            pattern="突破在即",
            pct=2.0,
            adj_score=78,
            amount=2e8,
            pattern_adj={"突破在即": -3.0},
            quality_delta=1,
            want_buy=True,
        )
        self.assertFalse(v.ok)

    def test_pullback_can_buy(self):
        v = evaluate_precision(
            pattern="强势回踩",
            pct=-1.2,
            adj_score=76,
            amount=3e8,
            pattern_adj={"强势回踩": 2.0},
            quality_delta=3,
            want_buy=True,
        )
        self.assertTrue(v.ok)
        self.assertTrue(v.allow_buy)

    def test_low_asym_rejected(self):
        v = evaluate_precision(
            pattern="趋势延续",
            pct=7.0,
            adj_score=65,
            amount=2e8,
            pattern_adj={},
            quality_delta=0,
            want_buy=True,
        )
        self.assertFalse(v.allow_buy)


if __name__ == "__main__":
    unittest.main()
