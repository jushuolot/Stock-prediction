import unittest
from unittest.mock import patch

from src.providers.eastmoney_fund_holdings import _norm_chg, fetch_fund_holdings_snapshot


class TestFundHoldings(unittest.TestCase):
    def test_norm_chg(self):
        self.assertEqual(_norm_chg("新进"), "新进")
        self.assertEqual(_norm_chg("增仓"), "增仓")
        self.assertEqual(_norm_chg("减仓"), "减仓")
        self.assertEqual(_norm_chg("不变"), "不变")

    @patch("src.providers.eastmoney_fund_holdings.requests.get")
    def test_fetch_snapshot_parses_latest_period(self, mock_get):
        mock_get.return_value.json.return_value = {
            "success": True,
            "result": {
                "data": [
                    {
                        "REPORT_DATE": "2026-03-31 00:00:00",
                        "ORG_TYPE": "01",
                        "HOLDCHA": "减仓",
                        "HOLDCHA_NUM": -1000,
                        "TOTALSHARES_RATIO": 1.2,
                        "HOULD_NUM": 4,
                    },
                    {
                        "REPORT_DATE": "2026-03-31 00:00:00",
                        "ORG_TYPE": "00",
                        "HOLDCHA_NUM": 5000,
                        "TOTALSHARES_RATIO": 3.0,
                        "HOULD_NUM": 6,
                    },
                    {
                        "REPORT_DATE": "2025-12-31 00:00:00",
                        "ORG_TYPE": "01",
                        "HOLDCHA": "增仓",
                        "HOLDCHA_NUM": 2000,
                        "TOTALSHARES_RATIO": 1.8,
                        "HOULD_NUM": 63,
                    },
                ]
            },
        }
        mock_get.return_value.raise_for_status = lambda: None
        snap = fetch_fund_holdings_snapshot("301418")
        self.assertIsNotNone(snap)
        assert snap is not None
        self.assertEqual(snap.report_date, "2026-03-31")
        self.assertEqual(snap.fund_chg, "减仓")
        self.assertEqual(snap.fund_count_chg, -59)
        self.assertAlmostEqual(snap.fund_ratio_chg or 0, -0.6, places=3)


if __name__ == "__main__":
    unittest.main()
