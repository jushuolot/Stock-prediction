"""P9 运维：推送日志、重试、健康告警。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.notify.health_alert import maybe_send_health_alert
from src.notify.push_log import push_log_path, read_recent, record_push
from src.notify.retry import enqueue_retry, load_queue, retry_with_backoff, save_queue
from src.storage.paths import safe_user_id


class PushLogTests(unittest.TestCase):
    def test_record_and_read(self):
        with tempfile.TemporaryDirectory() as td:
            uid = "testuser"
            p = Path(td) / "push_log.jsonl"

            def fake_path(*, user_id: str = "default"):
                assert safe_user_id(user_id) == uid
                return p

            with patch("src.notify.push_log.push_log_path", fake_path):
                record_push(channel="webhook", ok=True, detail="ok", user_id=uid)
                rows = read_recent(user_id=uid, limit=5)
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["ok"])


class RetryTests(unittest.TestCase):
    def test_retry_backoff_success(self):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            return calls["n"] >= 2, "done"

        with patch("src.notify.retry.time.sleep", lambda *_: None):
            ok, msg = retry_with_backoff(fn, max_attempts=3, base_delay=0.01)
        self.assertTrue(ok)

    def test_queue_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "q.json"

            def fake_path(*, user_id: str = "default"):
                return p

            with patch("src.notify.retry.retry_queue_path", fake_path):
                enqueue_retry({"channel": "email", "digest": "x"}, user_id="u1")
                self.assertEqual(len(load_queue(user_id="u1")), 1)
                save_queue([], user_id="u1")
                self.assertEqual(load_queue(user_id="u1"), [])


class HealthAlertTests(unittest.TestCase):
    def test_debounce(self):
        with tempfile.TemporaryDirectory() as td:
            state_p = Path(td) / "state.json"

            def fake_state(*, user_id: str = "default"):
                return state_p

            probes = [{"name": "东财", "ok": False, "detail": "fail"}]
            with patch("src.notify.health_alert._state_path", fake_state):
                with patch("src.notify.health_alert.get_health_alert_webhook_url", return_value="http://x"):
                    with patch("src.notify.health_alert.post_webhook", return_value=(True, "ok")):
                        ok1, _ = maybe_send_health_alert(probes, debounce_seconds=3600)
                        ok2, msg2 = maybe_send_health_alert(probes, debounce_seconds=3600)
            self.assertTrue(ok1)
            self.assertFalse(ok2)


if __name__ == "__main__":
    unittest.main()
