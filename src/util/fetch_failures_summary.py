"""批量刷新失败汇总（P62）：可折叠失败列表与复制文本。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.util.retry_fetch_ui import failed_tickers


def failures_expander_label(count: int) -> str:
    """折叠区标题：失败 N 只。"""
    return f"失败 {count} 只"


def format_failures_for_copy(codes: list[str]) -> str:
    """每行一个代码，便于复制到 Excel / 终端。"""
    return "\n".join(codes)


def collect_failed_codes(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
) -> list[str]:
    """当前列表中摘要拉取失败的代码（保持 watchlist 顺序）。"""
    return failed_tickers(watchlist, snapshots)


def render_fetch_failures_summary(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    key_prefix: str = "watch",
) -> int:
    """展示可折叠失败汇总；返回失败数量。"""
    codes = collect_failed_codes(watchlist, snapshots)
    if not codes:
        return 0
    with st.expander(failures_expander_label(len(codes)), expanded=False):
        st.caption("以下标的摘要拉取失败，可复制代码后排查或逐行重试：")
        st.code(format_failures_for_copy(codes), language=None)
        st.text_area(
            "代码列表（可复制）",
            value=format_failures_for_copy(codes),
            height=min(80, 28 + len(codes) * 22),
            key=f"{key_prefix}_fail_copy",
            label_visibility="collapsed",
        )
    return len(codes)
