"""share_message 与 cloud_preflight 单元测试。"""

from __future__ import annotations

import unittest

from src.util.cloud_preflight import check_requirements_text
from src.util.share_message import build_share_message


class ShareMessageTests(unittest.TestCase):
    def test_build_share_message(self):
        msg = build_share_message(app_url="https://demo.streamlit.app")
        self.assertIn("https://demo.streamlit.app", msg)
        self.assertIn("私发", msg)

    def test_build_share_message_with_password(self):
        msg = build_share_message(
            app_url="https://demo.streamlit.app",
            password="secret123",
            include_password=True,
        )
        self.assertIn("secret123", msg)


class CloudPreflightTests(unittest.TestCase):
    def test_rejects_curl_cffi_package(self):
        errs = check_requirements_text("curl_cffi>=0.5\nnumpy>=1.24,<2\n")
        self.assertTrue(any("curl_cffi" in e for e in errs))

    def test_accepts_current_requirements(self):
        from pathlib import Path

        req = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
        self.assertEqual(check_requirements_text(req), [])


if __name__ == "__main__":
    unittest.main()
