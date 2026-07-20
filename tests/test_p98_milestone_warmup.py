"""P98 千步预热横幅与页脚提示单元测试。"""

from __future__ import annotations

import unittest

from src.ui.footer import build_footer_warmup_note
from src.ui.milestone_banner import (
    MILESTONE_STEP,
    WARMUP_MIN_STEP,
    WARMUP_SESSION_FLAG,
    build_warmup_message,
    should_show_warmup,
)


class MilestoneWarmupTests(unittest.TestCase):
    def test_warmup_message_at_960(self):
        msg = build_warmup_message(960)
        self.assertIn("960", msg)
        self.assertIn("40", msg)
        self.assertIn("千步", msg)

    def test_warmup_min_step(self):
        self.assertEqual(WARMUP_MIN_STEP, 960)

    def test_should_show_warmup_in_range(self):
        ss: dict = {}
        self.assertTrue(should_show_warmup(ss, step=960))
        self.assertTrue(should_show_warmup(ss, step=999))

    def test_should_not_show_warmup_below_min(self):
        ss: dict = {}
        self.assertFalse(should_show_warmup(ss, step=959))

    def test_should_not_show_warmup_at_milestone(self):
        ss: dict = {}
        self.assertFalse(should_show_warmup(ss, step=MILESTONE_STEP))

    def test_should_not_show_warmup_twice(self):
        ss = {WARMUP_SESSION_FLAG: True}
        self.assertFalse(should_show_warmup(ss, step=960))

    def test_footer_note_below_milestone(self):
        note = build_footer_warmup_note(960)
        self.assertIsNotNone(note)
        self.assertIn("千步预热", note)
        self.assertIn("40", note)

    def test_footer_note_at_milestone(self):
        note = build_footer_warmup_note(MILESTONE_STEP)
        self.assertIsNotNone(note)
        self.assertIn("千步进化里程碑", note)

    def test_footer_note_below_warmup_min(self):
        self.assertIsNone(build_footer_warmup_note(959))


if __name__ == "__main__":
    unittest.main()
