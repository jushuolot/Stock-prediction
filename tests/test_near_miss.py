"""近失榜（P130）。"""

from __future__ import annotations

import unittest

from src.analysis.near_miss import (
    NearMiss,
    rank_near_misses,
    stage_label,
    summarize_near_misses,
)
from src.util.buddha_nightly_brief import build_nightly_brief


class TestNearMiss(unittest.TestCase):
    def test_rank_dedupe_and_order(self):
        rows = rank_near_misses(
            [
                NearMiss("000001", "平安", "precision", "追高", precision_score=50),
                NearMiss("000002", "万科", "low_score", "分数略低", score=62),
                NearMiss("000001", "平安银行", "precision", "更近", precision_score=58),
            ]
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["code"], "000001")
        self.assertEqual(rows[0]["precision_score"], 58)

    def test_summarize(self):
        s = summarize_near_misses(
            [{"name": "天山电子", "code": "301379", "reason": "不对称分 50<56"}]
        )
        self.assertIn("天山电子", s)
        self.assertIn("近失", s)

    def test_stage_label(self):
        self.assertEqual(stage_label("precision"), "精准闸门")
        self.assertEqual(stage_label("quality"), "质量过滤")

    def test_brief_includes_near_miss(self):
        brief = build_nightly_brief(
            ritual={"data_fresh": True, "ritual_level": "green", "data_bar_date": "2026-07-20"},
            predict_for="2026-07-21",
            a_picks=[],
            global_picks=[],
            outlook={"crash_prob_1_2w_pct": 25, "outlook_2w": "中性"},
            hit_summary=None,
            near_miss_summary="近失 2 只，最近：天山电子（不对称分偏低）",
        )
        self.assertEqual(brief["mood"], "yellow")
        joined = "\n".join(brief["lines"])
        self.assertIn("近失", joined)
        self.assertIn("天山电子", brief["action"])


if __name__ == "__main__":
    unittest.main()
