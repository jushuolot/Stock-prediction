"""侧边栏：推荐使用路径。"""

from __future__ import annotations

import streamlit as st

from src.ui.changelog_panel import render_changelog_panel
from src.ui.capability_map import render_capability_map_sidebar
from src.ui.playbook_preview import render_playbook_preview_sidebar
from src.ui.health_panel import render_health_panel
from src.ui.push_panel import render_push_panel
from src.ui.readonly_export_panel import render_readonly_export_panel
from src.ui.share_panel import render_share_panel
from src.ui.theme_style import render_theme_toggle
from src.util.i18n_strings import render_locale_toggle
from src.ui.milestone_banner import EVOLUTION_100_PATH
from src.util.readonly_mode import is_readonly_mode
from src.storage.history_store import mark_dirty
from src.util.sidebar_state import (
    is_section_collapsed,
    normalize_sidebar_collapsed,
    set_section_collapsed,
)

def render_workflow_sidebar() -> None:
    simple = str(st.session_state.get("ui_mode", "garden")) != "pro"
    with st.sidebar:
        if simple:
            st.markdown("### 🌱 私人花园")
            st.caption("只有你知道密码。每晚来看成长日记即可。")
            if st.button("⚙️ 进入专家模式（四页精简版）", use_container_width=True):
                st.session_state.ui_mode = "pro"
                st.rerun()
            st.markdown(
                "[📖 如何部署你的私密空间](docs/PRIVATE_GARDEN.md) · "
                "[☁️ 零本地·全公网进化](docs/CLOUD_ONLY.md)"
            )
            render_theme_toggle()
            return

        if st.button("🌱 回到花园简版", use_container_width=True):
            st.session_state.ui_mode = "garden"
            st.rerun()

        collapsed_prefs = normalize_sidebar_collapsed(st.session_state.get("sidebar_collapsed"))
        workflow_collapsed = is_section_collapsed(collapsed_prefs, "workflow_phase")
        capability_collapsed = is_section_collapsed(collapsed_prefs, "capability_map")
        fold_pref = st.checkbox(
            "折叠快速上手",
            value=workflow_collapsed,
            key="sidebar_workflow_fold_pref",
        )
        if fold_pref != workflow_collapsed:
            st.session_state.sidebar_collapsed = set_section_collapsed(
                collapsed_prefs, "workflow_phase", fold_pref
            )
            mark_dirty()

        with st.expander("快速上手", expanded=not fold_pref):
            st.markdown(
                f"""
**① 发现标的** — 搜股票，点「加入自选」

**② 自选分析** — 选一只 → **一键分析** → 下载简报

**③ 市场一览** — 涨跌幅榜 / 板块 / 异动速览（一个页里三个子标签）

**④ 历史记录** — 查以前刷过的榜单和分析

---
*详细清单：[docs/EVOLUTION_100.md]({EVOLUTION_100_PATH})*
                """
            )

        cap_fold_pref = st.checkbox(
            "折叠能力地图",
            value=capability_collapsed,
            key="sidebar_capability_fold_pref",
        )
        if cap_fold_pref != capability_collapsed:
            st.session_state.sidebar_collapsed = set_section_collapsed(
                collapsed_prefs, "capability_map", cap_fold_pref
            )
            mark_dirty()

        render_capability_map_sidebar(expanded=not cap_fold_pref)

        playbook_collapsed = is_section_collapsed(collapsed_prefs, "playbook_preview")
        pb_fold_pref = st.checkbox(
            "折叠作战手册预览",
            value=playbook_collapsed,
            key="sidebar_playbook_fold_pref",
        )
        if pb_fold_pref != playbook_collapsed:
            st.session_state.sidebar_collapsed = set_section_collapsed(
                collapsed_prefs, "playbook_preview", pb_fold_pref
            )
            mark_dirty()

        render_playbook_preview_sidebar(expanded=not pb_fold_pref)

        render_theme_toggle()
        render_locale_toggle()
        render_share_panel()
        if not is_readonly_mode():
            render_push_panel()
        render_readonly_export_panel()
        render_health_panel()
        render_changelog_panel()
