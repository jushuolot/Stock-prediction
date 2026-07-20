"""P38 ?readonly=1 只读模式单元测试。"""

from __future__ import annotations

import unittest

from src.export.readonly_snapshot import build_readonly_snapshot
from src.util.readonly_mode import (
    SESSION_KEY,
    is_readonly_mode,
    parse_readonly_flag,
)


class ReadonlyParamTests(unittest.TestCase):
    def test_parse_truthy_values(self):
        for val in ("1", "true", "TRUE", " yes ", "on"):
            self.assertTrue(parse_readonly_flag(val), msg=val)

    def test_parse_falsy_values(self):
        for val in ("", "0", "false", "no", None, "readonly"):
            self.assertFalse(parse_readonly_flag(val), msg=repr(val))

    def test_is_readonly_mode_from_dict(self):
        self.assertTrue(is_readonly_mode({SESSION_KEY: True}))
        self.assertFalse(is_readonly_mode({SESSION_KEY: False}))
        self.assertFalse(is_readonly_mode({}))

    def test_snapshot_extra_readonly(self):
        snap = build_readonly_snapshot(
            watchlist=[],
            watch_snapshots={},
            briefs={},
            extra={"readonly_mode": True},
        )
        self.assertTrue(snap["meta"]["readonly_mode"])


if __name__ == "__main__":
    unittest.main()
