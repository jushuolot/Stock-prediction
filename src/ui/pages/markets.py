"""市场一览 — 涨跌幅榜 + 板块 + 异动速览（P113 合并原 ③④⑤）。"""

from __future__ import annotations

import streamlit as st

from src.ui.pages import movers, panorama, plates

_SUBTAB_LABELS = ("📈 涨跌幅榜", "🧩 板块热点", "⚡ 异动速览")


def render() -> None:
    st.subheader("市场一览")
    st.caption(
        "**用法：** 先刷 **涨跌幅榜** 找热点 → 看 **板块** 谁在领涨 → "
        "需要批量归类时点 **异动速览**（基于当前榜单，约 1 秒）。"
    )
    cur = str(st.session_state.get("markets_subtab") or "movers")
    _HINTS = {"plates": "🧩 板块热点", "panorama": "⚡ 异动速览", "movers": "📈 涨跌幅榜"}
    if cur in _HINTS and cur != "movers":
        st.info(f"链接目标：**{_HINTS[cur]}** — 请点上方对应子标签。")

    t_movers, t_plates, t_pano = st.tabs(list(_SUBTAB_LABELS))
    with t_movers:
        st.session_state.markets_subtab = "movers"
        movers.render(embedded=True)
    with t_plates:
        st.session_state.markets_subtab = "plates"
        plates.render(embedded=True)
    with t_pano:
        st.session_state.markets_subtab = "panorama"
        panorama.render(embedded=True)
