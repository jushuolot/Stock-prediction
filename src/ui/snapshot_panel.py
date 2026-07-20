"""全市场快照对比面板（P126–P127）。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ui.df_style import show_df

from src.analysis.market_snapshot import DIFF_JSON, FOLLOWUPS_JSON, WEEKLY_JSON, weekly_summary_to_markdown
from src.util.cloud_picks_loader import load_cloud_picks


def _load_diff() -> dict[str, Any] | None:
    cloud = load_cloud_picks()
    if cloud and cloud.get("snapshot_diff"):
        return cloud["snapshot_diff"]
    if DIFF_JSON.is_file():
        try:
            import json

            return json.loads(DIFF_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _load_weekly() -> dict[str, Any] | None:
    cloud = load_cloud_picks()
    if cloud and cloud.get("weekly_summary"):
        return cloud["weekly_summary"]
    if WEEKLY_JSON.is_file():
        try:
            import json

            return json.loads(WEEKLY_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _load_followups() -> list[dict[str, Any]]:
    cloud = load_cloud_picks()
    if cloud and cloud.get("deep_followups"):
        return list(cloud["deep_followups"])
    if FOLLOWUPS_JSON.is_file():
        try:
            import json

            data = json.loads(FOLLOWUPS_JSON.read_text(encoding="utf-8"))
            return list(data.get("items") or [])
        except Exception:
            pass
    return []


def render_snapshot_panel() -> None:
    st.markdown("### 📸 全市场快照对比")
    st.caption("轻量快照 → 次日对比 → 自动精选再分析（仅少数标的跑深度）。")

    weekly = _load_weekly()
    followups = _load_followups()
    cloud = load_cloud_picks() or {}
    cal = cloud.get("calibration")

    if weekly:
        st.info(f"**周汇总：** {weekly.get('headline') or '—'}")
        rate = weekly.get("week_hit_rate_pct")
        if rate is not None:
            st.caption(f"本周快照验证命中率 **{rate:.0f}%**（{weekly.get('week_checks')} 次）")
        md = weekly_summary_to_markdown(weekly, calibration=cal, followups=followups)
        st.download_button(
            "📥 下载周成果汇总 (.md)",
            data=md.encode("utf-8"),
            file_name="周成果汇总.md",
            mime="text/markdown",
            key="weekly_summary_download",
        )

    if followups:
        st.markdown("**值得再分析（系统自动精选）**")
        for i, f in enumerate(followups):
            cols = st.columns([3, 1])
            with cols[0]:
                st.caption(
                    f"**{f.get('name')}** `{f.get('code')}` · {f.get('tag')} · "
                    f"**{f.get('verdict')}** · {f.get('one_line')}"
                )
            with cols[1]:
                if st.button("查看", key=f"snap_follow_{i}_{f.get('code')}", use_container_width=True):
                    st.session_state.garden_lens_kw = str(f.get("code") or "")
                    st.session_state._garden_lens_pending_kw = str(f.get("code") or "")
                    st.rerun()

    diff = _load_diff()
    if not diff:
        if not followups:
            st.caption("尚无两日快照对比；第二个交易日收盘后会自动生成。")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("对比样本", str(diff.get("compared") or 0))
    avg = diff.get("avg_pct_delta")
    c2.metric("均涨跌变化", f"{avg:+.2f}%" if avg is not None else "—")
    c3.metric("快照日", f"{diff.get('prev_date')}→{diff.get('curr_date')}")

    for line in diff.get("conclusions") or []:
        st.caption(f"· {line}")

    checks = diff.get("pick_checks") or []
    if checks:
        st.markdown("**昨日预测 vs 今日快照**")
        show_df(pd.DataFrame(checks), use_container_width=True, hide_index=True)

    movers = diff.get("movers") or []
    if movers:
        st.markdown("**异动前列**")
        show_df(pd.DataFrame(movers[:8]), use_container_width=True, hide_index=True)
