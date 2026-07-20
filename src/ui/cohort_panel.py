"""多人选股画像 + 云端汇总展示。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ui.df_style import show_df

from src.analysis.cohort_analytics import build_cohort_insights
from src.analysis.user_pick_profile import build_user_pick_profile
from src.auth.users import auth_mode_label, current_user_id
from src.storage.cloud_contrib import load_all_contributions
from src.storage.history_store import load_history
from src.util.cloud_picks_loader import load_cohort_insights


def _personal_profile() -> dict[str, Any]:
    store = load_history()
    latest = store.get("latest") or {}
    prefs = latest.get("user_prefs") or {}
    prof = build_user_pick_profile(
        current_user_id(),
        pick_log=latest.get("pick_log") or [],
        watchlist=store.get("watchlist") or [],
        search_history=prefs.get("search_history") or [],
    )
    return prof.as_dict()


def render_cohort_panel(*, expanded: bool = True) -> None:
    st.markdown("### 👥 多人选股 · 云端汇总")
    st.caption(f"{auth_mode_label()} · 每次保存历史会自动同步你的选股画像到云端。")

    prof = _personal_profile()
    c1, c2, c3 = st.columns(3)
    c1.metric("你的风格", (prof.get("style_label") or "—")[:14])
    hr = prof.get("hit_rate_pct")
    c2.metric("你的命中率", f"{hr:.0f}%" if hr is not None else "—")
    c3.metric("推荐/自选", f"{prof.get('pick_count', 0)}/{prof.get('watch_count', 0)}")

    if prof.get("top_patterns"):
        st.caption("偏好模式：" + "、".join(prof.get("top_patterns") or []))
    if prof.get("top_codes"):
        st.caption("常关注代码：" + "、".join(prof.get("top_codes") or []))

    cohort = load_cohort_insights()
    if not cohort:
        local = load_all_contributions()
        if local:
            cohort = build_cohort_insights(local).as_dict()
    if not cohort or not cohort.get("user_count"):
        st.info("云端尚无多人汇总。配置多组密码后，各用户使用后会在每晚扫盘时合并分析。")
        return

    for line in cohort.get("summary_lines") or []:
        st.caption(f"☁️ {line}")

    users = cohort.get("users") or []
    if users:
        st.markdown("**各用户选股特点**")
        urows = []
        for u in users:
            urows.append(
                {
                    "用户": u.get("user_id"),
                    "风格": u.get("style"),
                    "命中率%": u.get("hit_rate_pct"),
                    "自选": u.get("watch_count"),
                    "推荐": u.get("pick_count"),
                    "偏好模式": "、".join(u.get("top_patterns") or [])[:24],
                }
            )
        show_df(pd.DataFrame(urows), use_container_width=True, hide_index=True)

    stocks = cohort.get("stock_consensus") or []
    if stocks:
        st.markdown("**群体关注股票汇总**")
        show_df(pd.DataFrame(stocks), use_container_width=True, hide_index=True)
