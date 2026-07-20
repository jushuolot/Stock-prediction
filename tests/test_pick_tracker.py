import unittest
from datetime import date, timedelta

from src.analysis.pick_tracker import (
    append_today_picks,
    hit_rate_summary,
    normalize_pick_log,
    records_for_display,
    verify_pick_record,
)


class TestPickTracker(unittest.TestCase):
    def test_append_dedupe(self):
        log = append_today_picks(
            [],
            [{"code": "600519", "name": "茅台", "signal": "买入", "score": 70, "pct": 2.0, "hold_days": "3天"}],
            day="2025-06-01",
        )
        log2 = append_today_picks(log, [{"code": "600519", "name": "茅台", "signal": "买入", "score": 70, "pct": 2.0, "hold_days": "3天"}], day="2025-06-01")
        self.assertEqual(len(log2), 1)

    def test_verify_hit(self):
        rec = {
            "pick_date": (date.today() - timedelta(days=5)).isoformat(),
            "code": "600519",
            "hold_days": 3,
            "pick_pct": 1.0,
            "verified": False,
        }
        out = verify_pick_record(rec, current_pct=3.5)
        self.assertTrue(out["verified"])
        self.assertTrue(out["hit"])

    def test_hit_rate(self):
        log = [
            {"verified": True, "hit": True},
            {"verified": True, "hit": False},
            {"verified": True, "hit": True},
        ]
        s = hit_rate_summary(log)
        self.assertEqual(s["hits"], 2)
        self.assertEqual(s["total_verified"], 3)

    def test_normalize_pick_log_dirty(self):
        self.assertEqual(normalize_pick_log(None), [])
        self.assertEqual(normalize_pick_log(42), [])
        self.assertEqual(len(normalize_pick_log(["bad", {"code": "1", "pick_date": "2025-01-01"}])), 1)
        rows = records_for_display([{"pick_date": "2025-01-01", "code": "600519", "hold_days": "3天"}])
        self.assertEqual(rows[0].hold_days, 3)
        self.assertEqual(records_for_display({"pick_date": "2025-01-01", "code": "600519"})[0].code, "600519")


if __name__ == "__main__":
    unittest.main()
