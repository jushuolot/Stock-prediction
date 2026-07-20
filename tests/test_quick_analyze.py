"""quick_analyze 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.quick_analyze import build_watch_snapshot, industry_fin_summary
from src.analysis.signals import ScoreBreakdown


class QuickAnalyzeTests(unittest.TestCase):
    def test_industry_fin_summary(self):
        data = {
            "ok": True,
            "industry": "白酒",
            "columns": ["总市值", "净资产", "净利润", "市盈率(动)", "市净率", "毛利率", "净利率", "ROE"],
            "rows": [
                {
                    "kind": "stock",
                    "label": "测试",
                    "cells": ["—", "—", "—", "25.00", "3.50", "—", "—", "15.00%"],
                },
                {
                    "kind": "rank",
                    "label": "行业排名",
                    "cells": ["—", "—", "—", "—", "—", "—", "—", "12/50"],
                },
            ],
        }
        s = industry_fin_summary(data)
        self.assertIn("白酒", s)
        self.assertIn("ROE", s)

    def test_build_watch_snapshot(self):
        item = {"代码": "600519", "名称": "贵州茅台", "类型": "A"}
        score = ScoreBreakdown(total=55.0, trend=20.0, momentum=5.0, risk=-5.0, liquidity=5.0, notes=[])
        snap = build_watch_snapshot(
            item=item,
            stats={"涨跌幅%": 2.5},
            score=score,
        )
        self.assertEqual(snap.code, "600519")
        self.assertAlmostEqual(snap.pct, 2.5)
        self.assertAlmostEqual(snap.score, 55.0)
        self.assertTrue(snap.one_line.endswith("。"))


if __name__ == "__main__":
    unittest.main()
