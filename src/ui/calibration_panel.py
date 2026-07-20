"""预测校准面板：预测 vs 真实 K 线对比（P125）。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ui.df_style import show_df

from src.analysis.prediction_calibration import (
    build_calibration_report,
    merge_pick_logs,
)
from src.storage.cloud_pick_log import load_cloud_pick_log
from src.util.cloud_picks_loader import load_cloud_picks


def _merged_log(local_log: list) -> list[dict[str, Any]]:
    cloud = load_cloud_pick_log()
    return merge_pick_logs(local_log, cloud)


def render_calibration_panel(local_log: list, *, fetch_fn, readonly: bool) -> dict[str, Any] | None:
    """展示校准报告；返回 report dict 供扫盘权重使用。"""
    st.markdown("### 📐 预测 vs 真实")
    st.caption("每次推荐都会与后续 K 线真实涨跌对比，自动调整明日模型权重。")

    merged = _merged_log(local_log)
    if not merged:
        st.info("尚无预测记录。完成「预测明日」后会自动进入校准闭环。")
        cloud = load_cloud_picks()
        if cloud and cloud.get("calibration"):
            rep = cloud["calibration"]
            _show_report(rep)
            return rep
        return None

    cache_key = "_calibration_report"
    do_refresh = not readonly and st.button("🔄 用 K 线重算准确率", key="calibration_refresh")
    if do_refresh or st.session_state.get(cache_key) is None:
        with st.spinner("拉取 K 线，对比预测日与 D+1~D+3 真实涨跌…"):
            try:
                report = build_calibration_report(merged, fetch_fn)
                st.session_state[cache_key] = report.as_dict()
            except Exception as exc:
                st.warning(f"校准失败：{exc}")
                return st.session_state.get(cache_key)

    rep = st.session_state.get(cache_key)
    if not rep:
        cloud = load_cloud_picks()
        rep = (cloud or {}).get("calibration")
    if rep:
        _show_report(rep)
    return rep


def _show_report(rep: dict[str, Any]) -> None:
    c1, c2, c3 = st.columns(3)
    rate = rep.get("hit_rate_pct")
    c1.metric("3日命中率", f"{rate:.0f}%" if rate is not None else "—")
    avg = rep.get("avg_max_ret_pct")
    c2.metric("均最高涨幅", f"{avg:+.2f}%" if avg is not None else "—")
    c3.metric("已验证样本", str(rep.get("reviewed") or 0))

    for line in rep.get("conclusions") or []:
        st.caption(f"· {line}")

    pat = rep.get("by_pattern") or []
    if pat:
        st.markdown("**按模式准确率**")
        show_df(pd.DataFrame(pat), use_container_width=True, hide_index=True)

    recent = rep.get("recent_rows") or []
    if recent:
        st.markdown("**最近预测 vs 真实**")
        show_df(pd.DataFrame(recent), use_container_width=True, hide_index=True)

    st.download_button(
        "📥 下载校准报告 (.md)",
        data=_report_md(rep).encode("utf-8"),
        file_name="预测校准报告.md",
        mime="text/markdown",
        key="calibration_download_md",
    )


def _report_md(rep: dict[str, Any]) -> str:
    lines = ["# 预测 vs 真实 · 校准报告", ""]
    rate = rep.get("hit_rate_pct")
    if rate is not None:
        lines.append(f"- 3日命中率：**{rate:.0f}%**（样本 {rep.get('reviewed')}）")
    for c in rep.get("conclusions") or []:
        lines.append(f"- {c}")
    lines.append("")
    for row in rep.get("recent_rows") or []:
        lines.append(
            f"- {row.get('日期')} {row.get('名称')} {row.get('代码')} "
            f"{row.get('结果')} {row.get('明细')}"
        )
    lines.append("\n*非投资建议。*")
    return "\n".join(lines)
