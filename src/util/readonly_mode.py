"""只读分享链接 ?readonly=1（P38）。"""

from __future__ import annotations

import streamlit as st

SESSION_KEY = "_readonly_mode"
QUERY_KEY = "readonly"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def parse_readonly_flag(raw: str | None) -> bool:
    if raw is None:
        return False
    return str(raw).strip().lower() in _TRUTHY


def apply_readonly_from_query() -> bool:
    """读取 ?readonly= 并写入 session_state。"""
    raw = st.query_params.get(QUERY_KEY, "")
    if raw:
        st.session_state[SESSION_KEY] = parse_readonly_flag(str(raw))
    return bool(st.session_state.get(SESSION_KEY))


def is_readonly_mode(session_state: dict | None = None) -> bool:
    state = session_state if session_state is not None else st.session_state
    return bool(state.get(SESSION_KEY))
