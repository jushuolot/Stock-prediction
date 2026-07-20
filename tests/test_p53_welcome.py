"""P53 会话恢复欢迎条单元测试。"""

from __future__ import annotations

import unittest

from src.ui.welcome_banner import build_welcome_message, should_show_welcome


class WelcomeBannerTests(unittest.TestCase):
    def test_build_message_with_count_and_refresh(self):
        ss = {
            "watchlist": [{"代码": "1"}, {"代码": "2"}],
            "query_label_watch": "2026-06-06 10:00",
        }
        msg = build_welcome_message(ss)
        self.assertIn("2", msg)
        self.assertIn("2026-06-06 10:00", msg)

    def test_should_show_when_restored(self):
        ss = {
            "_restored_watchlist": True,
            "watchlist": [{"代码": "600519"}],
        }
        self.assertTrue(should_show_welcome(ss))

    def test_should_not_show_without_restore(self):
        ss = {"watchlist": [{"代码": "600519"}]}
        self.assertFalse(should_show_welcome(ss))

    def test_should_not_show_twice(self):
        ss = {
            "_restored_watchlist": True,
            "_welcome_banner_shown": True,
            "watchlist": [{"代码": "600519"}],
        }
        self.assertFalse(should_show_welcome(ss))


if __name__ == "__main__":
    unittest.main()
