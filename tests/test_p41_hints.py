"""P41 快捷键/URL 提示单元测试。"""

from __future__ import annotations

import unittest

from src.ui.keyboard_hints import format_keyboard_hints


class KeyboardHintsTests(unittest.TestCase):
    def test_format_zh_contains_tab_and_readonly(self):
        text = format_keyboard_hints(locale="zh")
        self.assertIn("?tab=watch", text)
        self.assertIn("?readonly=1", text)
        self.assertIn("只读", text)

    def test_format_en_contains_hints(self):
        text = format_keyboard_hints(locale="en")
        self.assertIn("?tab=search", text)
        self.assertIn("Read-only", text)


if __name__ == "__main__":
    unittest.main()
