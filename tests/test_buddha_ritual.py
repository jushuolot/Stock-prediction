import unittest
from datetime import date, datetime, timedelta, timezone

from src.providers import fresh_fetch
from src.util.buddha_ritual import build_ritual_meta, ritual_banner_lines, MarketDataProbe


class TestBuddhaRitual(unittest.TestCase):
    def test_build_meta_green(self):
        probe = MarketDataProbe(
            probe_code="600519",
            bar_date="2026-06-08",
            source="东方财富",
            fresh=True,
            expected_lo="2026-06-08",
            expected_hi="2026-06-08",
            ranking_source="东方财富",
            error="",
        )
        meta = build_ritual_meta(probe, a_picks=3, global_picks=2, predict_for="2026-06-09")
        self.assertTrue(meta["ritual_ok"])
        self.assertEqual(meta["ritual_level"], "green")

    def test_build_meta_red_stale(self):
        probe = MarketDataProbe(
            probe_code="600519",
            bar_date="2026-06-05",
            source="Yahoo",
            fresh=False,
            expected_lo="2026-06-08",
            expected_hi="2026-06-08",
            ranking_source="",
            error="lag",
        )
        meta = build_ritual_meta(probe, a_picks=0, global_picks=0, predict_for="2026-06-09")
        self.assertFalse(meta["data_fresh"])
        self.assertEqual(meta["ritual_level"], "red")

    def test_banner(self):
        line, level = ritual_banner_lines({"data_bar_date": "2026-06-08", "data_fresh": True, "a_picks": 2})
        self.assertIn("佛祖查岗", line)

    def test_expected_bar_monday_afternoon(self):
        cn = datetime(2026, 6, 8, 16, 0, tzinfo=timezone(timedelta(hours=8)))
        lo, hi = fresh_fetch.expected_latest_bar_date(now=cn)
        self.assertEqual(lo, hi)
        self.assertEqual(hi, date(2026, 6, 8))


if __name__ == "__main__":
    unittest.main()
