"""会话恢复欢迎条（P53）：历史含自选时展示数量与上次刷新。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.health_panel import format_last_refresh_label


def build_welcome_message(session_state: dict[str, Any]) -> str:
    """欢迎文案：自选数量 + 上次摘要刷新时间。"""
    count = len(session_state.get("watchlist") or [])
    last = format_last_refresh_label(session_state)
    return f"欢迎回来！已恢复 **{count}** 只自选股 · 上次摘要刷新：**{last}**"


def should_show_welcome(session_state: dict[str, Any]) -> bool:
    """启动时历史已恢复自选则展示一次。"""
    if session_state.get("_welcome_banner_shown"):
        return False
    if not session_state.get("_restored_watchlist"):
        return False
    return bool(session_state.get("watchlist"))


def render_welcome_banner() -> None:
    ss = dict(st.session_state)
    if not should_show_welcome(ss):
        return
    st.success(build_welcome_message(ss))
    st.session_state["_welcome_banner_shown"] = True
