"""P76 板块龙头对标单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.sector_leader import (
    compute_sector_leaders,
    sector_leader_for_ticker,
    sector_leader_table_rows,
)


class SectorLeaderTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
        {"名称": "工行", "代码": "601398"},
    ]

    def test_leader_by_score(self):
        snaps = {
            "600519": {"pct": 3.0, "score": 72.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 5.0, "score": 60.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": -0.5, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_leaders(self.wl, snaps)
        maotai = sector_leader_for_ticker(rows, "600519")
        wuliang = sector_leader_for_ticker(rows, "000858")
        self.assertIsNotNone(maotai)
        self.assertIsNotNone(wuliang)
        assert maotai is not None
        assert wuliang is not None
        self.assertTrue(maotai.is_leader)
        self.assertEqual(maotai.label, "👑 板块龙头")
        self.assertFalse(wuliang.is_leader)
        self.assertLess(wuliang.gap_score or 0, 0)

    def test_gap_vs_leader(self):
        snaps = {
            "600519": {"pct": 1.0, "score": 65.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 4.0, "score": 70.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": 0.0, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_leaders(self.wl, snaps)
        maotai = sector_leader_for_ticker(rows, "600519")
        self.assertIsNotNone(maotai)
        assert maotai is not None
        self.assertFalse(maotai.is_leader)
        self.assertEqual(maotai.leader_code, "000858")
        self.assertLess(maotai.gap_score or 0, 0)

    def test_single_peer_sector(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        snaps = {"600519": {"pct": 2.0, "score": 70.0, "fin_summary": "白酒 · ROE20%"}}
        rows = compute_sector_leaders(wl, snaps)
        self.assertEqual(rows[0].label, "板块仅本只")

    def test_table_rows_have_fool_conclusion(self):
        snaps = {
            "600519": {"pct": 3.0, "score": 72.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 1.0, "score": 60.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": -0.5, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_leaders(self.wl, snaps)
        table = sector_leader_table_rows(rows)
        self.assertEqual(len(table), 3)
        self.assertIn("傻瓜结论", table[0])
        self.assertIn("距龙头分", table[0])


if __name__ == "__main__":
    unittest.main()
