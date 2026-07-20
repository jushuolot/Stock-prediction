"""P97 作战手册内置预览单元测试。"""

from __future__ import annotations

import unittest

from src.ui.playbook_preview import (
    PLAYBOOK_PATH,
    PREVIEW_LINE_LIMIT,
    SECTION_KEY,
    load_playbook_preview,
    playbook_file_path,
)


class PlaybookPreviewTests(unittest.TestCase):
    def test_playbook_file_exists(self):
        self.assertTrue(playbook_file_path().is_file())

    def test_preview_line_limit(self):
        full_lines = playbook_file_path().read_text(encoding="utf-8").splitlines()
        preview = load_playbook_preview()
        preview_lines = preview.splitlines()
        self.assertLessEqual(len(preview_lines), PREVIEW_LINE_LIMIT + 3)
        if len(full_lines) > PREVIEW_LINE_LIMIT:
            self.assertIn("完整手册", preview)

    def test_preview_contains_key_sections(self):
        preview = load_playbook_preview()
        self.assertIn("机构 vs 散户", preview)
        self.assertIn("每日 15 分钟流程", preview)
        self.assertIn("能力地图", preview)
        self.assertIn("推送与自动化", preview)

    def test_preview_path_constant(self):
        self.assertEqual(PLAYBOOK_PATH, "docs/PUBLIC_DATA_PLAYBOOK.md")

    def test_section_key(self):
        self.assertEqual(SECTION_KEY, "playbook_preview")


if __name__ == "__main__":
    unittest.main()
