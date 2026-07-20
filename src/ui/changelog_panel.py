"""侧边栏更新日志。"""

from __future__ import annotations

import streamlit as st

from src.util.app_meta import APP_VERSION, CHANGELOG, EVOLUTION_STEP


def render_changelog_panel() -> None:
    with st.expander("📜 进化日志", expanded=False):
        st.caption(f"v{APP_VERSION} · 累计 {EVOLUTION_STEP} 步")
        for phase, desc in CHANGELOG:
            st.markdown(f"- **{phase}** — {desc}")
        st.caption("完整百步清单见 `docs/EVOLUTION_100.md`")
