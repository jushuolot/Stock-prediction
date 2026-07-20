"""数据新鲜度徽章（P47）：摘要超过 stale_hours 显示 stale。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def normalize_stale_hours(raw: Any, *, default: float = 24.0) -> float:
    try:
        h = float(raw)
    except (TypeError, ValueError):
        return default
    return max(0.5, min(h, 168.0))


def parse_snapshot_time(updated_at: Any) -> datetime | None:
    text = str(updated_at or "").strip()
    if not text:
        return None
    for fmt in ("%Y年%m月%d日 %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def is_stale(
    updated_at: Any,
    *,
    stale_hours: float = 24.0,
    now: datetime | None = None,
) -> bool:
    ts = parse_snapshot_time(updated_at)
    if ts is None:
        return True
    ref = now or datetime.now()
    return ref - ts > timedelta(hours=normalize_stale_hours(stale_hours))


def freshness_badge(
    updated_at: Any,
    *,
    stale_hours: float = 24.0,
    now: datetime | None = None,
) -> str:
    if is_stale(updated_at, stale_hours=stale_hours, now=now):
        return "⏳ stale"
    return ""


def snapshot_price(snap: dict[str, Any]) -> float | None:
    for key in ("price", "收盘", "最新价"):
        val = snap.get(key)
        if val is None:
            continue
        try:
            p = float(val)
        except (TypeError, ValueError):
            continue
        if p > 0:
            return p
    return None
