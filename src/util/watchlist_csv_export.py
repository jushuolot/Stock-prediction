"""自选表 CSV 导出（P67）：code, name, score, pct, note, group。"""

from __future__ import annotations

import csv
import io
from typing import Any

from src.util.watch_groups import groups_for_ticker, normalize_watch_groups
from src.util.watch_notes import get_note, normalize_watch_notes

CSV_FIELDNAMES = ("code", "name", "score", "pct", "note", "group")


def watchlist_table_csv_rows(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any] | None = None,
    *,
    watch_notes: dict[str, str] | None = None,
    watch_groups: dict[str, list[str]] | None = None,
) -> list[dict[str, str]]:
    snaps = snapshots or {}
    notes = normalize_watch_notes(watch_notes or {})
    groups = normalize_watch_groups(watch_groups or {})
    rows: list[dict[str, str]] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snaps.get(code) or {}
        pct = snap.get("pct")
        score = snap.get("score")
        grp = groups_for_ticker(groups, code)
        rows.append(
            {
                "code": code,
                "name": str(item.get("名称") or ""),
                "score": f"{float(score):.1f}" if score is not None else "",
                "pct": f"{float(pct):+.2f}" if pct is not None else "",
                "note": get_note(notes, code),
                "group": ",".join(grp),
            }
        )
    return rows


def watchlist_table_to_csv_bytes(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any] | None = None,
    *,
    watch_notes: dict[str, str] | None = None,
    watch_groups: dict[str, list[str]] | None = None,
) -> bytes:
    rows = watchlist_table_csv_rows(
        watchlist,
        snapshots,
        watch_notes=watch_notes,
        watch_groups=watch_groups,
    )
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(CSV_FIELDNAMES))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")
