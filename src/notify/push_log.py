"""推送结果持久化日志（P9）。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.storage.paths import project_root, safe_user_id
from src.util.query_time import format_query_datetime

_MAX_LINES = 500
_KEEP_LINES = 200


def push_log_path(*, user_id: str = "default") -> Path:
    uid = safe_user_id(user_id)
    p = project_root() / "data" / "users" / uid / "push_log.jsonl"
    if uid == "default":
        legacy = project_root() / "data" / "push_log.jsonl"
        if legacy.exists() and not p.exists():
            return legacy
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def record_push(
    *,
    channel: str,
    ok: bool,
    detail: str,
    user_id: str = "default",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "at": format_query_datetime(datetime.now()),
        "channel": channel,
        "ok": bool(ok),
        "detail": str(detail)[:500],
        "user_id": safe_user_id(user_id),
    }
    if extra:
        entry.update(extra)
    path = push_log_path(user_id=user_id)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _rotate(path)
    return entry


def read_recent(*, user_id: str = "default", limit: int = 10) -> list[dict[str, Any]]:
    path = push_log_path(user_id=user_id)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict[str, Any]] = []
    for line in reversed(lines[-max(limit, 1) * 3 :]):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(out) >= limit:
            break
    return out


def _rotate(path: Path) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) <= _MAX_LINES:
        return
    kept = lines[-_KEEP_LINES:]
    tmp = path.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(kept) + "\n", encoding="utf-8")
    tmp.replace(path)
