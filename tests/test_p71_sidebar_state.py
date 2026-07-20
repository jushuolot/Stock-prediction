"""P71 侧边栏折叠状态单元测试。"""

from __future__ import annotations

import unittest

from src.util.sidebar_state import (
    is_section_collapsed,
    normalize_sidebar_collapsed,
    set_section_collapsed,
)


class SidebarStateTests(unittest.TestCase):
    def test_normalize_filters_unknown(self):
        raw = {"workflow_phase": True, "other": False, "": True}
        self.assertEqual(normalize_sidebar_collapsed(raw), {"workflow_phase": True})

    def test_normalize_non_dict(self):
        self.assertEqual(normalize_sidebar_collapsed([]), {})
        self.assertEqual(normalize_sidebar_collapsed(None), {})

    def test_is_section_collapsed_default(self):
        self.assertFalse(is_section_collapsed({}, "workflow_phase"))
        self.assertTrue(is_section_collapsed({"workflow_phase": True}, "workflow_phase"))

    def test_set_section_collapsed(self):
        c = set_section_collapsed({}, "workflow_phase", True)
        self.assertEqual(c, {"workflow_phase": True})
        c2 = set_section_collapsed(c, "workflow_phase", False)
        self.assertEqual(c2, {})

    def test_set_unknown_section_ignored(self):
        c = set_section_collapsed({}, "unknown", True)
        self.assertEqual(c, {})


if __name__ == "__main__":
    unittest.main()
