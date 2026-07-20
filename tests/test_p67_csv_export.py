"""P67 自选 CSV 导出单元测试。"""

from __future__ import annotations

import csv
import io
import unittest

from src.util.watchlist_csv_export import (
    CSV_FIELDNAMES,
    watchlist_table_csv_rows,
    watchlist_table_to_csv_bytes,
)


class CsvExportTests(unittest.TestCase):
    def test_rows_columns_and_values(self):
        wl = [{"名称": "茅台", "代码": "600519", "类型": "A", "市场": "沪"}]
        snaps = {"600519": {"pct": 1.5, "score": 72.3}}
        notes = {"600519": "核心持仓"}
        groups = {"白酒": ["600519"], "核心": ["600519"]}
        rows = watchlist_table_csv_rows(
            wl,
            snaps,
            watch_notes=notes,
            watch_groups=groups,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0].keys()), CSV_FIELDNAMES)
        self.assertEqual(rows[0]["code"], "600519")
        self.assertEqual(rows[0]["name"], "茅台")
        self.assertEqual(rows[0]["score"], "72.3")
        self.assertEqual(rows[0]["pct"], "+1.50")
        self.assertEqual(rows[0]["note"], "核心持仓")
        self.assertEqual(rows[0]["group"], "核心,白酒")

    def test_csv_bytes_utf8_bom(self):
        wl = [{"名称": "工行", "代码": "601398"}]
        raw = watchlist_table_to_csv_bytes(wl, {})
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        self.assertEqual(list(reader.fieldnames), list(CSV_FIELDNAMES))
        row = next(reader)
        self.assertEqual(row["code"], "601398")
        self.assertEqual(row["name"], "工行")

    def test_empty_watchlist(self):
        self.assertEqual(watchlist_table_to_csv_bytes([], {}), b"")


if __name__ == "__main__":
    unittest.main()
