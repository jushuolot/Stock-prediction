"""相对板块强弱（P73）：对比自选标的 vs 同板块均涨跌幅/均评分（公开快照）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.sector_heatmap import UNKNOWN_SECTOR, aggregate_sector_distribution, extract_sector_label

_PCT_THRESHOLD = 0.25
_SCORE_THRESHOLD = 1.5


@dataclass(frozen=True)
class SectorRelativeRow:
    code: str
    name: str
    sector: str
    ticker_pct: float | None
    ticker_score: float | None
    sector_avg_pct: float | None
    sector_avg_score: float | None
    pct_vs_sector: float | None
    score_vs_sector: float | None
    label: str
    fool_conclusion: str


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _relative_label(
    pct_vs: float | None,
    score_vs: float | None,
    *,
    sector: str,
    peer_count: int,
) -> tuple[str, str]:
    if sector == UNKNOWN_SECTOR:
        return "板块未知", "暂无板块信息，请先刷新摘要或完成一键分析。"
    if peer_count <= 1:
        return "板块仅本只", "自选里同板块只有这一只，无法对比强弱。"
    wins = losses = 0
    if pct_vs is not None:
        if pct_vs > _PCT_THRESHOLD:
            wins += 1
        elif pct_vs < -_PCT_THRESHOLD:
            losses += 1
    if score_vs is not None:
        if score_vs > _SCORE_THRESHOLD:
            wins += 1
        elif score_vs < -_SCORE_THRESHOLD:
            losses += 1
    if wins == 0 and losses == 0:
        return "与板块相当", "涨跌幅与评分均接近同板块自选均值，暂无显著强弱。"
    if wins > losses:
        return "跑赢板块", "相对同板块自选，涨跌幅或评分至少一项明显更强。"
    if losses > wins:
        return "跑输板块", "相对同板块自选，涨跌幅或评分至少一项明显偏弱。"
    return "与板块相当", "涨跌与评分信号不一致，整体与板块均值接近。"


def compute_sector_relative(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    *,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> list[SectorRelativeRow]:
    """逐标的对比板块均涨跌幅/均评分（板块来自 sector_heatmap 同源逻辑）。"""
    buckets = aggregate_sector_distribution(
        watchlist,
        snapshots,
        brief_for_code=brief_for_code,
    )
    by_sector = {b.sector: b for b in buckets}
    rows: list[SectorRelativeRow] = []
    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        name = str(item.get("名称") or code)
        snap = snapshots.get(code) or {}
        brief = brief_for_code(code) if brief_for_code else None
        sector = extract_sector_label(snap, brief_md=brief)
        bucket = by_sector.get(sector)
        ticker_pct = _float_or_none(snap.get("pct"))
        ticker_score = _float_or_none(snap.get("score"))
        sector_avg_pct = bucket.avg_pct if bucket else None
        sector_avg_score = bucket.avg_score if bucket else None
        peer_count = bucket.count if bucket else 0
        pct_vs = (
            round(ticker_pct - sector_avg_pct, 2)
            if ticker_pct is not None and sector_avg_pct is not None
            else None
        )
        score_vs = (
            round(ticker_score - sector_avg_score, 1)
            if ticker_score is not None and sector_avg_score is not None
            else None
        )
        label, fool = _relative_label(pct_vs, score_vs, sector=sector, peer_count=peer_count)
        rows.append(
            SectorRelativeRow(
                code=code,
                name=name,
                sector=sector,
                ticker_pct=ticker_pct,
                ticker_score=ticker_score,
                sector_avg_pct=sector_avg_pct,
                sector_avg_score=sector_avg_score,
                pct_vs_sector=pct_vs,
                score_vs_sector=score_vs,
                label=label,
                fool_conclusion=fool,
            )
        )
    rows.sort(key=lambda r: (r.label != "跑赢板块", r.label == "板块未知", r.name))
    return rows


def sector_relative_table_rows(rows: list[SectorRelativeRow]) -> list[dict[str, Any]]:
    """UI 表格：傻瓜结论 + 相对板块标签。"""
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
                "板块均%": r.sector_avg_pct,
                "相对板块%": r.pct_vs_sector,
                "评分": r.ticker_score,
                "板块均分": r.sector_avg_score,
                "相对板块分": r.score_vs_sector,
            }
        )
    return table


def sector_relative_for_ticker(
    rows: list[SectorRelativeRow],
    code: str,
) -> SectorRelativeRow | None:
    target = str(code or "").strip()
    for r in rows:
        if r.code == target:
            return r
    return None
