"""P25 板块热力图 lite 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.sector_heatmap import (
    UNKNOWN_SECTOR,
    aggregate_sector_distribution,
    extract_sector_label,
    sector_bar_values,
    sector_distribution_rows,
)


class SectorHeatmapTests(unittest.TestCase):
    def test_extract_from_snapshot_fields(self):
        snap = {"sector": "科技", "fin_summary": "白酒 · ROE10%"}
        self.assertEqual(extract_sector_label(snap), "科技")
        snap2 = {"industry": "银行", "fin_summary": ""}
        self.assertEqual(extract_sector_label(snap2), "银行")

    def test_extract_from_fin_summary(self):
        snap = {"fin_summary": "白酒 · ROE15% · 市盈率(动)25"}
        self.assertEqual(extract_sector_label(snap), "白酒")

    def test_extract_from_brief(self):
        brief = "## 财务对比摘要（A 股）\n\n新能源 · ROE8%\n"
        self.assertEqual(extract_sector_label({}, brief_md=brief), "新能源")

    def test_unknown_sector(self):
        self.assertEqual(extract_sector_label({}), UNKNOWN_SECTOR)

    def test_aggregate_and_table(self):
        wl = [
            {"名称": "茅台", "代码": "600519"},
            {"名称": "五粮液", "代码": "000858"},
            {"名称": "工行", "代码": "601398"},
        ]
        snaps = {
            "600519": {"pct": 2.0, "score": 70.0, "fin_summary": "白酒 · ROE20%"},
            "000858": {"pct": 1.0, "score": 65.0, "fin_summary": "白酒 · ROE18%"},
            "601398": {"pct": -0.5, "score": 55.0, "fin_summary": "银行 · ROE10%"},
        }
        buckets = aggregate_sector_distribution(wl, snaps)
        self.assertEqual(len(buckets), 2)
        self.assertEqual(buckets[0].sector, "白酒")
        self.assertEqual(buckets[0].count, 2)
        self.assertEqual(buckets[0].avg_pct, 1.5)
        self.assertEqual(buckets[0].avg_score, 67.5)
        rows = sector_distribution_rows(buckets)
        self.assertEqual(rows[0]["板块"], "白酒")
        self.assertEqual(rows[0]["数量"], 2)
        labels, counts = sector_bar_values(buckets)
        self.assertEqual(labels[0], "白酒")
        self.assertEqual(counts[0], 2)


if __name__ == "__main__":
    unittest.main()
