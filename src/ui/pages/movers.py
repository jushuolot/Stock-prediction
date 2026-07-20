from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui import app_core as C

from src.providers import eastmoney, market_data
from src.storage.history_store import mark_dirty
from src.ui.movers_table import render_movers_table, sync_mover_pick_from_query
from src.util.query_time import format_query_datetime


def render(*, embedded: bool = False) -> None:
    if not embedded:
        st.subheader("全球股市")
    st.caption("A 股：东财→新浪；港股/美股：Yahoo（盘中/收盘以源站为准）。")
    C._show_query_banner("movers")
    market = st.selectbox(
        "市场",
        options=["A股", "港股", "美股"],
        index=0,
        key="movers_market_select",
    )
    board = st.selectbox(
        "榜单类型",
        options=["涨幅榜", "跌幅榜", "成交额榜", "换手率榜"],
        index=0,
    )
    if market != "A股" and board == "换手率榜":
        st.caption("换手率榜主要适用于 A 股；港/美股将按涨跌幅展示。")
    top_n = st.slider("显示条数", min_value=10, max_value=80, value=30, step=5)
    if st.button("刷新榜单", type="primary", use_container_width=True):
        with st.spinner("正在从公开源拉取榜单…"):
            df, src = market_data.fetch_global_ranking_multi(
                market=market, board=board, limit=top_n
            )
        st.session_state["movers_df"] = df
        st.session_state["movers_board"] = board
        st.session_state["movers_src"] = src
        st.session_state["movers_market"] = market
        C._stamp_query("movers")
        mark_dirty()
        C._save_history(
            log_kind="movers",
            log_label=f"{market} {board} 榜单",
            market=market,
            board=board,
            count=len(df),
        )

    movers = st.session_state.get("movers_df")
    if movers is None:
        st.info("选择市场与榜单类型后，点「刷新榜单」加载。")
    elif movers.empty:
        st.warning("暂未拉到榜单数据。可切换市场或稍后重试，也可到「搜索/添加」直接查个股。")
    else:
        q_movers = C._query_label("movers")
        st.success(
            f"榜单来源：{st.session_state.get('movers_src', '')}　|　"
            f"市场：{st.session_state.get('movers_market', market)}　|　"
            f"查询日期：{q_movers or format_query_datetime()}"
        )
        sync_mover_pick_from_query()
        codes = movers["代码"].astype(str).str.replace(r"\.0$", "", regex=True).tolist()
        cur = str(st.session_state.get("movers_pick_code") or "").replace(".0", "")
        if cur not in codes:
            st.session_state["movers_pick_code"] = codes[0]
        render_movers_table(
            movers,
            selected_code=str(st.session_state["movers_pick_code"]),
            query_label=q_movers,
        )
        pick_code = st.selectbox(
            "选择一只做深度溯源",
            options=codes,
            key="movers_pick_code",
        )
        pick_row = movers.loc[movers["代码"] == pick_code].iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            if st.button("加入自选股", key="add_mover"):
                kind = str(pick_row.get("类型") or C._pick_kind(pick_row.to_dict()))
                yh = str(pick_row.get("Yahoo代码") or pick_row["代码"])
                h = eastmoney.SearchHit(
                    code=str(pick_row["代码"]),
                    name=str(pick_row["名称"]),
                    market=str(pick_row.get("市场") or "A股"),
                    kind=kind,
                    yahoo=yh,
                )
                C._add_to_watchlist(h)
                st.success(f"已加入：{pick_row['名称']}（{pick_code}）")
        with c2:
            if st.button("生成行动路线", key="mover_route", type="primary"):
                st.session_state["insight_pick"] = pick_row.to_dict()
                st.session_state["insight_board"] = board
                st.session_state["insight_auto_days"] = 90
                st.session_state["insight_pending"] = True

