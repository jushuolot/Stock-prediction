"""快照 diff 后精选再分析：只对少数有意义标的跑轻量模型（P127）。"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from src.analysis.quick_analyze import analyze_watch_light

FetchFn = Callable[..., tuple[Any, str]]


def _row_item(code: str, name: str, universe: pd.DataFrame) -> dict[str, str]:
    if universe is not None and not universe.empty:
        c6 = str(code).zfill(6)
        for _, row in universe.iterrows():
            rc = str(row.get("代码") or "").replace(".0", "").strip()
            if rc == c6:
                return {
                    "代码": rc,
                    "名称": str(row.get("名称") or name),
                    "市场": "A股",
                }
    return {"代码": str(code).zfill(6), "名称": name, "市场": "A股"}


def select_followup_targets(
    diff: dict[str, Any] | None,
    *,
    max_items: int = 6,
) -> list[tuple[str, str, str]]:
    """返回 (code, name, tag) 值得再分析的列表。"""
    if not diff:
        return []
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for pc in diff.get("pick_checks") or []:
        if pc.get("hit") is not False:
            continue
        c = str(pc.get("code") or "").zfill(6)
        if len(c) != 6 or c in seen:
            continue
        seen.add(c)
        out.append((c, str(pc.get("name") or c), "预测未中·复盘"))
        if len(out) >= max_items:
            return out

    for m in diff.get("movers") or []:
        if len(out) >= max_items:
            break
        delta = float(m.get("delta_pct") or 0)
        if abs(delta) < 2.0:
            continue
        c = str(m.get("code") or "").zfill(6)
        if len(c) != 6 or c in seen:
            continue
        seen.add(c)
        out.append((c, str(m.get("name") or c), f"快照异动Δ{delta:+.1f}%"))

    return out[:max_items]


def build_deep_followups(
    diff: dict[str, Any] | None,
    universe: pd.DataFrame,
    fetch_fn: FetchFn,
    *,
    max_items: int = 6,
) -> list[dict[str, Any]]:
    """对精选标的跑轻量技术摘要（无质量/K线明日全量，省资源）。"""
    targets = select_followup_targets(diff, max_items=max_items)
    rows: list[dict[str, Any]] = []
    for code, name, tag in targets:
        item = _row_item(code, name, universe)
        try:
            snap = analyze_watch_light(item, fetch_fn, days=60)
            score = snap.score
            verdict = "值得再看"
            if score is not None and score < 55:
                verdict = "偏弱观望"
            elif score is not None and score >= 72:
                verdict = "偏强关注"
            rows.append(
                {
                    "code": code,
                    "name": item["名称"],
                    "tag": tag,
                    "score": score,
                    "pct": snap.pct,
                    "one_line": snap.one_line,
                    "verdict": verdict,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "code": code,
                    "name": name,
                    "tag": tag,
                    "score": None,
                    "pct": None,
                    "one_line": f"轻量分析失败：{exc}"[:48],
                    "verdict": "待查",
                }
            )
    return rows
