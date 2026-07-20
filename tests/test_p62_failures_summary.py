"""P62 批量刷新失败汇总单元测试。"""

from __future__ import annotations

import unittest

from src.util.fetch_failures_summary import (
    collect_failed_codes,
    failures_expander_label,
    format_failures_for_copy,
)
from src.util.retry_fetch_ui import FETCH_FAIL_PREFIX


class FetchFailuresSummaryTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "600000"},
        {"名称": "B", "代码": "000001"},
        {"名称": "C", "代码": "AAPL"},
    ]

    def test_failures_expander_label(self):
        self.assertEqual(failures_expander_label(3), "失败 3 只")

    def test_format_failures_for_copy(self):
        self.assertEqual(format_failures_for_copy(["600000", "AAPL"]), "600000\nAAPL")

    def test_collect_failed_codes_order(self):
        snaps = {
            "600000": {"one_line": "ok"},
            "000001": {"one_line": f"{FETCH_FAIL_PREFIX}：timeout", "fetch_failed": True},
            "AAPL": {"fetch_failed": True},
        }
        self.assertEqual(collect_failed_codes(self.wl, snaps), ["000001", "AAPL"])

    def test_collect_failed_codes_empty(self):
        snaps = {"600000": {"one_line": "ok"}, "000001": {"one_line": "ok"}}
        self.assertEqual(collect_failed_codes(self.wl[:2], snaps), [])


if __name__ == "__main__":
    unittest.main()
