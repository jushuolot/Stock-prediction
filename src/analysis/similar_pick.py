"""相似股推荐 lite（P52）：同板块自选快照内按评分推荐 1–3 只。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.sector_heatmap import UNKNOWN_SECTOR, extract_sector_label


@dataclass(frozen=True)
class SimilarPick:
    code: str
    name: str
    sector: str
    score: float | None
    pct: float | None
    anchor_code: str
    anchor_name: str
    reason: str


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def suggest_similar_picks(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    *,
    max_picks: int = 3,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> list[SimilarPick]:
    """从自选板块与快照评分中推荐同板块标的（仅 watch_snapshots，无外部 API）。"""
    limit = max(1, min(int(max_picks), 3))
    names: dict[str, str] = {}
    by_sector: dict[str, list[tuple[str, str, float | None, float | None]]] = {}

    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        names[code] = str(item.get("名称") or code)
        snap = snapshots.get(code)
        if not snap:
            continue
        brief = brief_for_code(code) if brief_for_code else None
        sector = extract_sector_label(snap, brief_md=brief)
        if sector == UNKNOWN_SECTOR:
            continue
        by_sector.setdefault(sector, []).append(
            (code, names[code], _float_or_none(snap.get("score")), _float_or_none(snap.get("pct")))
        )

    candidates: list[SimilarPick] = []
    for sector, members in by_sector.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda m: (-(m[2] if m[2] is not None else -1.0), m[0]))
        anchor = members[0]
        for peer in members[1:]:
            candidates.append(
                SimilarPick(
                    code=peer[0],
                    name=peer[1],
                    sector=sector,
                    score=peer[2],
                    pct=peer[3],
                    anchor_code=anchor[0],
                    anchor_name=anchor[1],
                    reason=f"与 {anchor[1]}({anchor[0]}) 同属{sector}",
                )
            )

    candidates.sort(key=lambda p: (-(p.score if p.score is not None else -1.0), p.code))
    return candidates[:limit]


def similar_pick_rows(picks: list[SimilarPick]) -> list[dict[str, Any]]:
    """表格行：代码、名称、板块、评分、涨跌幅、说明。"""
    rows: list[dict[str, Any]] = []
    for p in picks:
        rows.append(
            {
                "代码": p.code,
                "名称": p.name,
                "板块": p.sector,
                "评分": f"{p.score:.1f}" if p.score is not None else "—",
                "涨跌幅%": f"{p.pct:+.2f}" if p.pct is not None else "—",
                "说明": p.reason,
            }
        )
    return rows
