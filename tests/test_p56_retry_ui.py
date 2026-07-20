"""P56 摘要拉取失败重试 UI 逻辑单元测试。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.util.retry_fetch_ui import (
    FETCH_FAIL_PREFIX,
    failed_tickers,
    is_snapshot_fetch_failed,
    refresh_one_snapshot,
    retry_button_key,
)


class RetryFetchUiTests(unittest.TestCase):
    wl = [
        {"名称": "A", "代码": "1"},
        {"名称": "B", "代码": "2"},
    ]

    def test_is_snapshot_fetch_failed(self):
        self.assertFalse(is_snapshot_fetch_failed(None))
        self.assertFalse(is_snapshot_fetch_failed({"one_line": "正常摘要"}))
        self.assertTrue(is_snapshot_fetch_failed({"fetch_failed": True}))
        self.assertTrue(
            is_snapshot_fetch_failed({"one_line": f"{FETCH_FAIL_PREFIX}：timeout"})
        )

    def test_failed_tickers_order(self):
        snaps = {
            "1": {"one_line": "ok"},
            "2": {"one_line": f"{FETCH_FAIL_PREFIX}：err", "fetch_failed": True},
        }
        self.assertEqual(failed_tickers(self.wl, snaps), ["2"])

    def test_retry_button_key(self):
        self.assertEqual(retry_button_key("600000"), "watch_retry_600000")

    def test_refresh_one_snapshot_success(self):
        fetch = MagicMock(return_value=(MagicMock(empty=False), "src"))
        with unittest.mock.patch(
            "src.util.retry_fetch_ui.analyze_watch_light",
            return_value=MagicMock(
                updated_at="",
                as_dict=lambda: {"code": "1", "one_line": "ok", "pct": 1.0},
            ),
        ):
            snap, ok = refresh_one_snapshot(self.wl[0], fetch, query_label="t1")
        self.assertTrue(ok)
        self.assertEqual(snap["one_line"], "ok")

    def test_refresh_one_snapshot_failure(self):
        fetch = MagicMock(side_effect=RuntimeError("net"))
        snap, ok = refresh_one_snapshot(self.wl[0], fetch, query_label="t1")
        self.assertFalse(ok)
        self.assertTrue(is_snapshot_fetch_failed(snap))
        self.assertIn("net", snap["one_line"])


if __name__ == "__main__":
    unittest.main()
