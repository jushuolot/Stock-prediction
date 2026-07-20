import unittest
from datetime import date

from src.util.data_date_label import (
    build_kline_caption,
    data_lag_hint,
    format_trade_date_cn,
    parse_bar_date,
    short_trade_date,
)


class TestDataDateLabel(unittest.TestCase):
    def test_parse_bar_date(self):
        self.assertEqual(parse_bar_date("2026-06-05"), date(2026, 6, 5))
        self.assertIsNone(parse_bar_date("bad"))

    def test_format_cn(self):
        self.assertIn("周五", format_trade_date_cn(date(2026, 6, 5)))

    def test_lag_hint(self):
        msg = data_lag_hint(date(2026, 6, 5), today=date(2026, 6, 8))
        self.assertIsNotNone(msg)
        assert msg is not None
        self.assertIn("2026", msg)

    def test_kline_caption(self):
        cap = build_kline_caption(
            {"日期": "2026-06-05"},
            ksrc="东财",
            query_label="2026年06月08日 15:00:00",
            range_text="2025-01-01 ~ 2026-06-08",
            currency="CNY",
        )
        self.assertIn("K线交易日", cap)
        self.assertIn("今天", cap)

    def test_short_date(self):
        self.assertEqual(short_trade_date(date(2026, 6, 5)), "06-05")


if __name__ == "__main__":
    unittest.main()
