"""快捷键 / URL 提示（P41）。"""

from __future__ import annotations

import streamlit as st

from src.util.i18n_strings import get_locale, t

_HINTS: list[tuple[str, dict[str, str]]] = [
    ("?tab=watch", {"zh": "打开自选分析", "en": "Open watchlist tab"}),
    ("?tab=search", {"zh": "打开发现标的", "en": "Open discover tab"}),
    ("?tab=markets", {"zh": "打开市场一览", "en": "Open markets tab"}),
    ("?tab=history", {"zh": "打开历史记录", "en": "Open history tab"}),
    ("?readonly=1", {"zh": "只读模式（隐藏编辑）", "en": "Read-only mode (no edits)"}),
]


def format_keyboard_hints(*, locale: str | None = None) -> str:
    loc = locale or get_locale()
    title = "链接提示" if loc == "zh" else "URL hints"
    parts = [f"**{title}**"]
    for param, labels in _HINTS:
        desc = labels.get(loc) or labels["zh"]
        parts.append(f"`{param}` — {desc}")
    return " · ".join(parts)


def render_keyboard_hints() -> None:
    st.caption(format_keyboard_hints())
