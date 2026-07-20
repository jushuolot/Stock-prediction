from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.df_style import show_df

from src.storage.history_store import mark_dirty
from src.ui import app_core as C
from src.ui.quick_actions import render_search_quick_actions
from src.ui.simple_result import render_search_result_banner
from src.providers import eastmoney, symbol_search, yahoo
from src.util.readonly_mode import is_readonly_mode
from src.util.search_history import normalize_search_history, push_search
from src.util.watchlist_add import add_hit_to_watchlist, effective_code, is_in_watchlist


def _run_global_search(keyword: str) -> None:
    kw = (keyword or "").strip()
    st.session_state.last_hits = symbol_search.suggest(kw, limit=40)
    if kw:
        st.session_state.search_history = push_search(
            st.session_state.get("search_history"),
            kw,
        )
        mark_dirty()
    C._stamp_query("search")


def render() -> None:
    st.subheader("发现标的")
    st.caption(
        "输入中文名、代码或拼音（如 茅台、600519、0700）→ **开始搜索** → **加入自选**。"
        "加完后去 **① 自选分析** 做一键分析。"
    )
    render_search_quick_actions()
    C._show_query_banner("search")

    st.session_state.setdefault("search_kw", "茅台")
    history = normalize_search_history(st.session_state.get("search_history"))
    if history:
        st.caption("最近搜索（点击重搜）")
        chip_cols = st.columns(min(len(history), 8))
        for i, term in enumerate(history[:8]):
            with chip_cols[i % len(chip_cols)]:
                if st.button(term, key=f"search_hist_{i}", use_container_width=True):
                    st.session_state.search_kw = term
                    with st.spinner("正在并行搜索 A 股 / 港股 / 美股…"):
                        _run_global_search(term)
                    st.rerun()

    kw = st.text_input(
        "关键词",
        key="search_kw",
        placeholder="中文名、代码、拼音、美股代码 SNX、公司英文名 synnex…",
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("开始搜索", type="primary", use_container_width=True):
            with st.spinner("正在并行搜索 A 股 / 港股 / 美股…"):
                _run_global_search(kw)
    with col2:
        st.caption("同时查 A 股、港股、美股，不用切换市场。")

    hits: list[eastmoney.SearchHit] = st.session_state.last_hits or []
    if hits:
        cnt = symbol_search.count_by_kind(hits)
        render_search_result_banner(
            total=len(hits),
            a=cnt["A"],
            hk=cnt["HK"],
            us=cnt["US"],
            other=cnt["OTHER"],
        )
        readonly = is_readonly_mode()
        wl = list(st.session_state.get("watchlist") or [])
        preview = []
        for h in hits:
            code = effective_code(h)
            status = "已加入" if is_in_watchlist(wl, code) else "可加入"
            preview.append(
                {
                    "名称": h.name,
                    "代码": code,
                    "市场": h.kind,
                    "状态": status,
                }
            )
        show_df(pd.DataFrame(preview), use_container_width=True, hide_index=True)
        st.caption("👇 点右侧按钮加入自选")
        for i, h in enumerate(hits):
            code = effective_code(h)
            in_wl = is_in_watchlist(wl, code)
            row = st.columns([5, 1])
            with row[0]:
                st.markdown(C._hit_label(h))
            with row[1]:
                if readonly:
                    st.caption("只读")
                elif in_wl:
                    st.caption("已加入")
                elif st.button("加入自选", key=f"search_quick_add_{i}", use_container_width=True):
                    new_wl, added = add_hit_to_watchlist(st.session_state.watchlist, h)
                    if added:
                        st.session_state.watchlist = new_wl
                        mark_dirty()
                        C._save_history(log_kind="watchlist", log_label=f"加入自选股 {h.name}")
                        st.toast(f"已加入自选：{h.name}")
                        st.rerun()

        labels = [C._hit_label(h) for h in hits]
        idx = st.selectbox("选一只看详细介绍", range(len(labels)), format_func=lambda i: labels[i])
        h = hits[int(idx)]
        st.markdown(f"#### {h.name}（{effective_code(h)}）")
        if h.kind in ("US", "HK") and h.yahoo:
            try:
                prof = yahoo.fetch_profile(h.yahoo)
                st.markdown(
                    f"- **交易所：** {prof.exchange or '—'}\n"
                    f"- **行业：** {prof.industry or '—'}\n"
                    f"- **板块：** {prof.sector or '—'}"
                )
                if prof.long_business_summary:
                    st.caption(prof.long_business_summary[:500] + ("…" if len(prof.long_business_summary) > 500 else ""))
            except Exception as e:
                st.warning(f"简介拉取失败：{e}")
        else:
            stub = eastmoney.fetch_company_profile_stub(h)
            if isinstance(stub, dict):
                for k, v in stub.items():
                    st.markdown(f"- **{k}：** {v}")
            else:
                st.write(stub)
        if readonly:
            st.caption("只读模式：无法加入自选股。")
        elif is_in_watchlist(st.session_state.watchlist, effective_code(h)):
            st.caption("已在自选股中。")
        elif st.button("加入这只到自选", use_container_width=True):
            if C._add_to_watchlist(h):
                st.success(f"✅ 已加入自选：{h.name}。请到 **① 自选分析** 查看。")
    else:
        st.info("👆 输入关键词后点 **「开始搜索」**。例如：茅台、0700、苹果、SNX。")
