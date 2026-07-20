"""花园页紧凑多人选股条 UI（P123）。"""

from __future__ import annotations

import streamlit as st

from src.analysis.garden_cohort import build_cohort_strip_payload, resolve_cohort_data


def render_garden_cohort_strip() -> None:
    st.markdown("### 👥 云端同伴选股")
    payload = build_cohort_strip_payload(resolve_cohort_data())
    if not payload.get("has_data"):
        st.info(str(payload.get("message") or "暂无多人汇总。"))
        return
    st.caption(payload["headline"])
    for line in payload.get("top_lines") or []:
        st.caption(f"· {line}")
    st.caption(payload.get("detail_caption") or "")
