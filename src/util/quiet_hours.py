"""提醒静默时段（P65）：本地小时窗口内跳过自动 Webhook 推送。"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def normalize_hour(value: Any, *, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        h = int(float(value))
    except (TypeError, ValueError):
        return default
    if 0 <= h <= 23:
        return h
    return default


def normalize_quiet_hours(raw: Any) -> dict[str, int | None]:
    """返回 {start, end}；均为 None 表示未启用。"""
    if not isinstance(raw, dict):
        return {"start": None, "end": None}
    start = normalize_hour(raw.get("start"))
    end = normalize_hour(raw.get("end"))
    if start is None or end is None:
        return {"start": None, "end": None}
    return {"start": start, "end": end}


def quiet_hours_enabled(qh: dict[str, int | None]) -> bool:
    n = normalize_quiet_hours(qh)
    return n["start"] is not None and n["end"] is not None


def is_in_quiet_hours(
    qh: dict[str, int | None],
    *,
    now: datetime | None = None,
) -> bool:
    """判断当前本地小时是否落在静默窗口内（支持跨午夜）。"""
    n = normalize_quiet_hours(qh)
    start = n["start"]
    end = n["end"]
    if start is None or end is None:
        return False
    if start == end:
        return False
    dt = now or datetime.now()
    hour = dt.hour
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def quiet_hours_caption(qh: dict[str, int | None]) -> str:
    n = normalize_quiet_hours(qh)
    if not quiet_hours_enabled(n):
        return "未设置静默时段"
    return f"{n['start']:02d}:00 – {n['end']:02d}:00（本地）"
