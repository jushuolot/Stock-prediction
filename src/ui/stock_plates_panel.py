"""所属板块 + 相关个股（主从面板）。"""

from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from src.providers.eastmoney_stock_plates import fetch_plate_constituents, fetch_stock_belong_plates
from src.ui.df_style import show_df

@st.cache_data(ttl=180, show_spinner=False)
def _cached_belong_plates(code6: str, limit: int) -> pd.DataFrame:
    return fetch_stock_belong_plates(code6, limit=limit)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_constituents(bk_code: str, sort: str, limit: int) -> pd.DataFrame:
    return fetch_plate_constituents(bk_code, sort=sort, limit=limit)


def render_stock_plates_panel(
    *,
    code: str,
    name: str = "",
    key_prefix: str = "plates",
    on_add_watchlist: Callable[[str, str], None] | None = None,
    belong_limit: int = 60,
    constituent_limit: int = 35,
    lazy: bool = False,
) -> None:
    """渲染「所属板块 / 阶段涨幅」主从 UI。仅适用于 6 位 A 股代码。"""
    code6 = str(code or "").strip()
    if code6.isdigit() and len(code6) <= 6:
        code6 = code6.zfill(6)
    if not (code6.isdigit() and len(code6) == 6):
        st.caption("所属板块仅支持沪深京 A 股 6 位代码。")
        return

    load_sk = f"{key_prefix}_plates_loaded_{code6}"
    if lazy:
        if st.button("加载所属板块", key=f"{load_sk}_btn", type="secondary"):
            st.session_state[load_sk] = True
            _cached_belong_plates.clear()
            _cached_constituents.clear()
        if not st.session_state.get(load_sk):
            st.caption("点击上方按钮拉取所属板块与相关个股（东财）。")
            return

    tab_belong, tab_period = st.tabs(["所属板块", "阶段涨幅"])

    with tab_period:
        st.caption("敬请期待：个股与各板块阶段涨幅对比。")

    with tab_belong:
        sk = f"{key_prefix}_belong_sel"
        sort_k = f"{key_prefix}_const_sort"

        if st.button("刷新所属板块", key=f"{key_prefix}_refresh", type="secondary"):
            _cached_belong_plates.clear()
            _cached_constituents.clear()

        with st.spinner("正在拉取所属板块…"):
            belong_df = _cached_belong_plates(code6, belong_limit)

        if belong_df is None or belong_df.empty:
            st.info("暂未拉到所属板块数据，请稍后重试。")
            return

        labels = []
        for _, row in belong_df.iterrows():
            pct = row.get("涨跌幅%")
            pct_s = f"{pct:+.2f}%" if pct is not None and not pd.isna(pct) else "—"
            labels.append(f"{row['名称']}（{pct_s}）")

        prev = st.session_state.get(sk)
        if prev is None or prev >= len(labels):
            st.session_state[sk] = 0

        st.markdown("**所属板块**")
        top_show = belong_df[["名称", "涨跌幅%", "领涨股"]].copy()
        show_df(
            top_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "涨跌幅%": st.column_config.NumberColumn("涨跌幅%", format="%.2f%%"),
            },
            key=f"{key_prefix}_top_tbl",
        )

        sel_idx = st.selectbox(
            "选择板块（查看相关个股）",
            range(len(labels)),
            format_func=lambda i: labels[i],
            key=sk,
        )
        sel_idx = int(sel_idx)
        row = belong_df.iloc[sel_idx]
        bk = str(row.get("板块代码") or "")
        plate_name = str(row.get("名称") or "")
        plate_link = str(row.get("相关链接") or "")

        sort_label = st.selectbox(
            "成份股排序",
            ["股票涨跌幅排行", "成交额排行"],
            index=0,
            key=sort_k,
        )
        sort_key = "amount" if sort_label == "成交额排行" else "pct"

        with st.spinner(f"正在拉取「{plate_name}」成份股…"):
            cons_df = _cached_constituents(bk, sort_key, constituent_limit)

        h1, h2 = st.columns([3, 1])
        with h1:
            st.markdown(f"**{plate_name}相关个股**")
        with h2:
            if plate_link:
                st.link_button("更多", plate_link, use_container_width=True)

        if cons_df is None or cons_df.empty:
            st.warning("暂未拉到成份股，请换板块或稍后重试。")
            return

        cons_show = cons_df[["名称", "最新价", "涨跌幅%"]].copy()
        show_df(
            cons_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "最新价": st.column_config.NumberColumn("最新价", format="%.2f"),
                "涨跌幅%": st.column_config.NumberColumn("涨跌幅%", format="%.2f%%"),
            },
            key=f"{key_prefix}_bottom_tbl",
        )

        if on_add_watchlist:
            pick_label = st.selectbox(
                "加入自选股",
                range(len(cons_df)),
                format_func=lambda i: f"{cons_df.iloc[i]['名称']}（{cons_df.iloc[i]['代码']}）",
                key=f"{key_prefix}_wl_pick",
            )
            if st.button("加入所选到自选股", key=f"{key_prefix}_wl_add"):
                r = cons_df.iloc[int(pick_label)]
                c = str(r.get("代码") or "").strip()
                n = str(r.get("名称") or "").strip()
                if c and n:
                    on_add_watchlist(c, n)
                    st.success(f"已加入 {n}（{c}）。")
