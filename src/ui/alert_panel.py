"""自选股阈值提醒 UI（P13）+ Webhook 推送（P17）+ 价格目标（P46）。"""

from __future__ import annotations

import streamlit as st

from src.analysis.watch_alerts import alerts_to_markdown, compute_watch_alerts
from src.notify.alert_push import maybe_push_alerts_if_configured, push_alerts_webhook
from src.notify.webhook import get_webhook_url
from src.storage.history_store import mark_dirty
from src.util.alert_profiles import ALERT_PROFILES, apply_alert_profile, profile_caption
from src.util.freshness_badge import normalize_stale_hours
from src.util.price_targets import normalize_price_targets, set_targets
from src.util.quiet_hours import normalize_quiet_hours, quiet_hours_caption, quiet_hours_enabled
from src.util.readonly_mode import is_readonly_mode


def _alert_params() -> dict:
    return {
        "pct_up": float(st.session_state.get("alert_pct_up", 5.0)),
        "pct_down": float(st.session_state.get("alert_pct_down", -5.0)),
        "score_low": float(st.session_state.get("alert_score_low", 40.0)),
        "score_high": float(st.session_state.get("alert_score_high", 65.0)),
        "price_targets": normalize_price_targets(st.session_state.get("price_targets") or {}),
    }


def render_alert_panel(*, watchlist: list[dict], snapshots: dict) -> list:
    alerts: list = []
    readonly = is_readonly_mode()
    with st.expander("🔔 智能提醒（涨跌幅 / 评分 / 价格目标）", expanded=False):
        if readonly:
            alerts = compute_watch_alerts(watchlist, snapshots, **_alert_params())
            if not alerts:
                st.caption("当前无触发项。")
            else:
                for a in alerts[:12]:
                    icon = {"hot": "🔥", "warn": "⚠️", "info": "ℹ️"}.get(a.level, "•")
                    st.markdown(f"{icon} **{a.name}（{a.code}）** — {a.message}")
            return alerts
        st.session_state.setdefault("alert_pct_up", 5.0)
        st.session_state.setdefault("alert_pct_down", -5.0)
        st.session_state.setdefault("alert_score_low", 40.0)
        st.session_state.setdefault("alert_score_high", 65.0)
        st.session_state.setdefault("push_webhook_on_alerts", False)
        st.session_state.setdefault("price_targets", {})
        st.session_state.setdefault("quiet_hours", {})
        st.session_state.quiet_hours = normalize_quiet_hours(st.session_state.quiet_hours)
        st.session_state.price_targets = normalize_price_targets(st.session_state.price_targets)
        st.session_state["stale_hours"] = normalize_stale_hours(
            st.session_state.get("stale_hours", 24.0)
        )
        st.caption("提醒模板（一键套用阈值）")
        prof_cols = st.columns(len(ALERT_PROFILES))
        for i, prof in enumerate(ALERT_PROFILES):
            with prof_cols[i]:
                if st.button(prof.label, key=f"alert_prof_{prof.id}", use_container_width=True):
                    apply_alert_profile(st.session_state, prof.id)
                    mark_dirty()
                    st.rerun()
        active_prof = next(
            (
                p
                for p in ALERT_PROFILES
                if float(st.session_state.alert_pct_up) == p.pct_up
                and float(st.session_state.alert_pct_down) == p.pct_down
                and float(st.session_state.alert_score_low) == p.score_low
                and float(st.session_state.alert_score_high) == p.score_high
            ),
            None,
        )
        if active_prof:
            st.caption(f"当前：{active_prof.label} · {profile_caption(active_prof)}")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.number_input("涨幅≥%", key="alert_pct_up", step=0.5)
        with c2:
            st.number_input("跌幅≤%", key="alert_pct_down", step=0.5)
        with c3:
            st.number_input("低评分≤", key="alert_score_low", step=1.0)
        with c4:
            st.number_input("高评分≥", key="alert_score_high", step=1.0)
        st.caption("价格目标（全局 stale 阈值）")
        pt1, pt2, pt3 = st.columns([2, 1, 1])
        with pt1:
            pt_code = st.selectbox(
                "设置目标价",
                options=[str(x.get("代码") or "") for x in watchlist] or [""],
                key="alert_pt_code",
            )
        with pt2:
            pt_above = st.number_input("≥ 卖出/止盈", min_value=0.0, value=0.0, step=0.01, key="alert_pt_above")
        with pt3:
            pt_below = st.number_input("≤ 买入/止损", min_value=0.0, value=0.0, step=0.01, key="alert_pt_below")
        if st.button("保存价格目标", key="alert_pt_save", use_container_width=True):
            above = pt_above if pt_above > 0 else None
            below = pt_below if pt_below > 0 else None
            st.session_state.price_targets = set_targets(
                normalize_price_targets(st.session_state.price_targets),
                pt_code,
                above=above,
                below=below,
            )
            mark_dirty()
            st.success(f"已保存 {pt_code} 价格目标。")
        targets = normalize_price_targets(st.session_state.price_targets)
        if targets:
            for tc, tv in list(targets.items())[:8]:
                parts = []
                if tv.get("above") is not None:
                    parts.append(f"≥{tv['above']:.2f}")
                if tv.get("below") is not None:
                    parts.append(f"≤{tv['below']:.2f}")
                st.caption(f"· {tc}: {' / '.join(parts)}")
        st.number_input(
            "摘要 stale 小时",
            min_value=0.5,
            max_value=168.0,
            step=0.5,
            key="stale_hours",
            help="超过此小时数未刷新摘要则显示 stale 徽章",
        )
        alerts = compute_watch_alerts(watchlist, snapshots, **_alert_params())
        wh = get_webhook_url()
        if wh:
            st.checkbox("提醒触发时自动推送 Webhook", key="push_webhook_on_alerts")
            qh = normalize_quiet_hours(st.session_state.quiet_hours)
            qh_on = st.checkbox(
                "启用静默时段（本地小时，跳过自动推送）",
                value=quiet_hours_enabled(qh),
                key="quiet_hours_enabled",
            )
            if qh_on:
                q1, q2 = st.columns(2)
                with q1:
                    qh_start = st.number_input(
                        "开始（时）",
                        min_value=0,
                        max_value=23,
                        value=int(qh["start"] if qh["start"] is not None else 22),
                        step=1,
                        key="quiet_hours_start",
                    )
                with q2:
                    qh_end = st.number_input(
                        "结束（时）",
                        min_value=0,
                        max_value=23,
                        value=int(qh["end"] if qh["end"] is not None else 8),
                        step=1,
                        key="quiet_hours_end",
                    )
                st.session_state.quiet_hours = {"start": int(qh_start), "end": int(qh_end)}
                st.caption(f"静默：{quiet_hours_caption(st.session_state.quiet_hours)}")
            else:
                st.session_state.quiet_hours = {"start": None, "end": None}
        if not alerts:
            st.caption("当前无触发项；请先「刷新全部摘要」。")
        else:
            for a in alerts[:12]:
                icon = {"hot": "🔥", "warn": "⚠️", "info": "ℹ️"}.get(a.level, "•")
                st.markdown(f"{icon} **{a.name}（{a.code}）** — {a.message}")
            md = alerts_to_markdown(alerts)
            st.download_button(
                "下载提醒 (.md)",
                data=md.encode("utf-8"),
                file_name="自选股提醒.md",
                mime="text/markdown",
                key="alert_md_dl",
                use_container_width=True,
            )
            if wh:
                if st.button("推送到 Webhook", key="alert_push_webhook", use_container_width=True):
                    with st.spinner("推送提醒中…"):
                        ok, msg = push_alerts_webhook(alerts)
                    if ok:
                        st.success(f"Webhook: ✓ {msg}")
                    else:
                        st.warning(f"Webhook: ✗ {msg}")
            last = st.session_state.get("_last_alert_push_result")
            if last:
                st.caption(f"上次提醒推送：{last}")
        if st.button("保存提醒阈值", key="alert_save_prefs", use_container_width=True):
            mark_dirty()
            st.success("阈值已保存（随会话持久化）。")
    if alerts:
        maybe_push_alerts_if_configured(alerts)
    return alerts
