"""移动端布局样式（P6）。"""

from __future__ import annotations

import streamlit as st

_MOBILE_CSS = """
<style>
/* 手机 / 窄屏：更易读、少横向滚动 */
@media (max-width: 768px) {
  .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    max-width: 100% !important;
  }
  [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
  [data-testid="stDataFrame"] div { font-size: 12px !important; }
  .stDownloadButton button, .stButton button {
    min-height: 2.75rem;
  }
  h1 { font-size: 1.35rem !important; }
  [data-testid="stTabs"] button { font-size: 0.72rem !important; padding: 0.35rem 0.5rem !important; }
}
@media (max-width: 480px) {
  [data-testid="stSidebar"] {
    min-width: min(100vw, 300px) !important;
  }
}
</style>
"""


def inject_mobile_styles() -> None:
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)
