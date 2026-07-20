"""主 Tab 路由与 ?tab= 深链接（P18）；P113 精简为四页。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from src.util.i18n_strings import TAB_IDS, get_locale, tab_label, tab_order

# 旧七页深链接 → 新四页（markets 子页 / watch）
_LEGACY_MARKET_TABS = frozenset({"movers", "plates", "panorama"})
_LEGACY_INSIGHT = "insight"

TAB_ORDER: list[tuple[str, str]] = [
    ("watch", "① 自选分析"),
    ("search", "② 发现标的"),
    ("markets", "③ 市场一览"),
    ("history", "④ 历史记录"),
]

_TAB_IDS = frozenset(TAB_IDS)


def _current_tab_order() -> list[tuple[str, str]]:
    return tab_order(locale=get_locale())


def _tab_labels() -> list[str]:
    return [label for _, label in _current_tab_order()]


def _tab_id_by_label() -> dict[str, str]:
    return {label: tid for tid, label in _current_tab_order()}

_TAB_ALIASES: dict[str, str] = {
    "watch": "watch",
    "search": "search",
    "markets": "markets",
    "history": "history",
    "movers": "movers",
    "plates": "plates",
    "panorama": "panorama",
    "insight": "insight",
    "1": "watch",
    "2": "search",
    "3": "markets",
    "4": "history",
    "工作台": "watch",
    "分析工作台": "watch",
    "自选分析": "watch",
    "搜索": "search",
    "搜索添加": "search",
    "发现标的": "search",
    "市场一览": "markets",
    "板块": "plates",
    "板块行情": "plates",
    "全球股市": "movers",
    "异动": "panorama",
    "异动全景": "panorama",
    "行动路线": "insight",
    "历史": "history",
    "历史记录": "history",
    "watchlist": "watch",
    "sectors": "plates",
    "global markets": "movers",
    "movers panorama": "panorama",
    "action route": "insight",
}
for tid in TAB_IDS:
    _TAB_ALIASES[tab_label(tid, locale="zh")] = tid
    _TAB_ALIASES[tab_label(tid, locale="en")] = tid


def resolve_tab_id(raw: str) -> str | None:
    key = (raw or "").strip()
    if not key:
        return None
    lower = key.lower()
    if lower in _TAB_ALIASES:
        return _TAB_ALIASES[lower]
    if key in _TAB_ALIASES:
        return _TAB_ALIASES[key]
    for tid, label in TAB_ORDER:
        if key in label or label in key:
            return tid
    for tid, label in tab_order():
        if key in label or label in key:
            return tid
    return None


def _apply_resolved_tab(resolved: str) -> None:
    if resolved in _LEGACY_MARKET_TABS:
        st.session_state.active_tab = "markets"
        st.session_state.markets_subtab = resolved
        return
    if resolved == _LEGACY_INSIGHT:
        st.session_state.active_tab = "watch"
        return
    if resolved in _TAB_IDS:
        st.session_state.active_tab = resolved


def apply_tab_from_query() -> str | None:
    """读取 ?tab= 并写入 session_state.active_tab。"""
    st.session_state.setdefault("active_tab", TAB_IDS[0])
    raw = st.query_params.get("tab", "")
    if not raw:
        return None
    resolved = resolve_tab_id(str(raw))
    if not resolved:
        return None
    _apply_resolved_tab(resolved)
    return str(st.session_state.active_tab)


def render_main_tabs(pages: dict[str, Callable[[], None]]) -> None:
    order = _current_tab_order()
    ids = [tid for tid, _ in order]
    labels = _tab_labels()
    id_by_label = _tab_id_by_label()
    current = str(st.session_state.get("active_tab") or ids[0])
    if current not in ids:
        current = ids[0]
    idx = ids.index(current)

    selected_label = st.radio(
        "主导航",
        options=labels,
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_id = id_by_label[selected_label]
    st.session_state.active_tab = selected_id

    render_fn = pages.get(selected_id)
    if render_fn:
        render_fn()
