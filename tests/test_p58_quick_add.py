"""P58 搜索页快捷加入自选单元测试。"""

from __future__ import annotations

import unittest

from src.providers.eastmoney import SearchHit
from src.util.watchlist_add import (
    add_hit_to_watchlist,
    effective_code,
    hit_to_watchlist_item,
    is_in_watchlist,
)


class QuickAddWatchlistTests(unittest.TestCase):
    def test_effective_code_a_share(self):
        h = SearchHit(code="600519", name="茅台", market="沪市A股", kind="A", yahoo="600519.SS")
        self.assertEqual(effective_code(h), "600519")

    def test_effective_code_us(self):
        h = SearchHit(code="SNX", name="Synnex", market="美股", kind="US", yahoo="SNX")
        self.assertEqual(effective_code(h), "SNX")

    def test_hit_to_watchlist_item(self):
        h = SearchHit(code="600519", name="茅台", market="沪市A股", kind="A", yahoo="600519.SS")
        item = hit_to_watchlist_item(h)
        self.assertEqual(item["代码"], "600519")
        self.assertEqual(item["名称"], "茅台")
        self.assertEqual(item["货币"], "CNY")

    def test_is_in_watchlist(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        self.assertTrue(is_in_watchlist(wl, "600519"))
        self.assertFalse(is_in_watchlist(wl, "000858"))

    def test_add_hit_new(self):
        h = SearchHit(code="600519", name="茅台", market="沪市A股", kind="A", yahoo="600519.SS")
        wl, added = add_hit_to_watchlist([], h)
        self.assertTrue(added)
        self.assertEqual(len(wl), 1)
        self.assertEqual(wl[0]["代码"], "600519")

    def test_add_hit_duplicate(self):
        h = SearchHit(code="600519", name="茅台", market="沪市A股", kind="A", yahoo="600519.SS")
        wl0 = [{"名称": "茅台", "代码": "600519", "类型": "A", "市场": "沪市A股"}]
        wl, added = add_hit_to_watchlist(wl0, h)
        self.assertFalse(added)
        self.assertEqual(len(wl), 1)


if __name__ == "__main__":
    unittest.main()
