import unittest

from src.util.buddha_nightly_brief import build_nightly_brief, brief_to_markdown


class TestBuddhaNightlyBrief(unittest.TestCase):
    def test_green_brief(self):
        brief = build_nightly_brief(
            ritual={"data_fresh": True, "ritual_level": "green", "data_bar_date": "2026-06-09", "data_source": "新浪"},
            predict_for="2026-06-10",
            a_picks=[{"signal": "明日偏多", "name": "茅台"}],
            global_picks=[],
            outlook={"crash_prob_1_2w_pct": 20, "outlook_2w": "偏多"},
            hit_summary={"label": "最近 3 次", "rate_pct": 66.7},
        )
        self.assertEqual(brief["mood"], "green")
        self.assertIn("佛祖今晚查岗", brief_to_markdown(brief))

    def test_red_stale(self):
        brief = build_nightly_brief(
            ritual={"data_fresh": False, "ritual_level": "red"},
            predict_for="2026-06-10",
            a_picks=[],
            global_picks=[],
            outlook=None,
            hit_summary=None,
        )
        self.assertEqual(brief["mood"], "red")


if __name__ == "__main__":
    unittest.main()
