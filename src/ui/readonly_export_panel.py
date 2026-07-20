"""只读快照导出 UI（P7）。"""

from __future__ import annotations

import streamlit as st

from src.export.readonly_snapshot import collect_snapshot_from_session, snapshot_to_json_bytes
from src.util.query_time import format_query_datetime


def render_readonly_export_panel() -> None:
    with st.expander("📦 只读数据快照", expanded=False):
        st.caption("导出 JSON，供脚本或同事只读读取（不含密码）。")
        snap = collect_snapshot_from_session(st.session_state)
        st.download_button(
            "下载 snapshot.json",
            data=snapshot_to_json_bytes(snap),
            file_name=f"stock_assistant_snapshot_{format_query_datetime().replace(':', '-').replace(' ', '_')}.json",
            mime="application/json",
            key="readonly_snapshot_dl",
            use_container_width=True,
        )
        st.caption(f"schema: {snap.get('schema')} · 自选 {snap.get('counts', {}).get('watchlist', 0)} 只")
