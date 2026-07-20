"""P18 tab_router 单元测试。"""

from __future__ import annotations

import unittest

from src.ui.tab_router import resolve_tab_id


class TabRouterTests(unittest.TestCase):
    def test_resolve_aliases(self):
        self.assertEqual(resolve_tab_id("watch"), "watch")
        self.assertEqual(resolve_tab_id("1"), "watch")
        self.assertEqual(resolve_tab_id("搜索"), "search")
        self.assertEqual(resolve_tab_id("history"), "history")
        self.assertEqual(resolve_tab_id("④ 历史记录"), "history")
        self.assertEqual(resolve_tab_id("全球股市"), "movers")
        self.assertEqual(resolve_tab_id("板块行情"), "plates")

    def test_resolve_unknown(self):
        self.assertIsNone(resolve_tab_id(""))
        self.assertIsNone(resolve_tab_id("unknown_tab_xyz"))


if __name__ == "__main__":
    unittest.main()
