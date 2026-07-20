"""工作台仪表盘聚合指标（P37）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analysis.watch_alerts import compute_watch_alerts


@dataclass(frozen=True)
class DashboardStats:
    watch_count: int
    snapshot_count: int
    scored_count: int
    avg_score: float | None
    up_count: int
    down_count: int
    flat_count: int
    alert_count: int


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def compute_dashboard_stats(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
) -> DashboardStats:
    """从 watch_snapshots 聚合均分、涨跌家数与当日提醒条数。"""
    watch_count = len(watchlist)
    snapshot_count = 0
    scored_count = 0
    score_sum = 0.0
    up_count = 0
    down_count = 0
    flat_count = 0

    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snapshots.get(code) or {}
        if not snap:
            continue
        snapshot_count += 1
        score = _float_or_none(snap.get("score"))
        if score is not None:
            scored_count += 1
            score_sum += score
        pct = _float_or_none(snap.get("pct"))
        if pct is None:
            flat_count += 1
        elif pct > 0:
            up_count += 1
        elif pct < 0:
            down_count += 1
        else:
            flat_count += 1

    avg_score = (score_sum / scored_count) if scored_count else None
    alerts = compute_watch_alerts(
        watchlist,
        snapshots,
        pct_up=pct_up,
        pct_down=pct_down,
        score_low=score_low,
        score_high=score_high,
    )

    return DashboardStats(
        watch_count=watch_count,
        snapshot_count=snapshot_count,
        scored_count=scored_count,
        avg_score=avg_score,
        up_count=up_count,
        down_count=down_count,
        flat_count=flat_count,
        alert_count=len(alerts),
    )
