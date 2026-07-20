"""多标的作战优先级（P85）：提醒 + 风险旗标 + 相对板块综合排序。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.risk_radar import compute_risk_radar
from src.analysis.sector_relative import (
    SectorRelativeRow,
    compute_sector_relative,
    sector_relative_for_ticker,
)
from src.analysis.watch_alerts import WatchAlert, compute_watch_alerts

_ALERT_WEIGHT = {"hot": 30, "warn": 20, "info": 10}
_RISK_FLAG_POINTS = 15
_SECTOR_POINTS = {"跑输板块": 18, "与板块相当": 4, "板块仅本只": 2, "板块未知": 0, "跑赢板块": 0}


@dataclass(frozen=True)
class PriorityRank:
    code: str
    name: str
    score: float
    reason: str


def _alert_points(alerts: list[WatchAlert]) -> dict[str, tuple[int, list[str]]]:
    by_code: dict[str, tuple[int, list[str]]] = defaultdict(lambda: (0, []))
    for alert in alerts:
        pts, msgs = by_code[alert.code]
        w = _ALERT_WEIGHT.get(alert.level, 5)
        pts += w
        msgs = list(msgs)
        msgs.append(alert.message)
        by_code[alert.code] = (pts, msgs)
    return dict(by_code)


def _risk_points(
    snap: dict[str, Any],
    sector_relative: SectorRelativeRow | None,
    *,
    stale_hours: float,
) -> tuple[int, list[str]]:
    flags = compute_risk_radar(snap, sector_relative=sector_relative, stale_hours=stale_hours)
    triggered = [f for f in flags if f.triggered]
    pts = len(triggered) * _RISK_FLAG_POINTS
    msgs = [f"{f.kind}：{f.message}" for f in triggered[:2]]
    return pts, msgs


def _sector_points(rel: SectorRelativeRow | None) -> tuple[int, str]:
    if rel is None:
        return 0, ""
    pts = _SECTOR_POINTS.get(rel.label, 0)
    if rel.label == "跑输板块":
        return pts, "相对板块偏弱"
    if rel.label == "跑赢板块":
        return pts, "相对板块偏强"
    if rel.label == "与板块相当":
        return pts, "与板块相当"
    return pts, rel.label


def rank_watchlist_priority(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    alerts: list[WatchAlert] | None = None,
    stale_hours: float = 24.0,
    brief_for_code: Callable[[str], str | None] | None = None,
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
    price_targets: dict[str, dict[str, float | None]] | None = None,
    top_n: int = 5,
) -> list[PriorityRank]:
    """按提醒、风险旗标、跑输板块综合打分，返回 Top N 及傻瓜理由。"""
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
    alert_map = _alert_points(alerts)
    rel_rows = compute_sector_relative(
        watchlist,
        snapshots,
        brief_for_code=brief_for_code,
    )
    ranked: list[PriorityRank] = []
    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        name = str(item.get("名称") or code)
        snap = snapshots.get(code) or {}
        rel = sector_relative_for_ticker(rel_rows, code)
        a_pts, a_msgs = alert_map.get(code, (0, []))
        r_pts, r_msgs = _risk_points(snap, rel, stale_hours=stale_hours)
        s_pts, s_label = _sector_points(rel)
        total = float(a_pts + r_pts + s_pts)
        parts: list[str] = []
        if a_msgs:
            parts.append(f"提醒 {len(a_msgs)} 条（{a_msgs[0]}）")
        elif alerts:
            parts.append("暂无阈值提醒")
        if r_msgs:
            parts.append(f"风险 {len(r_msgs)} 项（{r_msgs[0]}）")
        if s_label:
            parts.append(s_label)
        if not parts:
            parts.append("暂无显著信号，可按计划复查")
        reason = "；".join(parts[:3])
        ranked.append(PriorityRank(code=code, name=name, score=total, reason=reason))
    ranked.sort(key=lambda r: (-r.score, r.code))
    with_signal = [r for r in ranked if r.score > 0]
    pool = with_signal if with_signal else ranked
    return pool[: max(0, top_n)]


def priority_table_rows(ranks: list[PriorityRank]) -> list[dict[str, Any]]:
    """UI 表格行。"""
    out: list[dict[str, Any]] = []
    for i, r in enumerate(ranks, start=1):
        out.append(
            {
                "优先序": i,
                "名称": r.name,
                "代码": r.code,
                "优先分": f"{r.score:.0f}",
                "关注理由": r.reason,
            }
        )
    return out


def format_priority_section(ranks: list[PriorityRank]) -> str:
    """Markdown 段落，供 expander 展示。"""
    if not ranks:
        return "暂无自选股或摘要，请先刷新全部摘要。"
    lines = ["**今日建议优先关注（Top 5）**", ""]
    for i, r in enumerate(ranks, start=1):
        lines.append(f"{i}. **{r.name}（{r.code}）** — {r.reason}")
    lines.append("")
    lines.append("排序依据：阈值提醒 > 风险旗标 > 跑输板块（公开快照，非投资建议）。")
    return "\n".join(lines)


def format_priority_digest_section(
    ranks: list[PriorityRank],
    *,
    top_n: int = 3,
) -> str:
    """Markdown 段落，供 digest/webhook 推送 Top 3（P88）。"""
    if not ranks:
        return ""
    top = ranks[: max(0, top_n)]
    if not top:
        return ""
    lines = ["## 今日优先关注 Top 3", ""]
    for i, r in enumerate(top, start=1):
        lines.append(f"{i}. **{r.name}（{r.code}）** — {r.reason}")
    lines.append("")
    lines.append("排序依据：阈值提醒 > 风险旗标 > 跑输板块（公开快照，非投资建议）。")
    lines.append("")
    return "\n".join(lines)
