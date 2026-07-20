"""P28 自选股笔记单元测试。"""

from __future__ import annotations

import unittest

from src.util.watch_notes import (
    get_note,
    normalize_watch_notes,
    remove_ticker_note,
    remove_tickers_notes,
    set_note,
)


class WatchNotesTests(unittest.TestCase):
    def test_normalize(self):
        raw = {"600519": " 核心持仓 ", "": "x", "601398": ""}
        self.assertEqual(normalize_watch_notes(raw), {"600519": "核心持仓"})
        self.assertEqual(normalize_watch_notes([]), {})

    def test_get_set_note(self):
        notes: dict[str, str] = {}
        self.assertEqual(get_note(notes, "600519"), "")
        notes = set_note(notes, "600519", " 观察 ")
        self.assertEqual(get_note(notes, "600519"), "观察")
        notes = set_note(notes, "600519", "")
        self.assertEqual(notes, {})

    def test_remove_notes(self):
        notes = {"600519": "a", "601398": "b"}
        self.assertEqual(remove_ticker_note(notes, "600519"), {"601398": "b"})
        self.assertEqual(
            remove_tickers_notes(notes, ["600519", "601398"]),
            {},
        )


if __name__ == "__main__":
    unittest.main()
