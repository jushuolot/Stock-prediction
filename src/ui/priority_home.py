"""首页作战入口：今日先看这 3 只（P89）。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.analysis.priority_queue import PriorityRank, rank_watchlist_priority
from src.analysis.watch_alerts import compute_watch_alerts
from src.storage.history_store import mark_dirty
from src.util.recent_viewed import push_recent_viewed, normalize_recent_viewed

PRIORITY_HOME_TITLE = "今日先看这3只"
PRIORITY_HOME_TOP_N = 3


def _alert_kwargs(session_state: Any) -> dict[str, float]:
    return {
        "pct_up": float(session_state.get("alert_pct_up", 5.0)),
        "pct_down": float(session_state.get("alert_pct_down", -5.0)),
        "score_low": float(session_state.get("alert_score_low", 40.0)),
        "score_high": float(session_state.get("alert_score_high", 65.0)),
        "price_targets": session_state.get("price_targets"),
    }


def compute_priority_home_ranks(
    session_state: Any,
    *,
    top_n: int = PRIORITY_HOME_TOP_N,
) -> list[PriorityRank]:
    """从 session 计算首页展示的 Top N 优先标的。"""
    wl = session_state.get("watchlist") or []
    snaps = session_state.get("watch_snapshots") or {}
    if not wl or not snaps:
        return []
    alert_kw = _alert_kwargs(session_state)
    alerts = compute_watch_alerts(wl, snaps, **alert_kw)
    return rank_watchlist_priority(
        wl,
        snaps,
        alerts=alerts,
        stale_hours=float(session_state.get("stale_hours", 24.0)),
        brief_for_code=lambda c: session_state.get(f"brief_md_{c}"),
        top_n=top_n,
        **alert_kw,
    )


def build_priority_home_labels(ranks: list[PriorityRank]) -> list[dict[str, str]]:
    """UI 按钮标签：code / name / label / reason。"""
    out: list[dict[str, str]] = []
    for i, r in enumerate(ranks, start=1):
        out.append(
            {
                "code": r.code,
                "name": r.name,
                "label": f"{i}. {r.name}（{r.code}）",
                "reason": r.reason,
            }
        )
    return out


def should_show_priority_home(session_state: Any) -> bool:
    return bool(compute_priority_home_ranks(session_state))


def render_priority_home_entry(session_state: Any | None = None) -> None:
    """首页醒目入口：Top 3 优先标的快捷跳转工作台。"""
    ss = session_state if session_state is not None else st.session_state
    ranks = compute_priority_home_ranks(ss)
    if not ranks:
        return
    labels = build_priority_home_labels(ranks)
    st.markdown(f"### 🎯 {PRIORITY_HOME_TITLE}")
    st.caption("按提醒、风险与板块强弱综合排序 — 点名称直达「① 分析工作台」")
    cols = st.columns(min(len(labels), PRIORITY_HOME_TOP_N))
    for i, item in enumerate(labels):
        with cols[i]:
            if st.button(
                item["label"],
                key=f"priority_home_btn_{item['code']}",
                use_container_width=True,
                help=item["reason"][:120],
            ):
                ss.watch_code = item["code"]
                ss.active_tab = "watch"
                old = normalize_recent_viewed(ss.get("recent_viewed"))
                new = push_recent_viewed(old, code=item["code"], name=item["name"])
                if new != old:
                    ss.recent_viewed = new
                mark_dirty()
                st.rerun()
