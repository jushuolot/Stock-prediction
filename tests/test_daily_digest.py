"""daily_digest 单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.daily_digest import build_watchlist_digest


class DailyDigestTests(unittest.TestCase):
    def test_build_watchlist_digest_table(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        snaps = {
            "600519": {
                "pct": 1.5,
                "score": 55.0,
                "one_line": "综合评分中性。",
                "fin_summary": "白酒 · ROE15%",
            }
        }
        md = build_watchlist_digest(wl, snaps, query_label="2024-01-01")
        self.assertIn("600519", md)
        self.assertIn("茅台", md)
        self.assertIn("+1.50%", md)
        self.assertIn("综合评分中性", md)


if __name__ == "__main__":
    unittest.main()
