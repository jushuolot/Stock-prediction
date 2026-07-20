"""v5 千步庆祝横幅（P100）：与会话 milestone_banner 独立的一次性提示。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.util.app_meta import APP_VERSION, EVOLUTION_STEP

V5_CELEBRATION_MIN_STEP = 1000
SESSION_FLAG = "_v5_celebration_banner_shown"
EVOLUTION_100_PATH = "docs/EVOLUTION_100.md"


def build_v5_celebration_message(
    *,
    version: str = APP_VERSION,
    step: int = EVOLUTION_STEP,
) -> str:
    """v5 时代庆祝文案：强调版本里程碑，区别于步数庆祝条。"""
    return (
        f"🚀 **欢迎进入 Stock Assistant v{version}！** "
        f"千步进化新起点（step **{step}**）· "
        f"公开数据作战手册已内置预览 · "
        f"下一步可用「自选健康分」一眼看懂组合状态 · "
        f"进化路线见 [`EVOLUTION.md`](../EVOLUTION.md) · "
        f"百步清单 [`docs/EVOLUTION_100.md`]({EVOLUTION_100_PATH})"
    )


def should_show_v5_celebration(
    session_state: dict[str, Any],
    *,
    step: int = EVOLUTION_STEP,
    min_step: int = V5_CELEBRATION_MIN_STEP,
) -> bool:
    """step >= min_step 且本会话尚未展示 v5 庆祝条。"""
    if step < min_step:
        return False
    if session_state.get(SESSION_FLAG):
        return False
    return True


def render_v5_celebration_banner() -> None:
    ss = dict(st.session_state)
    if not should_show_v5_celebration(ss):
        return
    st.info(build_v5_celebration_message())
    st.session_state[SESSION_FLAG] = True
