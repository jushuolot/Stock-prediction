from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui import app_core as C
from src.storage.serialize import route_report_from_session


def render() -> None:
    st.subheader("行动路线")
    st.caption("完整版报告页；日常建议在「① 分析工作台」内查看并导出简报。")
    C._show_query_banner("insight", extra=st.session_state.get("insight_range") or "")

    pick = st.session_state.get("insight_pick")
    if not pick:
        st.info("请先在「④ 全球股市」或「① 分析工作台」生成行动路线。")
    else:
        code = str(pick.get("代码") or "")
        name = str(pick.get("名称") or "")
        st.write(f"当前标的：**{name}（{code}）**　|　市场：{pick.get('市场', '')}")
        st.caption("K 线、财务对比、所属板块请在「① 分析工作台」查看。")
        if C._query_label("insight"):
            st.caption(f"本次报告查询时间：{C._query_label('insight')}")
        default_days = int(st.session_state.pop("insight_auto_days", 90))
        days = st.selectbox("分析回看天数", [90, 180, 365], index=[90, 180, 365].index(default_days))
        if st.button("重新生成报告", type="primary") or st.session_state.pop("insight_pending", False):
            C._run_insight_report(name=name, code=code, days=days, pick=pick)

    rep = route_report_from_session(st.session_state.get("route_report"))
    if rep:
        C._render_route_report_block(rep)
        if C._query_label("insight"):
            st.caption(f"本次查询时间：{C._query_label('insight')}")

