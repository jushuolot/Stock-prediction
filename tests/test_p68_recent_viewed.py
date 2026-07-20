"""P68 最近查看标的单元测试。"""

from __future__ import annotations

import unittest

from src.util.recent_viewed import (
    RECENT_VIEWED_MAX,
    chip_label,
    normalize_recent_viewed,
    push_recent_viewed,
    push_recent_viewed_many,
)


class RecentViewedTests(unittest.TestCase):
    def test_normalize_dedupes_and_legacy_keys(self):
        raw = [
            {"代码": "600519", "名称": "茅台"},
            {"code": "600519", "name": "茅台"},
            {"code": "601398", "name": "工行"},
        ]
        self.assertEqual(
            normalize_recent_viewed(raw),
            [{"code": "600519", "name": "茅台"}, {"code": "601398", "name": "工行"}],
        )

    def test_push_moves_to_front(self):
        hist = push_recent_viewed(
            [{"code": "600519", "name": "茅台"}],
            code="601398",
            name="工行",
        )
        self.assertEqual(hist[0]["code"], "601398")
        self.assertEqual(len(hist), 2)

    def test_push_dedupes_existing(self):
        hist = push_recent_viewed(
            [{"code": "600519", "name": "茅台"}, {"code": "601398", "name": "工行"}],
            code="601398",
            name="工行",
        )
        self.assertEqual(hist[0]["code"], "601398")
        self.assertEqual(hist.count({"code": "601398", "name": "工行"}), 1)
        self.assertEqual(len(hist), 2)

    def test_max_ten(self):
        base = [{"code": f"{i:06d}", "name": f"n{i}"} for i in range(RECENT_VIEWED_MAX)]
        hist = push_recent_viewed(base, code="999999", name="新")
        self.assertEqual(len(hist), RECENT_VIEWED_MAX)
        self.assertEqual(hist[0]["code"], "999999")
        self.assertNotIn("000009", [x["code"] for x in hist])

    def test_chip_label(self):
        self.assertEqual(chip_label({"code": "600519", "name": "茅台"}), "茅台 (600519)")
        self.assertEqual(chip_label({"code": "AAPL", "name": "AAPL"}), "AAPL")

    def test_push_many_batch_order(self):
        hist = push_recent_viewed_many(
            [],
            [("600519", "茅台"), ("601398", "工行"), ("300557", "理工光科")],
        )
        self.assertEqual(len(hist), 3)
        self.assertEqual(hist[0]["code"], "300557")
        self.assertEqual(hist[1]["code"], "601398")
        self.assertEqual(hist[2]["code"], "600519")

    def test_normalize_non_list(self):
        self.assertEqual(normalize_recent_viewed({}), [])
        self.assertEqual(normalize_recent_viewed("x"), [])


if __name__ == "__main__":
    unittest.main()
