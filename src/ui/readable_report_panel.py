"""可读分析简报 UI。"""

from __future__ import annotations

import streamlit as st

from src.analysis.readable_report import build_stock_brief_markdown


def render_readable_brief_panel(
    *,
    brief_md: str,
    file_stem: str,
    key_prefix: str = "brief",
    one_line: str | None = None,
    score: float | None = None,
) -> None:
    """展示 Markdown 简报并提供下载。"""
    if not brief_md.strip():
        return
    with st.expander("📄 可读分析简报", expanded=True):
        from src.ui.simple_result import render_brief_tldr

        render_brief_tldr(one_line, score=score)
        st.caption("完整内容如下；也可直接下载 `.md` 文件。")
        st.markdown(brief_md)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in file_stem)[:40]
        st.download_button(
            "下载简报 (.md)",
            data=brief_md.encode("utf-8"),
            file_name=f"{safe}_简报.md",
            mime="text/markdown",
            key=f"{key_prefix}_download",
            use_container_width=True,
        )


def build_and_store_brief(
    *,
    session_key: str,
    **kwargs,
) -> str:
    md = build_stock_brief_markdown(**kwargs)
    st.session_state[session_key] = md
    return md
