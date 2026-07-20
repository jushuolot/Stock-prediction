"""板块龙头对标（P76）：自选同板块内按评分/涨跌幅标龙头，展示与龙头差距。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.sector_heatmap import UNKNOWN_SECTOR, extract_sector_label

_SCORE_GAP_STRONG = 3.0
_PCT_GAP_STRONG = 1.0


@dataclass(frozen=True)
class SectorLeaderRow:
    code: str
    name: str
    sector: str
    ticker_pct: float | None
    ticker_score: float | None
    leader_code: str
    leader_name: str
    leader_pct: float | None
    leader_score: float | None
    gap_pct: float | None
    gap_score: float | None
    is_leader: bool
    label: str
    fool_conclusion: str


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _leader_key(pct: float | None, score: float | None) -> tuple[float, float, str]:
    s = score if score is not None else -1e9
    p = pct if pct is not None else -1e9
    return (s, p, "")


def _leader_label(
    *,
    is_leader: bool,
    gap_pct: float | None,
    gap_score: float | None,
    sector: str,
    peer_count: int,
) -> tuple[str, str]:
    if sector == UNKNOWN_SECTOR:
        return "板块未知", "暂无板块信息，请先刷新摘要或完成一键分析。"
    if peer_count <= 1:
        return "板块仅本只", "自选里同板块只有这一只，暂无可对标龙头。"
    if is_leader:
        return "👑 板块龙头", "同板块自选内评分/涨跌幅综合领先，可作对标基准。"
    behind_score = gap_score is not None and gap_score <= -_SCORE_GAP_STRONG
    behind_pct = gap_pct is not None and gap_pct <= -_PCT_GAP_STRONG
    if behind_score or behind_pct:
        return "落后龙头", "相对板块龙头，评分或涨跌幅至少一项明显偏弱。"
    ahead_score = gap_score is not None and gap_score >= _SCORE_GAP_STRONG
    ahead_pct = gap_pct is not None and gap_pct >= _PCT_GAP_STRONG
    if ahead_score or ahead_pct:
        return "挑战龙头", "部分指标已接近或超过当前龙头，可关注能否持续。"
    return "紧跟龙头", "与板块龙头差距不大，整体处于同板块中上游。"


def compute_sector_leaders(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    *,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> list[SectorLeaderRow]:
    """逐标的对标同板块龙头（评分优先、涨跌幅次之）。"""
    peers: dict[str, list[tuple[str, str, float | None, float | None]]] = {}
    meta: dict[str, tuple[str, str, str, float | None, float | None]] = {}

    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        name = str(item.get("名称") or code)
        snap = snapshots.get(code) or {}
        brief = brief_for_code(code) if brief_for_code else None
        sector = extract_sector_label(snap, brief_md=brief)
        pct = _float_or_none(snap.get("pct"))
        score = _float_or_none(snap.get("score"))
        meta[code] = (name, sector, code, pct, score)
        peers.setdefault(sector, []).append((code, name, pct, score))

    leaders: dict[str, tuple[str, str, float | None, float | None]] = {}
    for sector, group in peers.items():
        best = max(group, key=lambda g: _leader_key(g[2], g[3]))
        leaders[sector] = best

    rows: list[SectorLeaderRow] = []
    for code, (name, sector, _, pct, score) in meta.items():
        leader_code, leader_name, leader_pct, leader_score = leaders[sector]
        peer_count = len(peers.get(sector) or [])
        is_leader = code == leader_code and peer_count > 1
        gap_pct = (
            round(pct - leader_pct, 2)
            if pct is not None and leader_pct is not None
            else None
        )
        gap_score = (
            round(score - leader_score, 1)
            if score is not None and leader_score is not None
            else None
        )
        label, fool = _leader_label(
            is_leader=is_leader,
            gap_pct=gap_pct,
            gap_score=gap_score,
            sector=sector,
            peer_count=peer_count,
        )
        rows.append(
            SectorLeaderRow(
                code=code,
                name=name,
                sector=sector,
                ticker_pct=pct,
                ticker_score=score,
                leader_code=leader_code,
                leader_name=leader_name,
                leader_pct=leader_pct,
                leader_score=leader_score,
                gap_pct=gap_pct,
                gap_score=gap_score,
                is_leader=is_leader,
                label=label,
                fool_conclusion=fool,
            )
        )
    rows.sort(key=lambda r: (not r.is_leader, r.label == "板块未知", r.sector, r.name))
    return rows


def sector_leader_table_rows(rows: list[SectorLeaderRow]) -> list[dict[str, Any]]:
    """UI 表格：龙头标签 + 与龙头差距。"""
    table: list[dict[str, Any]] = []
    for r in rows:
        table.append(
            {
                "名称": r.name,
                "代码": r.code,
                "板块": r.sector,
                "结论": r.label,
                "傻瓜结论": r.fool_conclusion,
                "涨跌幅%": r.ticker_pct,
                "评分": r.ticker_score,
                "龙头": r.leader_name if not r.is_leader or r.sector != UNKNOWN_SECTOR else "—",
                "龙头代码": r.leader_code if peer_visible(r) else "—",
                "龙头涨跌幅%": r.leader_pct if peer_visible(r) else None,
                "龙头评分": r.leader_score if peer_visible(r) else None,
                "距龙头%": r.gap_pct,
                "距龙头分": r.gap_score,
            }
        )
    return table


def peer_visible(row: SectorLeaderRow) -> bool:
    return row.sector != UNKNOWN_SECTOR and row.label != "板块仅本只"


def sector_leader_for_ticker(
    rows: list[SectorLeaderRow],
    code: str,
) -> SectorLeaderRow | None:
    target = str(code or "").strip()
    for r in rows:
        if r.code == target:
            return r
    return None
