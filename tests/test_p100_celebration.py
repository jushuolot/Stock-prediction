"""P100 v5 千步庆祝横幅单元测试。"""

from __future__ import annotations

import unittest

from src.ui.milestone_banner import SESSION_FLAG as MILESTONE_SESSION_FLAG
from src.ui.v5_celebration_banner import (
    EVOLUTION_100_PATH,
    SESSION_FLAG,
    V5_CELEBRATION_MIN_STEP,
    build_v5_celebration_message,
    should_show_v5_celebration,
)


class V5CelebrationTests(unittest.TestCase):
    def test_build_message_contains_version_and_path(self):
        msg = build_v5_celebration_message(version="5.0.0", step=1000)
        self.assertIn("5.0.0", msg)
        self.assertIn("1000", msg)
        self.assertIn(EVOLUTION_100_PATH, msg)
        self.assertIn("v5", msg.lower())

    def test_min_step_is_1000(self):
        self.assertEqual(V5_CELEBRATION_MIN_STEP, 1000)

    def test_should_show_at_step_1000(self):
        ss: dict = {}
        self.assertTrue(should_show_v5_celebration(ss, step=1000))

    def test_should_not_show_below_1000(self):
        ss: dict = {}
        self.assertFalse(should_show_v5_celebration(ss, step=999))

    def test_should_not_show_twice(self):
        ss = {SESSION_FLAG: True}
        self.assertFalse(should_show_v5_celebration(ss, step=1000))

    def test_distinct_session_flag_from_milestone(self):
        self.assertNotEqual(SESSION_FLAG, MILESTONE_SESSION_FLAG)


if __name__ == "__main__":
    unittest.main()
