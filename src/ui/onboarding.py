"""新手引导与空状态提示（P5）。"""

from __future__ import annotations

import streamlit as st


def render_onboarding_banner() -> None:
    wl = st.session_state.get("watchlist") or []
    snaps = st.session_state.get("watch_snapshots") or {}

    if not wl:
        st.info(
            "👋 **第一次用？照着做就行：**\n\n"
            "1. 点 **② 发现标的** → 输入「茅台」→ **开始搜索** → **加入自选**\n"
            "2. 回到 **① 自选分析** → **刷新全部摘要** 或 **⚡ 一键分析**\n"
            "3. 看 **绿色/红色结论框**，满意就下载 `.md` 简报"
        )
        return

    if not snaps:
        st.warning(
            "💡 自选股已有 **{}** 只，尚未生成摘要。请进入 **① 自选分析** → "
            "点 **刷新全部摘要**（快速）或选中一只后 **⚡ 一键分析**（完整简报）。".format(len(wl))
        )
        return

    stale = sum(1 for x in wl if str(x.get("代码") or "") not in snaps)
    if stale > 0:
        st.caption(f"ℹ️ 有 {stale} 只自选股尚无摘要，可在工作台 **刷新全部摘要** 补齐。")
