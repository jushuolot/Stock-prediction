import unittest

from src.analysis.prediction_calibration import merge_pick_logs, load_calibration_adjustments


class TestPredictionCalibration(unittest.TestCase):
    def test_merge_dedup(self):
        a = [{"pick_date": "2026-06-01", "code": "600519", "verified": False}]
        b = [{"pick_date": "2026-06-01", "code": "600519", "verified": True, "hit": True}]
        merged = merge_pick_logs(a, b)
        self.assertEqual(len(merged), 1)
        self.assertTrue(merged[0].get("verified"))

    def test_load_adjustments(self):
        adj = load_calibration_adjustments(
            {
                "pattern_adjustments": {"趋势延续": -3.0},
                "score_floor_delta": 2.0,
                "buy_threshold_delta": 1.5,
            }
        )
        self.assertEqual(adj["pattern"]["趋势延续"], -3.0)
        self.assertEqual(adj["score_floor_delta"], 2.0)


if __name__ == "__main__":
    unittest.main()
