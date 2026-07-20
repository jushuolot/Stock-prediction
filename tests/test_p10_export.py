"""P10 导出与元信息测试。"""

from __future__ import annotations

import unittest

from src.util.app_meta import APP_VERSION, EVOLUTION_STEP
from src.util.watchlist_export import filter_watchlist, sort_watchlist, watchlist_to_csv_bytes


class ExportTests(unittest.TestCase):
    def test_csv_and_sort(self):
        wl = [{"名称": "B", "代码": "2"}, {"名称": "A", "代码": "1"}]
        snaps = {"1": {"pct": 5.0, "score": 60.0, "one_line": "x"}}
        sorted_wl = sort_watchlist(wl, snaps, by="涨跌幅", descending=True)
        self.assertEqual(sorted_wl[0]["代码"], "1")
        csv = watchlist_to_csv_bytes(sorted_wl, snaps)
        self.assertIn(b"\xe5\x90\x8d\xe7\xa7\xb0", csv)  # 名称 UTF-8 BOM

    def test_filter(self):
        wl = [{"名称": "茅台", "代码": "600519", "市场": "沪"}]
        self.assertEqual(len(filter_watchlist(wl, "茅台")), 1)
        self.assertEqual(len(filter_watchlist(wl, "xyz")), 0)


class MetaTests(unittest.TestCase):
    def test_version(self):
        self.assertTrue(APP_VERSION)
        self.assertGreaterEqual(EVOLUTION_STEP, 100)


if __name__ == "__main__":
    unittest.main()
