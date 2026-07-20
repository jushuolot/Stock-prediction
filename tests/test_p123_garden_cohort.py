import unittest

from src.analysis.garden_cohort import (
    build_cohort_strip_payload,
    cohort_brief_line,
    cohort_note_for_code,
    format_top_consensus_lines,
)
from src.analysis.garden_stock_lens import GardenLensCard


class TestP123GardenCohort(unittest.TestCase):
    def _sample_cohort(self) -> dict:
        return {
            "generated_at": "2026-06-09T12:00:00+08:00",
            "user_count": 3,
            "stock_consensus": [
                {"代码": "600519", "名称": "贵州茅台", "关注人数": 3, "提及次数": 5},
                {"代码": "000001", "名称": "平安银行", "关注人数": 2, "提及次数": 2},
            ],
            "summary_lines": ["共 3 位用户画像已汇总"],
        }

    def test_cohort_note_for_watched_stock(self):
        cohort = self._sample_cohort()
        self.assertEqual(cohort_note_for_code(cohort, "600519"), "👥 3人也在关注")
        self.assertEqual(cohort_note_for_code(cohort, "000001"), "👥 2人也在关注")
        self.assertEqual(cohort_note_for_code(cohort, "999999"), "")

    def test_format_top_consensus_lines(self):
        lines = format_top_consensus_lines(self._sample_cohort(), limit=2)
        self.assertEqual(len(lines), 2)
        self.assertIn("600519", lines[0])
        self.assertIn("3人关注", lines[0])

    def test_build_cohort_strip_payload(self):
        payload = build_cohort_strip_payload(self._sample_cohort())
        self.assertTrue(payload["has_data"])
        self.assertEqual(payload["user_count"], 3)
        self.assertEqual(len(payload["top_lines"]), 2)
        empty = build_cohort_strip_payload(None)
        self.assertFalse(empty["has_data"])

    def test_cohort_brief_line(self):
        line = cohort_brief_line(self._sample_cohort())
        self.assertIn("同伴选股", line)
        self.assertIn("贵州茅台", line)
        self.assertEqual(cohort_brief_line({"user_count": 1}), "")

    def test_lens_card_cohort_note_field(self):
        card = GardenLensCard(
            code="600519",
            name="贵州茅台",
            market="A股",
            price=100.0,
            pct=1.0,
            score=80.0,
            one_line="test",
            fund_tags="—",
            pick_history="—",
            hit_rate_label="—",
            google_note="",
            google_url="",
            cohort_note="👥 3人也在关注",
        )
        self.assertEqual(card.as_dict()["cohort_note"], "👥 3人也在关注")


if __name__ == "__main__":
    unittest.main()
