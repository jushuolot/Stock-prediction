"""推送重试队列（P9）。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

from src.storage.paths import project_root, safe_user_id

T = TypeVar("T")
_MAX_QUEUE = 20


def retry_queue_path(*, user_id: str = "default") -> Path:
    uid = safe_user_id(user_id)
    p = project_root() / "data" / "users" / uid / "push_retry_queue.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_queue(*, user_id: str = "default") -> list[dict[str, Any]]:
    path = retry_queue_path(user_id=user_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_queue(items: list[dict[str, Any]], *, user_id: str = "default") -> None:
    path = retry_queue_path(user_id=user_id)
    path.write_text(json.dumps(items[-_MAX_QUEUE:], ensure_ascii=False, indent=2), encoding="utf-8")


def enqueue_retry(item: dict[str, Any], *, user_id: str = "default") -> None:
    q = load_queue(user_id=user_id)
    item = dict(item)
    item.setdefault("enqueued_at", time.time())
    item.setdefault("attempts", 0)
    q.append(item)
    save_queue(q, user_id=user_id)


def drain_queue(
    handler: Callable[[dict[str, Any]], tuple[bool, str]],
    *,
    user_id: str = "default",
    max_items: int = 10,
) -> list[str]:
    q = load_queue(user_id=user_id)
    if not q:
        return []
    remaining: list[dict[str, Any]] = []
    logs: list[str] = []
    for item in q[: max(1, int(max_items))]:
        item["attempts"] = int(item.get("attempts") or 0) + 1
        ok, msg = handler(item)
        if ok:
            logs.append(f"retry ok: {item.get('channel')} {msg}")
        elif int(item["attempts"]) >= 5:
            logs.append(f"retry drop: {item.get('channel')} {msg}")
        else:
            remaining.append(item)
            logs.append(f"retry fail: {item.get('channel')} {msg}")
    remaining.extend(q[max_items:])
    save_queue(remaining, user_id=user_id)
    return logs


def retry_with_backoff(
    fn: Callable[[], tuple[bool, str]],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> tuple[bool, str]:
    last = ""
    for i in range(max(1, max_attempts)):
        ok, msg = fn()
        last = msg
        if ok:
            return True, msg
        if i < max_attempts - 1:
            time.sleep(base_delay * (4**i))
    return False, last
