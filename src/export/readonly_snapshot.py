"""只读数据快照导出（P7，供脚本/同事只读接入）。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.util.query_time import format_query_datetime

try:
    from src.util.app_meta import APP_VERSION, EVOLUTION_STEP
except ImportError:
    APP_VERSION = "1.0.0"
    EVOLUTION_STEP = 0

SCHEMA = "stock-assistant-readonly-v2"


def _briefs_from_keys(session_state: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in session_state:
        sk = str(key)
        if sk.startswith("brief_md_"):
            val = session_state[key]
            if isinstance(val, str) and val.strip():
                out[sk.replace("brief_md_", "", 1)] = val.strip()
    return out


def build_readonly_snapshot(
    *,
    watchlist: list[dict[str, Any]],
    watch_snapshots: dict[str, Any],
    briefs: dict[str, str],
    query_label: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = query_label or format_query_datetime(datetime.now())
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": now,
        "disclaimer": "公开行情规则整理，非投资建议；只读快照，不可写回。",
        "watchlist": watchlist,
        "snapshots": watch_snapshots,
        "briefs": briefs,
        "counts": {
            "watchlist": len(watchlist),
            "snapshots": len(watch_snapshots),
            "briefs": len(briefs),
        },
        "app_version": APP_VERSION,
        "evolution_step": EVOLUTION_STEP,
    }
    if extra:
        payload["meta"] = extra
    return payload


def snapshot_to_json_bytes(snapshot: dict[str, Any]) -> bytes:
    return json.dumps(snapshot, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def collect_snapshot_from_session(session_state: Any) -> dict[str, Any]:
    briefs = _briefs_from_keys(session_state)
    return build_readonly_snapshot(
        watchlist=list(session_state.get("watchlist") or []),
        watch_snapshots=dict(session_state.get("watch_snapshots") or {}),
        briefs=briefs,
        query_label=str(session_state.get("query_label_watch") or ""),
        extra={
            "auto_refresh_enabled": bool(session_state.get("auto_refresh_enabled")),
            "auto_refresh_minutes": int(session_state.get("auto_refresh_minutes") or 0),
            "readonly_mode": bool(session_state.get("_readonly_mode")),
        },
    )
