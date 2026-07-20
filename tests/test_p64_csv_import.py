"""P64 自选 CSV 导入单元测试。"""

from __future__ import annotations

import unittest

from src.util.watchlist_csv_import import (
    apply_csv_import,
    merge_csv_tickers_into_watchlist,
    parse_tickers_from_csv,
    ticker_to_watchlist_item,
)


class CsvImportTests(unittest.TestCase):
    def test_parse_with_header(self):
        raw = "代码,名称\n600519,茅台\n601398,工行\n"
        self.assertEqual(parse_tickers_from_csv(raw), ["600519", "601398"])

    def test_parse_english_header(self):
        raw = "ticker,name\nAAPL,Apple\nMSFT,Microsoft\n"
        self.assertEqual(parse_tickers_from_csv(raw), ["AAPL", "MSFT"])

    def test_parse_no_header_first_column(self):
        raw = "600519\n000858\n"
        self.assertEqual(parse_tickers_from_csv(raw), ["600519", "000858"])

    def test_ticker_to_item_a_share(self):
        item = ticker_to_watchlist_item("600519")
        self.assertEqual(item["代码"], "600519")
        self.assertEqual(item["类型"], "A")
        self.assertEqual(item["货币"], "CNY")

    def test_ticker_to_item_us(self):
        item = ticker_to_watchlist_item("aapl")
        self.assertEqual(item["代码"], "AAPL")
        self.assertEqual(item["类型"], "US")

    def test_merge_dedupe(self):
        wl0 = [{"名称": "茅台", "代码": "600519", "类型": "A", "市场": "沪市A股"}]
        merged, stats = merge_csv_tickers_into_watchlist(wl0, ["600519", "601398"])
        self.assertEqual(len(merged), 2)
        self.assertEqual(stats["added"], 1)
        self.assertEqual(stats["duplicates"], 1)

    def test_apply_csv_import(self):
        raw = "code\n600519\n601398\n"
        wl, stats = apply_csv_import([], raw)
        self.assertEqual(len(wl), 2)
        self.assertEqual(stats["added"], 2)


if __name__ == "__main__":
    unittest.main()
