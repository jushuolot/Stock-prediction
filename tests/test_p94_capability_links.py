"""P94 能力地图快捷跳转单元测试。"""

from __future__ import annotations

import unittest

from src.ui.capability_map import (
    CAPABILITY_ITEMS,
    PLAYBOOK_PATH,
    capability_map_markdown,
)
from src.util.watch_expander_nav import (
    CAPABILITY_EXPAND_KEYS,
    apply_watch_expand_from_query,
    capability_watch_href,
    watch_section_expanded,
)


class CapabilityLinkTests(unittest.TestCase):
    def test_all_capabilities_have_expand_keys(self):
        modules = {m for _, m, _ in CAPABILITY_ITEMS}
        self.assertEqual(modules, set(CAPABILITY_EXPAND_KEYS))

    def test_capability_watch_href(self):
        self.assertEqual(
            capability_watch_href("sector_relative"),
            "?tab=watch&expand=sector_relative",
        )
        self.assertEqual(capability_watch_href("unknown"), "?tab=watch")

    def test_apply_expand_sets_session_and_tab(self):
        ss: dict = {"active_tab": "search"}
        qp = {"expand": "battle_plan"}
        resolved = apply_watch_expand_from_query(ss, qp)
        self.assertEqual(resolved, "battle_plan")
        self.assertEqual(ss["active_tab"], "watch")
        self.assertTrue(ss["watch_expand_battle_plan"])

    def test_apply_expand_ignores_unknown(self):
        ss: dict = {}
        self.assertIsNone(apply_watch_expand_from_query(ss, {"expand": "nope"}))
        self.assertNotIn("watch_expand_nope", ss)

    def test_watch_section_expanded_one_shot(self):
        ss = {"watch_expand_priority_queue": True}
        self.assertTrue(watch_section_expanded(ss, "priority_queue"))
        self.assertNotIn("watch_expand_priority_queue", ss)
        self.assertFalse(watch_section_expanded(ss, "priority_queue"))

    def test_capability_map_markdown_has_links(self):
        md = capability_map_markdown(step=940)
        for _, module, _ in CAPABILITY_ITEMS:
            self.assertIn(f"?tab=watch&expand={module}", md)
        self.assertIn(PLAYBOOK_PATH, md)


if __name__ == "__main__":
    unittest.main()
