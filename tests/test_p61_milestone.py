"""P61/P99 千步庆祝横幅单元测试。"""

from __future__ import annotations

import unittest

from src.ui.milestone_banner import (
    EVOLUTION_100_PATH,
    MILESTONE_STEP,
    SESSION_FLAG,
    build_milestone_message,
    should_show_milestone,
)


class MilestoneBannerTests(unittest.TestCase):
    def test_build_message_contains_step_and_path(self):
        msg = build_milestone_message(1000)
        self.assertIn("1000", msg)
        self.assertIn(EVOLUTION_100_PATH, msg)
        self.assertIn("🎉", msg)

    def test_should_show_at_milestone(self):
        ss: dict = {}
        self.assertTrue(should_show_milestone(ss, step=MILESTONE_STEP))

    def test_should_not_show_below_milestone(self):
        ss: dict = {}
        self.assertFalse(should_show_milestone(ss, step=999))

    def test_should_not_show_twice(self):
        ss = {SESSION_FLAG: True}
        self.assertFalse(should_show_milestone(ss, step=MILESTONE_STEP))


if __name__ == "__main__":
    unittest.main()
