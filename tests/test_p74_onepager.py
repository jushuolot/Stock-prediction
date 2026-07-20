"""P74 机构式一页纸单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.institutional_onepager import build_institutional_onepager
from src.analysis.sector_relative import compute_sector_relative, sector_relative_for_ticker
from src.analysis.trend_summary import TrendPoint
from src.analysis.watch_alerts import WatchAlert


class OnepagerTests(unittest.TestCase):
    wl = [{"名称": "茅台", "代码": "600519"}, {"名称": "五粮液", "代码": "000858"}]
    snaps = {
        "600519": {
            "pct": 3.5,
            "score": 68.0,
            "one_line": "综合偏强",
            "fin_summary": "白酒 · ROE20%",
        },
        "000858": {"pct": 1.0, "score": 62.0, "fin_summary": "白酒 · ROE18%"},
    }

    def test_build_sections(self):
        rel_rows = compute_sector_relative(self.wl, self.snaps)
        sr = sector_relative_for_ticker(rel_rows, "600519")
        md = build_institutional_onepager(
            name="茅台",
            code="600519",
            snap=self.snaps["600519"],
            sector_relative=sr,
            query_label="2026-06-07 测试",
        )
        self.assertIn("机构式一页纸", md)
        self.assertIn("## 结论", md)
        self.assertIn("## 相对板块", md)
        self.assertIn("## 风险", md)
        self.assertIn("## 下一步", md)
        self.assertIn("600519", md)
        self.assertIn("偏强", md)

    def test_includes_alerts_and_trend(self):
        alerts = [
            WatchAlert("600519", "茅台", "hot", "涨 +6.00%（≥5%）", "hot"),
        ]
        points = [
            TrendPoint(at="t1", label="a", kind="insight", pct=1.0, score=60.0),
            TrendPoint(at="t0", label="b", kind="insight", pct=3.5, score=68.0),
        ]
        md = build_institutional_onepager(
            name="茅台",
            code="600519",
            snap=self.snaps["600519"],
            trend_points=points,
            alerts=alerts,
        )
        self.assertIn("涨 +6.00%", md)
        self.assertIn("提醒", md)

    def test_empty_snap_still_valid(self):
        md = build_institutional_onepager(name="X", code="1", snap={})
        self.assertIn("待分析", md)
        self.assertIn("非投资建议", md)


if __name__ == "__main__":
    unittest.main()
