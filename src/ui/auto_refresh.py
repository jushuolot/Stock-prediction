"""自选股摘要定时刷新（P6）。"""

from __future__ import annotations

import time
from typing import Any, Callable

import streamlit as st

from src.analysis.quick_analyze import refresh_watch_snapshots
from src.storage.history_store import mark_dirty
from src.util.query_time import format_query_datetime


def should_auto_refresh(*, now: float, last: float | None, interval_minutes: int) -> bool:
    if interval_minutes <= 0:
        return False
    if last is None:
        return True
    return (now - last) >= float(interval_minutes) * 60.0


def render_auto_refresh_controls() -> None:
    with st.expander("⏱ 自动刷新摘要", expanded=False):
        st.session_state.setdefault("auto_refresh_enabled", False)
        st.session_state.setdefault("auto_refresh_minutes", 5)
        st.toggle("开启自动刷新（页面保持打开时有效）", key="auto_refresh_enabled")
        st.selectbox(
            "刷新间隔",
            options=[5, 10, 15, 30],
            format_func=lambda x: f"每 {x} 分钟",
            key="auto_refresh_minutes",
            disabled=not st.session_state.get("auto_refresh_enabled"),
        )
        if st.session_state.get("auto_refresh_enabled"):
            st.caption("后台每 60 秒检测一次；到间隔后自动拉取日 K 与评分。")
        if st.session_state.get("_auto_refresh_at"):
            st.caption(f"上次自动刷新：{st.session_state.get('_auto_refresh_at')}")


def _tick_auto_refresh(fetch_fn: Callable[..., Any]) -> None:
    if not st.session_state.get("auto_refresh_enabled"):
        return
    if not st.session_state.get("watchlist"):
        return
    now = time.time()
    last_ts = st.session_state.get("_auto_refresh_ts")
    mins = int(st.session_state.get("auto_refresh_minutes") or 5)
    if not should_auto_refresh(now=now, last=last_ts, interval_minutes=mins):
        return
    try:
        label = format_query_datetime()
        st.session_state.watch_snapshots = refresh_watch_snapshots(
            st.session_state.watchlist,
            fetch_fn,
            query_label=label,
        )
        st.session_state._auto_refresh_ts = now
        st.session_state._auto_refresh_at = label
        mark_dirty()
        from src.analysis.watch_alerts import compute_watch_alerts
        from src.notify.alert_push import maybe_push_alerts_if_configured
        from src.notify.digest_push import maybe_push_after_refresh

        maybe_push_after_refresh()
        alerts = compute_watch_alerts(
            st.session_state.watchlist,
            st.session_state.watch_snapshots,
            pct_up=float(st.session_state.get("alert_pct_up") or 5.0),
            pct_down=float(st.session_state.get("alert_pct_down") or -5.0),
            score_low=float(st.session_state.get("alert_score_low") or 40.0),
            score_high=float(st.session_state.get("alert_score_high") or 65.0),
        )
        maybe_push_alerts_if_configured(alerts)
    except Exception as exc:
        st.session_state._auto_refresh_last_error = str(exc)[:120]


@st.fragment(run_every=60)
def auto_refresh_fragment(fetch_fn: Callable[..., Any]) -> None:
    _tick_auto_refresh(fetch_fn)
    err = st.session_state.pop("_auto_refresh_last_error", None)
    if err:
        st.caption(f"⚠️ 自动刷新失败：{err}")
    elif st.session_state.get("_auto_refresh_at") and st.session_state.get("auto_refresh_enabled"):
        st.caption(f"🔄 自动刷新已启用 · 上次 {st.session_state.get('_auto_refresh_at')}")
