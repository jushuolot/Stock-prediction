"""P52 相似股推荐 lite 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.similar_pick import similar_pick_rows, suggest_similar_picks


class SimilarPickTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
        {"名称": "宁德", "代码": "300750"},
        {"名称": "比亚迪", "代码": "002594"},
    ]
    snaps = {
        "600519": {"score": 80.0, "pct": 1.2, "fin_summary": "白酒 · ROE30%"},
        "000858": {"score": 72.0, "pct": 0.5, "fin_summary": "白酒 · ROE25%"},
        "300750": {"score": 65.0, "pct": -1.0, "fin_summary": "电池 · ROE18%"},
        "002594": {"score": 60.0, "pct": 2.0, "fin_summary": "汽车 · ROE15%"},
    }

    def test_suggest_same_sector_peers(self):
        picks = suggest_similar_picks(self.wl, self.snaps, max_picks=3)
        self.assertGreaterEqual(len(picks), 1)
        self.assertLessEqual(len(picks), 3)
        codes = {p.code for p in picks}
        self.assertIn("000858", codes)
        for p in picks:
            self.assertIn("白酒", p.sector)
            self.assertIn("600519", p.reason)

    def test_single_sector_member_skipped(self):
        picks = suggest_similar_picks(
            [{"名称": "宁德", "代码": "300750"}],
            {"300750": self.snaps["300750"]},
        )
        self.assertEqual(picks, [])

    def test_rows_format(self):
        picks = suggest_similar_picks(self.wl[:2], self.snaps)
        rows = similar_pick_rows(picks)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["代码"], "000858")
        self.assertIn("评分", rows[0])


if __name__ == "__main__":
    unittest.main()
