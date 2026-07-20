"""P17 alert_push 单元测试。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.analysis.watch_alerts import WatchAlert
from src.notify.alert_push import (
    alerts_fingerprint,
    build_alert_webhook_payload,
    maybe_push_alerts_if_configured,
    push_alerts_webhook,
)


class AlertPushTests(unittest.TestCase):
    def test_fingerprint_stable(self):
        alerts = [
            WatchAlert("1", "A", "hot", "涨 6%", "hot"),
            WatchAlert("2", "B", "warn", "跌 -6%", "warn"),
        ]
        self.assertEqual(alerts_fingerprint(alerts), alerts_fingerprint(list(reversed(alerts))))

    def test_payload_schema(self):
        alerts = [WatchAlert("600000", "浦发", "hot", "涨 6%", "hot")]
        p = build_alert_webhook_payload(alerts, user_id="u1", app_url="http://x")
        self.assertEqual(p["schema"], "stock-assistant-webhook-v1")
        self.assertEqual(p["kind"], "watch_alerts")
        self.assertEqual(p["alert_count"], 1)
        self.assertIn("digest_markdown", p)

    def test_push_alerts_webhook_mock(self):
        alerts = [WatchAlert("1", "X", "hot", "涨 6%", "hot")]
        ss = MagicMock()
        ss.get.side_effect = lambda k, default=None: {"_auth_user": "test"}.get(k, default)
        with patch("src.notify.alert_push.get_webhook_url", return_value="http://hook"):
            with patch("src.notify.alert_push.retry_with_backoff", return_value=(True, "HTTP 200")):
                with patch("src.notify.alert_push.record_push") as log:
                    ok, msg = push_alerts_webhook(alerts, session_state=ss)
        self.assertTrue(ok)
        self.assertIn("200", msg)
        log.assert_called_once()
        self.assertEqual(log.call_args.kwargs["channel"], "alert_webhook")

    def test_maybe_push_skips_duplicate(self):
        alerts = [WatchAlert("1", "X", "hot", "涨 6%", "hot")]
        ss = {
            "push_webhook_on_alerts": True,
            "_last_alert_push_fp": alerts_fingerprint(alerts),
        }
        with patch("src.notify.alert_push.get_webhook_url", return_value="http://hook"):
            with patch("src.notify.alert_push.push_alerts_webhook") as push:
                out = maybe_push_alerts_if_configured(alerts, session_state=ss)
        self.assertIsNone(out)
        push.assert_not_called()

    def test_maybe_push_when_enabled(self):
        alerts = [WatchAlert("1", "X", "hot", "涨 6%", "hot")]
        ss = {"push_webhook_on_alerts": True}
        with patch("src.notify.alert_push.get_webhook_url", return_value="http://hook"):
            with patch("src.notify.alert_push.push_alerts_webhook", return_value=(True, "ok")):
                out = maybe_push_alerts_if_configured(alerts, session_state=ss)
        self.assertEqual(out, (True, "ok"))
        self.assertEqual(ss["_last_alert_push_fp"], alerts_fingerprint(alerts))


if __name__ == "__main__":
    unittest.main()
