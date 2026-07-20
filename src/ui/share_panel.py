"""侧边栏：公网分享文案（P4）。"""

from __future__ import annotations

import os

import streamlit as st

from src.util.share_message import build_share_message


def _public_app_url() -> str:
    try:
        v = st.secrets.get("STOCK_APP_PUBLIC_URL")
        if v is not None and str(v).strip():
            return str(v).strip()
    except Exception:
        pass
    return os.environ.get("STOCK_APP_PUBLIC_URL", "").strip()


def render_share_panel() -> None:
    url = _public_app_url()
    with st.expander("📤 分享给同事", expanded=False):
        if not url:
            st.caption(
                "在 Streamlit Cloud **Secrets** 或本地 `.streamlit/secrets.toml` 中配置 "
                "`STOCK_APP_PUBLIC_URL = \"https://xxx.streamlit.app\"` 后可一键复制分享文案。"
            )
            st.caption("详见仓库 `DEPLOY_STREAMLIT.md`。")
            return

        include_pw = st.checkbox("文案中包含密码（仅私聊时使用）", value=False, key="share_include_pw")
        pw = ""
        if include_pw:
            try:
                pw = str(st.secrets.get("STOCK_ASSISTANT_PASSWORD") or "")
            except Exception:
                pw = os.environ.get("STOCK_ASSISTANT_PASSWORD", "")

        msg = build_share_message(app_url=url, password=pw, include_password=include_pw)
        st.text_area("分享文案", value=msg, height=260, key="share_msg_preview")
        st.download_button(
            "下载分享说明 (.txt)",
            data=msg.encode("utf-8"),
            file_name="StockAssistant_分享说明.txt",
            mime="text/plain",
            key="share_msg_download",
            use_container_width=True,
        )
        st.caption(f"公网链接：{url}")
