"""P73 相对板块强弱单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.sector_relative import (
    compute_sector_relative,
    sector_relative_for_ticker,
    sector_relative_table_rows,
)


class SectorRelativeTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
        {"名称": "工行", "代码": "601398"},
    ]

    def test_outperform_sector(self):
        snaps = {
            "600519": {"pct": 5.0, "score": 72.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 1.0, "score": 60.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": -0.5, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_relative(self.wl, snaps)
        maotai = sector_relative_for_ticker(rows, "600519")
        self.assertIsNotNone(maotai)
        assert maotai is not None
        self.assertEqual(maotai.sector, "白酒")
        self.assertEqual(maotai.label, "跑赢板块")
        self.assertGreater(maotai.pct_vs_sector or 0, 0)
        self.assertGreater(maotai.score_vs_sector or 0, 0)

    def test_underperform_sector(self):
        snaps = {
            "600519": {"pct": -2.0, "score": 50.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 3.0, "score": 68.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": 0.0, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_relative(self.wl, snaps)
        maotai = sector_relative_for_ticker(rows, "600519")
        self.assertIsNotNone(maotai)
        assert maotai is not None
        self.assertEqual(maotai.label, "跑输板块")

    def test_single_peer_sector(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        snaps = {"600519": {"pct": 2.0, "score": 70.0, "fin_summary": "白酒 · ROE20%"}}
        rows = compute_sector_relative(wl, snaps)
        self.assertEqual(rows[0].label, "板块仅本只")

    def test_table_rows_have_fool_conclusion(self):
        snaps = {
            "600519": {"pct": 2.0, "score": 70.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 1.0, "score": 65.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": -0.5, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        rows = compute_sector_relative(self.wl, snaps)
        table = sector_relative_table_rows(rows)
        self.assertEqual(len(table), 3)
        self.assertIn("傻瓜结论", table[0])
        self.assertIn("结论", table[0])


if __name__ == "__main__":
    unittest.main()
