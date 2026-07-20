"""运行环境：是否在 Streamlit Cloud 等公网托管。"""

from __future__ import annotations

import os


def is_streamlit_cloud() -> bool:
    """Streamlit Community Cloud 会注入 STREAMLIT_SHARING 或 sharing 相关环境。"""
    if os.environ.get("STREAMLIT_SHARING", "").lower() in ("1", "true", "yes"):
        return True
    if os.environ.get("STOCK_CLOUD_HOST", "").lower() in ("1", "true", "yes", "streamlit"):
        return True
    try:
        import streamlit as st

        if st.secrets.get("STOCK_CLOUD_HOST"):
            return True
    except Exception:
        pass
    return False


def cloud_mode_label() -> str:
    if is_streamlit_cloud():
        return "公网云端（算力在 Streamlit 服务器，不占用你的电脑）"
    return "本地/自托管"
