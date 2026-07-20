"""进化里程碑庆祝横幅（P61 600步 / P91 900步 / P99 1000步）：会话内一次性提示。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.util.app_meta import EVOLUTION_STEP

MILESTONE_STEP = 1000
WARMUP_MIN_STEP = 960
SESSION_FLAG = "_milestone_1000_banner_shown"
WARMUP_SESSION_FLAG = "_milestone_1000_warmup_shown"
EVOLUTION_100_PATH = "docs/EVOLUTION_100.md"


def build_milestone_message(step: int = EVOLUTION_STEP) -> str:
    """庆祝文案：千步达成 + 百步清单链接。"""
    return (
        f"🎉🎊 **{step} 步进化达成！** "
        f"Stock Assistant 已完成 **{step}** 步持续迭代 · "
        f"侧边栏可预览「公开数据作战手册」· "
        f"完整功能清单见 [`docs/EVOLUTION_100.md`]({EVOLUTION_100_PATH})"
    )


def build_warmup_message(step: int = EVOLUTION_STEP) -> str:
    """千步预热文案：距 1000 步里程碑剩余步数。"""
    remaining = max(0, MILESTONE_STEP - step)
    return (
        f"🔥 **千步进化预热** — 已完成 **{step}** 步，"
        f"距 **{MILESTONE_STEP}** 步里程碑还剩 **{remaining}** 步 · "
        f"侧边栏「作战手册预览」可先看每日流程 · "
        f"百步清单 [`docs/EVOLUTION_100.md`]({EVOLUTION_100_PATH})"
    )


def should_show_milestone(
    session_state: dict[str, Any],
    *,
    step: int = EVOLUTION_STEP,
    milestone: int = MILESTONE_STEP,
) -> bool:
    """step >= milestone 且本会话尚未展示过庆祝条。"""
    if step < milestone:
        return False
    if session_state.get(SESSION_FLAG):
        return False
    return True


def should_show_warmup(
    session_state: dict[str, Any],
    *,
    step: int = EVOLUTION_STEP,
    warmup_min: int = WARMUP_MIN_STEP,
    milestone: int = MILESTONE_STEP,
) -> bool:
    """step >= warmup_min 且 < milestone，本会话尚未展示预热条。"""
    if step < warmup_min or step >= milestone:
        return False
    if session_state.get(WARMUP_SESSION_FLAG):
        return False
    return True


def render_milestone_banner() -> None:
    ss = dict(st.session_state)
    if should_show_milestone(ss):
        st.success(build_milestone_message())
        st.session_state[SESSION_FLAG] = True
        return
    if should_show_warmup(ss):
        st.info(build_warmup_message())
        st.session_state[WARMUP_SESSION_FLAG] = True
