"""评分与涨跌幅展示徽章（P15）。"""

from __future__ import annotations

from typing import Any


def pct_badge(pct: Any) -> str:
    if pct is None:
        return "—"
    try:
        p = float(pct)
    except (TypeError, ValueError):
        return "—"
    if p >= 5:
        return f"🔺 {p:+.2f}%"
    if p <= -5:
        return f"🔻 {p:+.2f}%"
    if p > 0:
        return f"↑ {p:+.2f}%"
    if p < 0:
        return f"↓ {p:+.2f}%"
    return f"{p:+.2f}%"


def score_badge(score: Any) -> str:
    if score is None:
        return "—"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "—"
    if s >= 65:
        return f"🟢 {s:.1f}"
    if s <= 40:
        return f"🔴 {s:.1f}"
    return f"🟡 {s:.1f}"
