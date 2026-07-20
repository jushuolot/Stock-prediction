"""P16 compare_stocks 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.compare_stocks import (
    compare_table_rows,
    compare_to_markdown,
    compare_two_stocks,
)


class CompareStocksTests(unittest.TestCase):
    def test_side_by_side_deltas(self):
        item_a = {"名称": "甲", "代码": "600000", "市场": "沪A", "货币": "CNY"}
        item_b = {"名称": "乙", "代码": "000001", "市场": "深A", "货币": "CNY"}
        snap_a = {"pct": 3.5, "score": 62.0, "one_line": "偏强", "fin_summary": "ROE 12%"}
        snap_b = {"pct": -1.2, "score": 55.0, "one_line": "震荡", "fin_summary": "ROE 10%"}
        result = compare_two_stocks(item_a, item_b, snap_a, snap_b)
        self.assertAlmostEqual(result.pct_delta or 0, 4.7, places=1)
        self.assertAlmostEqual(result.score_delta or 0, 7.0, places=1)
        rows = compare_table_rows(result)
        self.assertEqual(rows[0]["指标"], "代码")
        self.assertIn("600000", rows[0]["A"])
        pct_row = next(r for r in rows if r["指标"] == "涨跌幅")
        self.assertIn("+3.50%", pct_row["A"])
        self.assertIn("-1.20%", pct_row["B"])

    def test_markdown_export(self):
        item_a = {"名称": "A", "代码": "1"}
        item_b = {"名称": "B", "代码": "2"}
        result = compare_two_stocks(item_a, item_b, {"pct": 1.0}, {"pct": 2.0})
        md = compare_to_markdown(result)
        self.assertIn("# 双股对比", md)
        self.assertIn("涨跌幅差", md)

    def test_missing_snapshots(self):
        item_a = {"名称": "A", "代码": "1"}
        item_b = {"名称": "B", "代码": "2"}
        result = compare_two_stocks(item_a, item_b, None, None)
        self.assertIsNone(result.pct_delta)
        self.assertIsNone(result.score_delta)


if __name__ == "__main__":
    unittest.main()
