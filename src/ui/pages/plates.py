from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.df_style import show_df

from src.ui import app_core as C

from src.providers import eastmoney, eastmoney_plates
from src.providers.ticker_util import yahoo_ticker_a
from src.util.query_time import format_query_datetime


def render(*, embedded: bool = False) -> None:
    if not embedded:
        st.subheader("板块行情")
    st.caption(
        "行业 / 概念 / 地区板块与资金流向（东财公开接口）。"
        "「相关链接」可打开东财板块页。"
    )
    C._show_query_banner("plates")
    plates_n = st.slider("显示条数", min_value=10, max_value=80, value=40, step=5, key="plates_top_n")
    plates_sort = st.selectbox("榜单", options=["涨幅榜", "跌幅榜"], index=0, key="plates_sort")
    st.caption("主力净流入单位为万元（东财原始为元 ÷10000）。")

    def _plates_display_cols(df: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "板块名称",
            "相关链接",
            "最新价",
            "涨跌额",
            "涨跌幅",
            "主力净流入",
            "领涨股",
            "领涨股涨跌幅",
        ]
        have = [c for c in cols if c in df.columns]
        return df[have] if have else df

    def _render_plate_table(
        df: pd.DataFrame | None,
        *,
        query_key: str,
        tab_key: str,
        show_lead_pick: bool,
    ) -> None:
        if df is None:
            st.info("选择子页后点击「刷新」加载板块数据。")
            return
        if df.empty:
            st.warning("暂未拉到板块数据，请稍后重试或检查网络（需能访问东财 push2 接口）。")
            return
        q = C._query_label(query_key) or format_query_datetime()
        st.caption(f"查询时间：{q}　共 {len(df)} 条")
        show_df(
            _plates_display_cols(df),
            use_container_width=True,
            hide_index=True,
            column_config={
                "相关链接": st.column_config.LinkColumn("相关链接", display_text="打开"),
                "涨跌幅": st.column_config.NumberColumn("涨跌幅", format="%.2f%%"),
                "领涨股涨跌幅": st.column_config.NumberColumn("领涨股涨跌幅", format="%.2f%%"),
                "主力净流入": st.column_config.NumberColumn("主力净流入(万)", format="%.2f"),
            },
        )
        if show_lead_pick and "领涨股代码" in df.columns:
            leads = df.loc[
                df["领涨股代码"].astype(str).str.len() >= 4,
                ["领涨股", "领涨股代码"],
            ].drop_duplicates(subset=["领涨股代码"])
            if not leads.empty:
                idx = st.selectbox(
                    "领涨股快捷操作",
                    options=range(len(leads)),
                    format_func=lambda i: f"{leads.iloc[i]['领涨股']} ({leads.iloc[i]['领涨股代码']})",
                    key=f"plates_lead_{tab_key}",
                )
                row = leads.iloc[int(idx)]
                code = str(row["领涨股代码"])
                name = str(row["领涨股"])
                if st.button("加入自选股", key=f"plates_add_lead_{tab_key}"):
                    h = eastmoney.SearchHit(
                        code=code,
                        name=name,
                        market="A股",
                        kind="A",
                        yahoo=yahoo_ticker_a(code),
                    )
                    C._add_to_watchlist(h)
                    st.success(f"已加入：{name}（{code}）")

    t_plate_ind, t_plate_con, t_plate_reg, t_plate_flow = st.tabs(
        ["行业板块", "概念板块", "地区板块", "资金流向"]
    )

    with t_plate_ind:
        if st.button("刷新行业板块", type="primary", key="plates_refresh_ind"):
            with st.spinner("正在拉取行业板块…"):
                st.session_state["plates_ind"] = eastmoney_plates.fetch_plate_board(
                    category="行业板块", board=plates_sort, limit=plates_n
                )
            C._stamp_query("plates")
        _render_plate_table(
            st.session_state.get("plates_ind"),
            query_key="plates",
            tab_key="ind",
            show_lead_pick=True,
        )

    with t_plate_con:
        if st.button("刷新概念板块", type="primary", key="plates_refresh_con"):
            with st.spinner("正在拉取概念板块…"):
                st.session_state["plates_con"] = eastmoney_plates.fetch_plate_board(
                    category="概念板块", board=plates_sort, limit=plates_n
                )
            C._stamp_query("plates")
        _render_plate_table(
            st.session_state.get("plates_con"),
            query_key="plates",
            tab_key="con",
            show_lead_pick=True,
        )

    with t_plate_reg:
        if st.button("刷新地区板块", type="primary", key="plates_refresh_reg"):
            with st.spinner("正在拉取地区板块…"):
                st.session_state["plates_reg"] = eastmoney_plates.fetch_plate_board(
                    category="地区板块", board=plates_sort, limit=plates_n
                )
            C._stamp_query("plates")
        _render_plate_table(
            st.session_state.get("plates_reg"),
            query_key="plates",
            tab_key="reg",
            show_lead_pick=True,
        )

    with t_plate_flow:
        st.caption("按主力净流入降序（行业 + 概念 + 地区合并展示）。")
        if st.button("刷新资金流向", type="primary", key="plates_refresh_flow"):
            with st.spinner("正在拉取资金流向…"):
                st.session_state["plates_flow"] = eastmoney_plates.fetch_flow_board(limit=plates_n)
            C._stamp_query("plates")
        _render_plate_table(
            st.session_state.get("plates_flow"),
            query_key="plates",
            tab_key="flow",
            show_lead_pick=False,
        )

