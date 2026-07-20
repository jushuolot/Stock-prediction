"""页面底部版本信息。"""

from __future__ import annotations

import streamlit as st

from src.util.app_meta import APP_VERSION, BUILD_LABEL, EVOLUTION_STEP
from src.util.cloud_picks_loader import load_cloud_picks
from src.ui.keyboard_hints import render_keyboard_hints
from src.ui.milestone_banner import MILESTONE_STEP, WARMUP_MIN_STEP


def build_footer_warmup_note(step: int = EVOLUTION_STEP) -> str | None:
    """step >= 960 时页脚附加千步预热说明。"""
    if step < WARMUP_MIN_STEP:
        return None
    if step >= MILESTONE_STEP:
        return (
            f"🎉 千步进化里程碑已达成（{MILESTONE_STEP} 步）· "
            f"见 docs/EVOLUTION_100.md"
        )
    remaining = MILESTONE_STEP - step
    return (
        f"🔥 千步预热：已完成 {step} 步，距 {MILESTONE_STEP} 步还剩 {remaining} 步"
    )


def _ritual_footer_bits() -> str:
    meta = st.session_state.get("ritual_meta")
    if not meta:
        cloud = load_cloud_picks()
        meta = (cloud or {}).get("ritual")
    if not meta:
        return ""
    bar = meta.get("data_bar_date") or "—"
    src = meta.get("data_source") or "—"
    fresh = "新鲜" if meta.get("data_fresh") else "滞后"
    return f" · 行情截止 {bar} · {src} · {fresh}"


def render_app_footer() -> None:
    simple = str(st.session_state.get("ui_mode", "garden")) != "pro"
    st.divider()
    if not simple:
        render_keyboard_hints()
    ritual_bits = _ritual_footer_bits()
    st.caption(
        f"Stock Assistant v{APP_VERSION} · {BUILD_LABEL}{ritual_bits} · "
        f"已进化 {EVOLUTION_STEP} 步 · 非投资建议"
    )
    if simple:
        st.caption("🌱 私人花园 · 密码仅你我知道 · 详见 docs/PRIVATE_GARDEN.md")
        return
    warmup_note = build_footer_warmup_note()
    if warmup_note:
        st.caption(warmup_note)
