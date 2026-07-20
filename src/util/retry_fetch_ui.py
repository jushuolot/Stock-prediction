"""摘要拉取失败重试（P56）：检测失败快照与单行重试逻辑。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from src.analysis.quick_analyze import WatchSnapshot, analyze_watch_light
from src.util.query_time import format_query_datetime

FETCH_FAIL_PREFIX = "拉取失败"


def is_snapshot_fetch_failed(snap: dict[str, Any] | None) -> bool:
    if not snap:
        return False
    if snap.get("fetch_failed"):
        return True
    return str(snap.get("one_line") or "").startswith(FETCH_FAIL_PREFIX)


def failed_tickers(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
) -> list[str]:
    """返回当前列表中摘要拉取失败的代码（保持 watchlist 顺序）。"""
    out: list[str] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        if code and is_snapshot_fetch_failed(snapshots.get(code)):
            out.append(code)
    return out


def retry_button_key(code: str) -> str:
    return f"watch_retry_{code}"


def _fail_snapshot(item: dict[str, Any], exc: Exception, label: str) -> dict[str, Any]:
    code = str(item.get("代码") or "")
    return WatchSnapshot(
        code=code,
        name=str(item.get("名称") or code),
        pct=None,
        score=None,
        one_line=f"{FETCH_FAIL_PREFIX}：{exc}",
        updated_at=label,
    ).as_dict() | {"fetch_failed": True}


def refresh_one_snapshot(
    item: dict[str, Any],
    fetch_fn: Callable[..., Any],
    *,
    query_label: str = "",
) -> tuple[dict[str, Any], bool]:
    """重试单只标的摘要；返回 (snapshot dict, 是否成功)。"""
    code = str(item.get("代码") or "")
    label = query_label or format_query_datetime(datetime.now())
    try:
        snap = analyze_watch_light(item, fetch_fn)
        snap.updated_at = label
        d = snap.as_dict()
        d.pop("fetch_failed", None)
        return d, True
    except Exception as exc:
        return _fail_snapshot(item, exc, label), False
