"""自选股导出工具（P10）。"""

from __future__ import annotations

import csv
import io
from typing import Any

from src.util.watch_notes import get_note, normalize_watch_notes


def watchlist_to_csv_rows(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any] | None = None,
    watch_notes: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    snaps = snapshots or {}
    notes = normalize_watch_notes(watch_notes or {})
    rows: list[dict[str, str]] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snaps.get(code) or {}
        pct = snap.get("pct")
        score = snap.get("score")
        rows.append(
            {
                "名称": str(item.get("名称") or ""),
                "代码": code,
                "涨跌幅%": f"{float(pct):+.2f}" if pct is not None else "",
                "评分": f"{float(score):.1f}" if score is not None else "",
                "一句话": str(snap.get("one_line") or ""),
                "笔记": get_note(notes, code),
                "货币": str(item.get("货币") or ""),
                "类型": str(item.get("类型") or ""),
                "市场": str(item.get("市场") or ""),
            }
        )
    return rows


def watchlist_to_csv_bytes(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any] | None = None,
    watch_notes: dict[str, str] | None = None,
) -> bytes:
    rows = watchlist_to_csv_rows(watchlist, snapshots, watch_notes=watch_notes)
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def sort_watchlist(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    by: str = "代码",
    descending: bool = False,
) -> list[dict[str, Any]]:
    wl = list(watchlist)

    def key_fn(item: dict[str, Any]) -> tuple:
        code = str(item.get("代码") or "")
        snap = snapshots.get(code) or {}
        if by == "涨跌幅":
            v = snap.get("pct")
            try:
                return (0, float(v) if v is not None else -1e9)
            except (TypeError, ValueError):
                return (0, -1e9)
        if by == "评分":
            v = snap.get("score")
            try:
                return (0, float(v) if v is not None else -1e9)
            except (TypeError, ValueError):
                return (0, -1e9)
        return (1, str(item.get(by) or code))

    return sorted(wl, key=key_fn, reverse=descending)


def filter_watchlist(watchlist: list[dict[str, Any]], keyword: str) -> list[dict[str, Any]]:
    kw = (keyword or "").strip().lower()
    if not kw:
        return list(watchlist)
    out: list[dict[str, Any]] = []
    for item in watchlist:
        hay = " ".join(
            str(item.get(k) or "") for k in ("名称", "代码", "市场", "类型")
        ).lower()
        if kw in hay:
            out.append(item)
    return out
