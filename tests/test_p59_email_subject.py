"""P59 汇总邮件主题行单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from src.analysis.watch_alerts import compute_watch_alerts
from src.notify.digest_push import (
    alert_count_for_session,
    format_digest_email_subject,
)


class EmailSubjectTests(unittest.TestCase):
    def test_subject_with_alerts(self):
        subj = format_digest_email_subject(
            alert_count=3,
            watch_count=5,
            when=datetime(2025, 6, 6, 9, 0),
        )
        self.assertIn("2025-06-06", subj)
        self.assertIn("3 条提醒", subj)
        self.assertNotIn("5 只", subj)

    def test_subject_no_alerts_shows_watch_count(self):
        subj = format_digest_email_subject(
            alert_count=0,
            watch_count=8,
            when=datetime(2025, 6, 6),
        )
        self.assertIn("2025-06-06", subj)
        self.assertIn("8 只", subj)
        self.assertNotIn("提醒", subj)

    def test_subject_empty_watchlist(self):
        subj = format_digest_email_subject(alert_count=0, watch_count=0)
        self.assertIn("自选股速览", subj)
        self.assertNotIn("提醒", subj)

    def test_alert_count_for_session(self):
        ss = {
            "watchlist": [{"名称": "茅台", "代码": "600519"}],
            "watch_snapshots": {"600519": {"pct": 6.0, "score": 70.0}},
            "alert_pct_up": 5.0,
            "alert_pct_down": -5.0,
            "alert_score_low": 40.0,
            "alert_score_high": 65.0,
            "price_targets": {},
        }
        n = alert_count_for_session(ss)
        self.assertEqual(n, len(compute_watch_alerts(ss["watchlist"], ss["watch_snapshots"], pct_up=5.0)))
        self.assertGreater(n, 0)

    @patch("src.notify.digest_push.send_digest_email", return_value=(True, "ok"))
    @patch("src.notify.digest_push.retry_with_backoff", side_effect=lambda fn, **kw: fn())
    @patch("src.notify.digest_push.record_push")
    def test_push_digest_email_uses_smart_subject(self, _rec, _retry, mock_send):
        from src.notify.digest_push import push_digest_email

        ss = {
            "watchlist": [{"名称": "茅台", "代码": "600519"}],
            "watch_snapshots": {"600519": {"pct": 6.0, "score": 70.0}},
            "alert_pct_up": 5.0,
            "_auth_user": "default",
        }
        push_digest_email(digest="# test", session_state=ss)
        mock_send.assert_called_once()
        subject = mock_send.call_args.kwargs["subject"]
        self.assertIn("条提醒", subject)


if __name__ == "__main__":
    unittest.main()
