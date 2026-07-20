"""P91 900 步庆祝 + 公开数据能力地图单元测试。"""

from __future__ import annotations

import unittest

from src.ui.capability_map import CAPABILITY_ITEMS, SECTION_KEY, capability_map_markdown
from src.ui.milestone_banner import (
    EVOLUTION_100_PATH,
    MILESTONE_STEP,
    SESSION_FLAG,
    build_milestone_message,
    should_show_milestone,
)


class CapabilityMapTests(unittest.TestCase):
    def test_capability_items_cover_key_features(self):
        titles = " ".join(t for t, _, _ in CAPABILITY_ITEMS)
        self.assertIn("相对板块", titles)
        self.assertIn("一页纸", titles)
        self.assertIn("作战清单", titles)
        self.assertIn("优先关注", titles)
        self.assertEqual(len(CAPABILITY_ITEMS), 4)

    def test_capability_map_markdown_modules(self):
        md = capability_map_markdown(step=1000)
        self.assertIn("sector_relative", md)
        self.assertIn("institutional_onepager", md)
        self.assertIn("battle_plan", md)
        self.assertIn("priority_queue", md)
        self.assertIn("1000", md)

    def test_section_key(self):
        self.assertEqual(SECTION_KEY, "capability_map")


class Milestone1000Tests(unittest.TestCase):
    def test_build_message_1000(self):
        msg = build_milestone_message(1000)
        self.assertIn("1000", msg)
        self.assertIn(EVOLUTION_100_PATH, msg)
        self.assertIn("作战手册", msg)
        self.assertIn("🎉", msg)

    def test_milestone_step_is_1000(self):
        self.assertEqual(MILESTONE_STEP, 1000)

    def test_should_show_at_1000(self):
        ss: dict = {}
        self.assertTrue(should_show_milestone(ss, step=MILESTONE_STEP))

    def test_should_not_show_below_1000(self):
        ss: dict = {}
        self.assertFalse(should_show_milestone(ss, step=999))

    def test_should_not_show_twice(self):
        ss = {SESSION_FLAG: True}
        self.assertFalse(should_show_milestone(ss, step=MILESTONE_STEP))


if __name__ == "__main__":
    unittest.main()
