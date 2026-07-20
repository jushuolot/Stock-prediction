import unittest
from unittest.mock import MagicMock, patch

from src.analysis.garden_stock_lens import _pick_history_line, build_garden_lens_card
from src.providers.eastmoney import SearchHit
from src.providers.google_finance import compare_prices, google_finance_symbol
from src.providers.image_ticker_ocr import extract_ticker_candidates


class TestP121SearchLens(unittest.TestCase):
    def test_google_symbol_a(self):
        h = SearchHit(code="600519", name="茅台", market="沪市", kind="A", yahoo="600519.SS")
        self.assertEqual(google_finance_symbol(h), "600519:SHA")

    def test_google_symbol_us(self):
        h = SearchHit(code="AAPL", name="Apple", market="美股", kind="US", yahoo="AAPL")
        self.assertTrue(google_finance_symbol(h).endswith(":NASDAQ"))

    def test_compare_prices(self):
        self.assertIn("一致", compare_prices(100.0, 100.5))

    def test_extract_tickers(self):
        c = extract_ticker_candidates("截图里有 600519 和 AAPL")
        self.assertIn("600519", c)
        self.assertIn("AAPL", c)

    def test_pick_history(self):
        h = SearchHit(code="600519", name="茅台", market="沪市", kind="A", yahoo="")
        log = [{"pick_date": "2025-06-01", "code": "600519", "verified": True, "hit": True}]
        line = _pick_history_line(h, log)
        self.assertIn("推荐过", line)
        self.assertIn("✅", line)

    @patch("src.analysis.garden_stock_lens.fetch_google_finance_quote", return_value=None)
    @patch("src.analysis.garden_stock_lens.fetch_fund_holdings_snapshot", return_value=None)
    @patch("src.analysis.garden_stock_lens.analyze_watch_light")
    def test_build_lens_card(self, mock_light, _fh, _gf):
        mock_light.return_value = MagicMock(
            price=10.0, pct=1.2, score=75.0, one_line="测试"
        )
        h = SearchHit(code="600519", name="茅台", market="沪市", kind="A", yahoo="")
        card = build_garden_lens_card(h, lambda *a, **k: (None, ""), [], fetch_google=False)
        self.assertEqual(card.code, "600519")
        self.assertEqual(card.score, 75.0)


if __name__ == "__main__":
    unittest.main()
