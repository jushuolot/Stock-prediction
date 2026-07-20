"""Stock Assistant — 入口：登录、私人花园 / 专家模式。"""

from __future__ import annotations

import streamlit as st

from src.storage.history_store import load_into_session, persist_session
from src.ui import app_core as C
from src.ui.pages import garden, history, markets, search, watch
from src.ui.tab_router import apply_tab_from_query, render_main_tabs
from src.util.watch_expander_nav import apply_watch_expand_from_query
from src.util.i18n_strings import tab_label
from src.ui.workflow_sidebar import render_workflow_sidebar
from src.ui.mobile_style import inject_mobile_styles
from src.ui.theme_style import inject_theme_styles
from src.ui.footer import render_app_footer
from src.util.readonly_mode import apply_readonly_from_query, is_readonly_mode

st.set_page_config(
    page_title="私人选股花园",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="auto",
)
C._login_gate()
C._init_state()
load_into_session()
apply_readonly_from_query()
C._apply_pending_session_keys()
inject_mobile_styles()
inject_theme_styles()

if st.query_params.get("pro") == "1":
    st.session_state.ui_mode = "pro"
if st.query_params.get("garden") == "1":
    st.session_state.ui_mode = "garden"
st.session_state.setdefault("ui_mode", "garden")

expert = st.session_state.ui_mode == "pro"
render_workflow_sidebar()

if expert:
    st.title("Stock Assistant · 专家模式")
    st.caption(
        "**四步用法：** ② 发现标的 → ① 自选分析 → ③ 市场一览 → ④ 历史记录。"
        "想简单用时点侧边栏 **回到花园**。"
    )
    if is_readonly_mode():
        st.info("👁 **只读模式**：链接带 `?readonly=1`。")
    apply_tab_from_query()
    apply_watch_expand_from_query(st.session_state, st.query_params)
    render_main_tabs(
        {
            "watch": watch.render,
            "search": search.render,
            "markets": markets.render,
            "history": history.render,
        }
    )
else:
    garden.render()

if st.session_state.get("_history_dirty"):
    persist_session()

render_app_footer()
