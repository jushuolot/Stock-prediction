"""P8 auth paths webhook 单元测试。"""

from __future__ import annotations

import unittest

from src.auth.users import safe_user_id
from src.notify.webhook import build_webhook_payload
from src.storage.paths import history_file_path


class AuthTests(unittest.TestCase):
    def test_safe_user_id(self):
        self.assertEqual(safe_user_id("alice"), "alice")
        self.assertEqual(safe_user_id("a/b"), "ab")


class PathTests(unittest.TestCase):
    def test_user_history_path(self):
        p = history_file_path(user_id="alice")
        self.assertIn("users", str(p))
        self.assertIn("alice", str(p))


class WebhookPayloadTests(unittest.TestCase):
    def test_build_payload(self):
        p = build_webhook_payload(
            digest_markdown="# hi",
            watchlist=[{"代码": "1"}],
            snapshots={},
            user_id="default",
        )
        self.assertEqual(p["schema"], "stock-assistant-webhook-v1")
        self.assertIn("digest_markdown", p)


if __name__ == "__main__":
    unittest.main()
