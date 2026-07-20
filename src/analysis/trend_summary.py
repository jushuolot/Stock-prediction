"""分析历史趋势（P20）：从 query_log + snapshots 提取评分/涨跌幅走势。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TrendPoint:
    at: str
    label: str
    kind: str
    pct: float | None
    score: float | None


def _entry_mentions_ticker(entry: dict[str, Any], ticker: str) -> bool:
    code = str(ticker or "").strip()
    if not code:
        return False
    stocks = str(entry.get("stocks") or "")
    if code in {s.strip() for s in stocks.split(",") if s.strip()}:
        return True
    hay = str(entry.get("label") or "") + str(entry.get("conclusions_summary") or "")
    if code in hay:
        return True
    if re.search(rf"[（(]{re.escape(code)}[）)]", hay):
        return True
    return False


def _snap_for_entry(snapshots: list[dict[str, Any]], entry_id: str) -> dict[str, Any] | None:
    for s in snapshots:
        if str(s.get("id")) == str(entry_id):
            return s
    return None


def _metrics_from_snapshot(snap: dict[str, Any] | None, ticker: str) -> tuple[float | None, float | None]:
    if not snap:
        return None, None
    state = snap.get("state") or snap
    ws = state.get("watch_snapshots") or {}
    row = ws.get(ticker) or {}
    pct = row.get("pct")
    score = row.get("score")
    try:
        pct_f = float(pct) if pct is not None else None
    except (TypeError, ValueError):
        pct_f = None
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None
    return pct_f, score_f


def collect_trend_points(
    query_log: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    ticker: str,
    *,
    limit: int = 8,
) -> list[TrendPoint]:
    """最近 N 次涉及该标的的分析（时间从新到旧）。"""
    code = str(ticker or "").strip()
    if not code:
        return []
    points: list[TrendPoint] = []
    for entry in query_log:
        if not _entry_mentions_ticker(entry, code):
            continue
        snap = _snap_for_entry(snapshots, str(entry.get("id") or ""))
        pct, score = _metrics_from_snapshot(snap, code)
        if pct is None and score is None:
            continue
        points.append(
            TrendPoint(
                at=str(entry.get("at") or ""),
                label=str(entry.get("label") or ""),
                kind=str(entry.get("kind") or ""),
                pct=pct,
                score=score,
            )
        )
        if len(points) >= limit:
            break
    return points


def trend_delta(points: list[TrendPoint]) -> tuple[float | None, float | None]:
    """最新 vs 最早：score_delta, pct_delta（points 为新→旧）。"""
    if len(points) < 2:
        return None, None
    newest, oldest = points[0], points[-1]
    score_d = None
    pct_d = None
    if newest.score is not None and oldest.score is not None:
        score_d = newest.score - oldest.score
    if newest.pct is not None and oldest.pct is not None:
        pct_d = newest.pct - oldest.pct
    return score_d, pct_d


def format_trend_markdown(points: list[TrendPoint], *, ticker: str = "") -> str:
    title = f"# {ticker} 分析趋势" if ticker else "# 分析趋势"
    if not points:
        return f"{title}\n\n暂无足够历史快照（需完成一键分析或刷新摘要后才会记录）。\n"
    lines = [title, "", "| 时间 | 类型 | 涨跌幅% | 评分 | 说明 |", "| --- | --- | --- | --- | --- |"]
    for p in points:
        pct_s = f"{p.pct:+.2f}" if p.pct is not None else "—"
        score_s = f"{p.score:.1f}" if p.score is not None else "—"
        lines.append(f"| {p.at} | {p.kind} | {pct_s} | {score_s} | {p.label[:40]} |")
    score_d, pct_d = trend_delta(points)
    if score_d is not None or pct_d is not None:
        parts: list[str] = []
        if pct_d is not None:
            parts.append(f"涨跌幅变化 {pct_d:+.2f} 个百分点")
        if score_d is not None:
            parts.append(f"评分变化 {score_d:+.1f} 分")
        lines.extend(["", "**区间变化（最新 vs 最早）**：" + " · ".join(parts)])
    return "\n".join(lines) + "\n"
