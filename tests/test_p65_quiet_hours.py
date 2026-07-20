"""P65 提醒静默时段单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from src.analysis.watch_alerts import WatchAlert
from src.notify.alert_push import maybe_push_alerts_if_configured
from src.util.quiet_hours import (
    is_in_quiet_hours,
    normalize_quiet_hours,
    quiet_hours_caption,
    quiet_hours_enabled,
)


class QuietHoursTests(unittest.TestCase):
    def test_normalize_disabled(self):
        self.assertEqual(normalize_quiet_hours({}), {"start": None, "end": None})

    def test_normalize_valid(self):
        self.assertEqual(normalize_quiet_hours({"start": 22, "end": 8}), {"start": 22, "end": 8})

    def test_same_day_window(self):
        qh = {"start": 9, "end": 17}
        self.assertTrue(is_in_quiet_hours(qh, now=datetime(2026, 6, 6, 10, 0)))
        self.assertFalse(is_in_quiet_hours(qh, now=datetime(2026, 6, 6, 18, 0)))

    def test_overnight_window(self):
        qh = {"start": 22, "end": 8}
        self.assertTrue(is_in_quiet_hours(qh, now=datetime(2026, 6, 6, 23, 0)))
        self.assertTrue(is_in_quiet_hours(qh, now=datetime(2026, 6, 6, 3, 0)))
        self.assertFalse(is_in_quiet_hours(qh, now=datetime(2026, 6, 6, 12, 0)))

    def test_caption(self):
        self.assertIn("22:00", quiet_hours_caption({"start": 22, "end": 8}))

    def test_enabled_flag(self):
        self.assertTrue(quiet_hours_enabled({"start": 22, "end": 8}))
        self.assertFalse(quiet_hours_enabled({}))

    def test_maybe_push_skips_during_quiet(self):
        alerts = [WatchAlert("1", "X", "hot", "涨 6%", "hot")]
        ss = {
            "push_webhook_on_alerts": True,
            "quiet_hours": {"start": 22, "end": 8},
        }
        quiet_now = datetime(2026, 6, 6, 23, 30)
        with patch("src.notify.alert_push.get_webhook_url", return_value="http://hook"):
            with patch("src.notify.alert_push.push_alerts_webhook") as push:
                out = maybe_push_alerts_if_configured(alerts, session_state=ss, now=quiet_now)
        self.assertIsNone(out)
        push.assert_not_called()

    def test_maybe_push_outside_quiet(self):
        alerts = [WatchAlert("1", "X", "hot", "涨 6%", "hot")]
        ss = {
            "push_webhook_on_alerts": True,
            "quiet_hours": {"start": 22, "end": 8},
        }
        day_now = datetime(2026, 6, 6, 12, 0)
        with patch("src.notify.alert_push.get_webhook_url", return_value="http://hook"):
            with patch("src.notify.alert_push.push_alerts_webhook", return_value=(True, "ok")):
                out = maybe_push_alerts_if_configured(alerts, session_state=ss, now=day_now)
        self.assertEqual(out, (True, "ok"))


if __name__ == "__main__":
    unittest.main()
