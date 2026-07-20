"""用户主题偏好（P24）：深色/浅色 CSS 覆盖。"""

from __future__ import annotations

import streamlit as st

_LIGHT_CSS = """
<style>
[data-testid="stAppViewContainer"] {
  background-color: #fafafa !important;
  color: #1a1a1a !important;
}
[data-testid="stSidebar"] {
  background-color: #f0f0f0 !important;
}
.block-container { color: #1a1a1a !important; }
</style>
"""


def inject_theme_styles() -> None:
    dark = st.session_state.get("dark_mode", True)
    if not dark:
        st.markdown(_LIGHT_CSS, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """侧边栏深色模式开关（偏好写入 user_prefs）。"""
    from src.storage.history_store import mark_dirty

    cur = bool(st.session_state.get("dark_mode", True))
    new = st.toggle("深色模式", value=cur, help="关闭后使用浅色背景（偏好会保存）")
    if new != cur:
        st.session_state.dark_mode = new
        mark_dirty()
