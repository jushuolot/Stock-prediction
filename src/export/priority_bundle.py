"""合并导出包（P86）：作战清单 + 速览 + 优先标的一页纸。"""

from __future__ import annotations

import io
import zipfile
from typing import Any, Callable

from src.analysis.battle_plan import build_battle_plan
from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.institutional_onepager import build_institutional_onepager
from src.analysis.priority_queue import PriorityRank, rank_watchlist_priority
from src.analysis.sector_relative import compute_sector_relative, sector_relative_for_ticker
from src.analysis.trend_summary import TrendPoint, collect_trend_points
from src.analysis.watch_alerts import WatchAlert, compute_watch_alerts
from src.util.query_time import format_query_datetime


def _alerts_for_code(alerts: list[WatchAlert], code: str) -> list[WatchAlert]:
    target = str(code or "").strip()
    return [a for a in alerts if a.code == target]


def _bundle_filenames(code: str) -> dict[str, str]:
    safe = str(code or "top").strip() or "top"
    return {
        "battle": "今日作战清单.md",
        "digest": "自选股速览.md",
        "onepager": f"一页纸_{safe}.md",
        "combined": f"合并导出_{safe}.md",
        "zip": f"合并导出_{safe}.zip",
    }


def build_priority_export_bundle_md(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    priority: PriorityRank | None = None,
    ranks: list[PriorityRank] | None = None,
    query_label: str = "",
    alerts: list[WatchAlert] | None = None,
    watch_notes: dict[str, str] | None = None,
    query_log: list[dict[str, Any]] | None = None,
    history_snapshots: list[dict[str, Any]] | None = None,
    brief_for_code: Callable[[str], str | None] | None = None,
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
    price_targets: dict[str, dict[str, float | None]] | None = None,
    stale_hours: float = 24.0,
) -> str:
    """单 Markdown 合并包：作战清单 + 速览 + 优先标的一页纸。"""
    now = query_label or format_query_datetime()
    if ranks is None:
        ranks = rank_watchlist_priority(
            watchlist,
            snapshots,
            alerts=alerts,
            stale_hours=stale_hours,
            brief_for_code=brief_for_code,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
            price_targets=price_targets,
        )
    if priority is None:
        priority = ranks[0] if ranks else None
    if alerts is None:
        alerts = compute_watch_alerts(
            watchlist,
            snapshots,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
            price_targets=price_targets,
        )
    battle = build_battle_plan(
        watchlist,
        snapshots,
        alerts=alerts,
        query_label=now,
        pct_up=pct_up,
        pct_down=pct_down,
        score_low=score_low,
        score_high=score_high,
        price_targets=price_targets,
    )
    digest = build_watchlist_digest(
        watchlist,
        snapshots,
        query_label=now,
        alerts=alerts,
        watch_notes=watch_notes,
    )
    onepager = ""
    if priority:
        rel_rows = compute_sector_relative(
            watchlist,
            snapshots,
            brief_for_code=brief_for_code,
        )
        rel = sector_relative_for_ticker(rel_rows, priority.code)
        snap = snapshots.get(priority.code) or {}
        trend: list[TrendPoint] = []
        if query_log is not None and history_snapshots is not None:
            trend = collect_trend_points(query_log, history_snapshots, priority.code, limit=6)
        onepager = build_institutional_onepager(
            name=priority.name,
            code=priority.code,
            snap=snap,
            sector_relative=rel,
            trend_points=trend,
            alerts=_alerts_for_code(alerts, priority.code),
            query_label=now,
        )
    parts = [
        battle.rstrip(),
        "",
        "---",
        "",
        digest.rstrip(),
    ]
    if onepager.strip():
        parts.extend(["", "---", "", onepager.rstrip()])
    parts.extend(
        [
            "",
            "---",
            "",
            f"> 合并导出 · 优先标的：{priority.name if priority else '—'}（{priority.code if priority else '—'}）",
            "> 基于公开行情快照，**非投资建议**。",
            "",
        ]
    )
    return "\n".join(parts)


def build_priority_export_bundle_zip(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    priority: PriorityRank | None = None,
    ranks: list[PriorityRank] | None = None,
    query_label: str = "",
    alerts: list[WatchAlert] | None = None,
    watch_notes: dict[str, str] | None = None,
    query_log: list[dict[str, Any]] | None = None,
    history_snapshots: list[dict[str, Any]] | None = None,
    brief_for_code: Callable[[str], str | None] | None = None,
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
    price_targets: dict[str, dict[str, float | None]] | None = None,
    stale_hours: float = 24.0,
) -> tuple[bytes, str]:
    """Zip 包（3 个 md 文件），返回 (bytes, 建议文件名)。"""
    now = query_label or format_query_datetime()
    if ranks is None:
        ranks = rank_watchlist_priority(
            watchlist,
            snapshots,
            alerts=alerts,
            stale_hours=stale_hours,
            brief_for_code=brief_for_code,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
            price_targets=price_targets,
        )
    if priority is None:
        priority = ranks[0] if ranks else None
    code = priority.code if priority else "watchlist"
    names = _bundle_filenames(code)
    md = build_priority_export_bundle_md(
        watchlist,
        snapshots,
        priority=priority,
        ranks=ranks,
        query_label=now,
        alerts=alerts,
        watch_notes=watch_notes,
        query_log=query_log,
        history_snapshots=history_snapshots,
        brief_for_code=brief_for_code,
        pct_up=pct_up,
        pct_down=pct_down,
        score_low=score_low,
        score_high=score_high,
        price_targets=price_targets,
        stale_hours=stale_hours,
    )
    if alerts is None:
        alerts = compute_watch_alerts(
            watchlist,
            snapshots,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
            price_targets=price_targets,
        )
    battle = build_battle_plan(
        watchlist,
        snapshots,
        alerts=alerts,
        query_label=now,
        pct_up=pct_up,
        pct_down=pct_down,
        score_low=score_low,
        score_high=score_high,
        price_targets=price_targets,
    )
    digest = build_watchlist_digest(
        watchlist,
        snapshots,
        query_label=now,
        alerts=alerts,
        watch_notes=watch_notes,
    )
    onepager = ""
    if priority:
        rel_rows = compute_sector_relative(
            watchlist,
            snapshots,
            brief_for_code=brief_for_code,
        )
        rel = sector_relative_for_ticker(rel_rows, priority.code)
        snap = snapshots.get(priority.code) or {}
        trend: list[TrendPoint] = []
        if query_log is not None and history_snapshots is not None:
            trend = collect_trend_points(query_log, history_snapshots, priority.code, limit=6)
        onepager = build_institutional_onepager(
            name=priority.name,
            code=priority.code,
            snap=snap,
            sector_relative=rel,
            trend_points=trend,
            alerts=_alerts_for_code(alerts, priority.code),
            query_label=now,
        )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(names["battle"], battle.encode("utf-8"))
        zf.writestr(names["digest"], digest.encode("utf-8"))
        if onepager.strip():
            zf.writestr(names["onepager"], onepager.encode("utf-8"))
        zf.writestr(names["combined"], md.encode("utf-8"))
    return buf.getvalue(), names["zip"]
