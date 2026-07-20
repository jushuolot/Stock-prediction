"""表格涨跌配色（P129b）。"""

from __future__ import annotations

import unittest

import pandas as pd

from src.ui.df_style import (
    _to_float,
    html_pct_color,
    is_pct_column,
    pct_columns,
    style_pct_dataframe,
)


class TestDfStyle(unittest.TestCase):
    def test_to_float_parses_strings(self):
        self.assertEqual(_to_float("+1.23"), 1.23)
        self.assertEqual(_to_float("-2.5%"), -2.5)
        self.assertEqual(_to_float("—"), None)
        self.assertEqual(_to_float(0), 0.0)

    def test_is_pct_column(self):
        self.assertTrue(is_pct_column("涨跌幅%"))
        self.assertTrue(is_pct_column("榜单日涨跌%"))
        self.assertTrue(is_pct_column("D+1涨幅%"))
        self.assertFalse(is_pct_column("命中率%"))
        self.assertFalse(is_pct_column("换手率%"))
        self.assertFalse(is_pct_column("名称"))

    def test_pct_columns_and_style(self):
        df = pd.DataFrame(
            {
                "名称": ["A", "B", "C"],
                "涨跌幅%": [1.2, -0.5, 0.0],
                "换手率%": [3.0, 4.0, 5.0],
            }
        )
        self.assertEqual(pct_columns(df), ["涨跌幅%"])
        sty = style_pct_dataframe(df)
        self.assertIsNotNone(sty)
        # Styler 应含涨跌列样式
        styles = sty.to_html() if hasattr(sty, "to_html") else str(sty)
        self.assertIn("#e74c3c", styles)
        self.assertIn("#27ae60", styles)

    def test_html_pct_color(self):
        self.assertEqual(html_pct_color(1.0), "#e74c3c")
        self.assertEqual(html_pct_color(-1.0), "#27ae60")
        self.assertEqual(html_pct_color(0), "#888888")


if __name__ == "__main__":
    unittest.main()
