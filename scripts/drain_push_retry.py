"""推送重试队列消费（P9 cron）。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.notify.digest_push import push_digest_email, push_digest_webhook  # noqa: E402
from src.notify.retry import drain_queue, load_queue  # noqa: E402


def main() -> int:
    user = os.environ.get("STOCK_USER", "default").strip() or "default"

    class SS:
        def __init__(self, d: dict) -> None:
            self._d = d

        def get(self, k, default=None):
            return self._d.get(k, default)

    def handler(item: dict) -> tuple[bool, str]:
        digest = str(item.get("digest") or "")
        ss = SS(item.get("session") or {})
        ch = str(item.get("channel") or "")
        if ch == "webhook":
            return push_digest_webhook(digest=digest, session_state=ss)
        if ch == "email":
            return push_digest_email(digest=digest)
        return False, f"unknown channel {ch}"

    if not load_queue(user_id=user):
        print("[drain_push_retry] queue empty")
        return 0
    logs = drain_queue(handler, user_id=user)
    for line in logs:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
