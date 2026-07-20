"""P24 深色模式偏好单元测试。"""

from __future__ import annotations

import unittest

from src.ui.theme_style import _LIGHT_CSS, inject_theme_styles


class ThemeStyleTests(unittest.TestCase):
    def test_light_css_defined(self):
        self.assertIn("background-color", _LIGHT_CSS)
        self.assertIn("#fafafa", _LIGHT_CSS)

    def test_inject_theme_no_crash_without_streamlit(self):
        # inject_theme_styles imports streamlit; smoke import only
        self.assertTrue(callable(inject_theme_styles))


if __name__ == "__main__":
    unittest.main()
