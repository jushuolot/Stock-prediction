"""搜索页快捷筛选与代码列表（P22）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import streamlit as st

from src.ui.df_style import show_df


def _pct(snap: dict[str, Any]) -> float | None:
    v = snap.get("pct")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _score(snap: dict[str, Any]) -> float | None:
    v = snap.get("score")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class QuickFilter:
    id: str
    label: str
    predicate: Callable[[dict[str, Any], dict[str, Any]], bool]


QUICK_FILTERS: tuple[QuickFilter, ...] = (
    QuickFilter("pct_up_3", "涨幅>3%", lambda _i, s: (_p := _pct(s)) is not None and _p > 3.0),
    QuickFilter("pct_down_3", "跌幅<-3%", lambda _i, s: (_p := _pct(s)) is not None and _p < -3.0),
    QuickFilter("score_gt_70", "评分>70", lambda _i, s: (_sc := _score(s)) is not None and _sc > 70.0),
    QuickFilter("score_lt_40", "评分<40", lambda _i, s: (_sc := _score(s)) is not None and _sc < 40.0),
    QuickFilter("has_brief", "有摘要", lambda _i, s: bool(str(s.get("one_line") or "").strip())),
)


def filter_watchlist_by_preset(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    preset_id: str,
) -> list[dict[str, Any]]:
    filt = next((f for f in QUICK_FILTERS if f.id == preset_id), None)
    if filt is None:
        return list(watchlist)
    out: list[dict[str, Any]] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snapshots.get(code) or {}
        if filt.predicate(item, snap):
            out.append(item)
    return out


def format_ticker_list(
    watchlist: list[dict[str, Any]],
    *,
    sep: str = ", ",
    line_break: bool = False,
) -> str:
    codes = [str(i.get("代码") or "").strip() for i in watchlist if str(i.get("代码") or "").strip()]
    if line_break:
        return "\n".join(codes)
    return sep.join(codes)


def preset_filter_summary(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    preset_id: str,
) -> list[dict[str, str]]:
    """返回筛选结果的简要行（名称/代码/涨跌幅/评分）。"""
    rows: list[dict[str, str]] = []
    for item in filter_watchlist_by_preset(watchlist, snapshots, preset_id):
        code = str(item.get("代码") or "")
        snap = snapshots.get(code) or {}
        pct = _pct(snap)
        score = _score(snap)
        rows.append(
            {
                "名称": str(item.get("名称") or code),
                "代码": code,
                "涨跌幅": f"{pct:+.2f}%" if pct is not None else "—",
                "评分": f"{score:.1f}" if score is not None else "—",
            }
        )
    return rows


def render_search_quick_actions() -> None:
    """在搜索页展示快捷筛选与可复制代码列表。"""
    wl = list(st.session_state.get("watchlist") or [])
    snaps = dict(st.session_state.get("watch_snapshots") or {})
    if not wl:
        return

    with st.expander("⚡ 快捷筛选 / 代码列表", expanded=False):
        st.caption("基于工作台已缓存摘要筛选；结果可一键复制代码到其他工具。")
        cols = st.columns(min(len(QUICK_FILTERS), 5))
        active = st.session_state.get("search_quick_filter")
        for i, filt in enumerate(QUICK_FILTERS):
            with cols[i % len(cols)]:
                if st.button(filt.label, key=f"qf_{filt.id}", use_container_width=True):
                    st.session_state.search_quick_filter = filt.id

        if active:
            filt = next((f for f in QUICK_FILTERS if f.id == active), None)
            if filt:
                matched = filter_watchlist_by_preset(wl, snaps, active)
                st.markdown(f"**{filt.label}** · 命中 {len(matched)} / {len(wl)} 只")
                if matched:
                    show_df(
                        preset_filter_summary(wl, snaps, active),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("当前快照下无匹配项，可先在工作台「刷新全部摘要」。")

        st.text_area(
            "自选股代码（可复制）",
            value=format_ticker_list(wl, line_break=True),
            height=80,
            help="每行一个代码，便于粘贴到 Excel / 终端 / 其他行情软件",
            key="search_ticker_copy_list",
        )
