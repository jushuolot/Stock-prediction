"""P34 搜索历史单元测试。"""

from __future__ import annotations

import unittest

from src.util.search_history import (
    SEARCH_HISTORY_MAX,
    normalize_search_history,
    push_search,
    remove_search_term,
)


class SearchHistoryTests(unittest.TestCase):
    def test_normalize_dedupes_and_trims(self):
        raw = [" 茅台 ", "600519", "茅台", "", "SNX", None]
        self.assertEqual(normalize_search_history(raw), ["茅台", "600519", "SNX"])

    def test_push_moves_to_front(self):
        hist = push_search(["600519", "茅台"], "SNX")
        self.assertEqual(hist, ["SNX", "600519", "茅台"])

    def test_push_dedupes_existing(self):
        hist = push_search(["600519", "茅台", "工行"], "茅台")
        self.assertEqual(hist[0], "茅台")
        self.assertEqual(hist.count("茅台"), 1)

    def test_max_twenty(self):
        base = [f"t{i}" for i in range(SEARCH_HISTORY_MAX)]
        hist = push_search(base, "new")
        self.assertEqual(len(hist), SEARCH_HISTORY_MAX)
        self.assertEqual(hist[0], "new")
        self.assertNotIn(f"t{SEARCH_HISTORY_MAX - 1}", hist)

    def test_remove_term(self):
        hist = remove_search_term(["茅台", "600519"], "茅台")
        self.assertEqual(hist, ["600519"])

    def test_normalize_non_list(self):
        self.assertEqual(normalize_search_history({}), [])
        self.assertEqual(normalize_search_history("x"), [])


if __name__ == "__main__":
    unittest.main()
