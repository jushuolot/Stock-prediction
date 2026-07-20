import unittest

from src.analysis.cohort_analytics import build_cohort_insights
from src.analysis.user_pick_profile import build_user_pick_profile


class TestCohortAnalytics(unittest.TestCase):
    def test_user_profile_style(self):
        prof = build_user_pick_profile(
            "alice",
            pick_log=[
                {
                    "code": "301418",
                    "pattern": "突破在即",
                    "reason": "[突破在即] test",
                    "verified": True,
                    "hit": True,
                },
                {
                    "code": "301231",
                    "pattern": "突破在即",
                    "verified": True,
                    "hit": False,
                },
            ],
            watchlist=[{"代码": "600519", "名称": "茅台"}],
            search_history=["茅台", "协昌科技"],
        )
        self.assertIn("成长", prof.style_label)
        self.assertIn("301418", prof.top_codes)

    def test_cohort_merge(self):
        c1 = {
            "user_id": "alice",
            "profile": build_user_pick_profile(
                "alice",
                pick_log=[{"code": "600519", "pattern": "趋势延续", "verified": True, "hit": True}],
            ).as_dict(),
            "recent_picks": ["600519"],
        }
        c2 = {
            "user_id": "bob",
            "profile": build_user_pick_profile(
                "bob",
                pick_log=[{"code": "600519", "pattern": "趋势延续", "verified": True, "hit": False}],
            ).as_dict(),
            "recent_picks": ["600519"],
        }
        ins = build_cohort_insights([c1, c2])
        self.assertEqual(ins.user_count, 2)
        self.assertTrue(ins.stock_consensus)
        self.assertEqual(ins.stock_consensus[0].get("代码"), "600519")
        self.assertEqual(ins.stock_consensus[0].get("关注人数"), 2)


if __name__ == "__main__":
    unittest.main()
