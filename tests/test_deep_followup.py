import unittest

from src.analysis.deep_followup import select_followup_targets


class TestDeepFollowup(unittest.TestCase):
    def test_select_missed_and_movers(self):
        diff = {
            "pick_checks": [{"code": "600519", "name": "茅台", "hit": False}],
            "movers": [{"code": "000001", "name": "平安", "delta_pct": 3.2}],
        }
        targets = select_followup_targets(diff, max_items=4)
        codes = [t[0] for t in targets]
        self.assertIn("600519", codes)
        self.assertIn("000001", codes)


if __name__ == "__main__":
    unittest.main()
