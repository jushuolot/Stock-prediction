"""readable_report 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.readable_report import build_stock_brief_markdown
from src.analysis.signals import ScoreBreakdown


class ReadableReportTests(unittest.TestCase):
    def test_build_stock_brief_markdown_contains_sections(self):
        score = ScoreBreakdown(
            total=55.0,
            trend=20.0,
            momentum=10.0,
            risk=-5.0,
            liquidity=5.0,
            notes=["趋势：偏强"],
        )
        md = build_stock_brief_markdown(
            name="测试股份",
            code="000001",
            kind="A",
            market="深圳",
            currency="CNY",
            stats={"收盘": 10.5, "涨跌幅%": 1.2, "最高": 10.8, "最低": 10.1, "成交量": 1e6, "日期": "2024-06-01"},
            score=score,
            kline_src="东财",
            query_label="2024-06-01 12:00",
        )
        self.assertIn("# 股票分析简报", md)
        self.assertIn("测试股份（000001）", md)
        self.assertIn("## 一、30 秒摘要", md)
        self.assertIn("## 二、评分拆解", md)
        self.assertIn("综合评分", md)
        self.assertIn("免责声明", md)


if __name__ == "__main__":
    unittest.main()
