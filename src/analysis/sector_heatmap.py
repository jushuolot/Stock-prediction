"""板块热力图 lite（P25）：按行业/板块聚合自选股快照。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


UNKNOWN_SECTOR = "未知"


@dataclass(frozen=True)
class SectorBucket:
    sector: str
    count: int
    avg_pct: float | None
    avg_score: float | None
    tickers: tuple[str, ...]


def _sector_from_fin_summary(fin: str) -> str | None:
    text = str(fin or "").strip()
    if not text:
        return None
    first = text.split(" · ")[0].strip()
    if first and first not in ("—", "行业"):
        return first
    return None


def _sector_from_brief(brief_md: str) -> str | None:
    text = str(brief_md or "")
    if not text:
        return None
    m = re.search(r"## 财务对比摘要[^\n]*\n\n([^\n]+)", text)
    if not m:
        return None
    line = m.group(1).strip()
    if not line or line in ("—", "行业"):
        return None
    return line.split(" · ")[0].strip() or None


def extract_sector_label(
    snap: dict[str, Any] | None,
    *,
    brief_md: str | None = None,
) -> str:
    """从快照 sector/industry 或 fin_summary / 简报中提取板块名。"""
    snap = snap or {}
    for key in ("sector", "industry", "板块", "行业"):
        raw = snap.get(key)
        if raw is None:
            continue
        label = str(raw).strip()
        if label and label not in ("—", "行业"):
            return label
    from_fin = _sector_from_fin_summary(str(snap.get("fin_summary") or ""))
    if from_fin:
        return from_fin
    from_brief = _sector_from_brief(brief_md or "")
    if from_brief:
        return from_brief
    return UNKNOWN_SECTOR


def aggregate_sector_distribution(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, dict[str, Any]],
    *,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> list[SectorBucket]:
    """按板块聚合自选数量、均涨跌幅与均评分。"""
    buckets: dict[str, dict[str, Any]] = {}
    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        snap = snapshots.get(code) or {}
        brief = brief_for_code(code) if brief_for_code else None
        sector = extract_sector_label(snap, brief_md=brief)
        row = buckets.setdefault(
            sector,
            {"count": 0, "pct_sum": 0.0, "pct_n": 0, "score_sum": 0.0, "score_n": 0, "tickers": []},
        )
        row["count"] += 1
        row["tickers"].append(code)
        pct = snap.get("pct")
        if pct is not None:
            try:
                row["pct_sum"] += float(pct)
                row["pct_n"] += 1
            except (TypeError, ValueError):
                pass
        score = snap.get("score")
        if score is not None:
            try:
                row["score_sum"] += float(score)
                row["score_n"] += 1
            except (TypeError, ValueError):
                pass

    out: list[SectorBucket] = []
    for sector, row in buckets.items():
        avg_pct = round(row["pct_sum"] / row["pct_n"], 2) if row["pct_n"] else None
        avg_score = round(row["score_sum"] / row["score_n"], 1) if row["score_n"] else None
        out.append(
            SectorBucket(
                sector=sector,
                count=int(row["count"]),
                avg_pct=avg_pct,
                avg_score=avg_score,
                tickers=tuple(row["tickers"]),
            )
        )
    out.sort(key=lambda b: (-b.count, b.sector))
    return out


def sector_distribution_rows(buckets: list[SectorBucket]) -> list[dict[str, Any]]:
    """表格行：板块、数量、均涨跌幅、均评分、标的。"""
    rows: list[dict[str, Any]] = []
    for b in buckets:
        rows.append(
            {
                "板块": b.sector,
                "数量": b.count,
                "均涨跌幅%": f"{b.avg_pct:+.2f}" if b.avg_pct is not None else "—",
                "均评分": f"{b.avg_score:.1f}" if b.avg_score is not None else "—",
                "标的": "、".join(b.tickers),
            }
        )
    return rows


def sector_bar_values(buckets: list[SectorBucket]) -> tuple[list[str], list[int]]:
    """条形图：板块名与数量（按数量降序）。"""
    labels = [b.sector for b in buckets]
    counts = [b.count for b in buckets]
    return labels, counts
