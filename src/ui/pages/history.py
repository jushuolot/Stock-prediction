from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.df_style import show_df

from src.ui import app_core as C

from src.storage.history_store import (
    KIND_LABELS,
    filter_query_log,
    format_log_option,
    get_snapshot_by_id,
    history_path,
    load_history,
    persist_session,
    restore_snapshot,
    unique_dates_from_log,
    unique_stocks_from_log,
)
from src.analysis.trend_summary import collect_trend_points, format_trend_markdown, trend_delta
from src.analysis.battle_plan import build_battle_plan
from src.analysis.weekly_report import build_weekly_report
from src.ui.cohort_panel import render_cohort_panel
from src.util.query_time import format_query_datetime


def render() -> None:
    render_cohort_panel()
    st.divider()
    st.subheader("历史记录")
    st.caption(
        f"自动记录榜单刷新、一键分析等操作。数据在 `data/{history_path().name}`，重登后自动恢复。"
    )
    st.caption(f"文件路径：`{history_path()}`")
    log = st.session_state.get("query_log") or []
    if not log:
        st.info("暂无历史。完成榜单刷新、异动全景或异动溯源后会自动记录。")
    else:
        st.markdown("**快速检索**")
        f1, f2, f3, f4 = st.columns(4)
        dates = unique_dates_from_log(log)
        with f1:
            f_date = st.selectbox("日期", ["全部"] + dates, key="hist_filter_date")
        kinds = sorted({str(e.get("kind") or "") for e in log if e.get("kind")})
        with f2:
            f_kind = st.selectbox(
                "类型",
                ["全部"] + kinds,
                format_func=lambda k: "全部" if k == "全部" else KIND_LABELS.get(k, k),
                key="hist_filter_kind",
            )
        markets = sorted({str(e.get("market") or "") for e in log if e.get("market")})
        with f3:
            f_market = st.selectbox("市场", ["全部"] + markets, key="hist_filter_market")
        stock_opts = unique_stocks_from_log(log)
        with f4:
            f_stock_pick = st.selectbox(
                "股票（可选）",
                ["全部"] + stock_opts[:60],
                key="hist_filter_stock_pick",
            )
        f_stock_kw = st.text_input(
            "股票关键词（代码/名称，与上项可叠加）",
            placeholder="如 920161、英伟达、兆易",
            key="hist_filter_stock_kw",
        )
        stock_kw = f_stock_kw
        if f_stock_pick and f_stock_pick != "全部":
            stock_kw = f"{f_stock_pick} {stock_kw}".strip()

        filtered = filter_query_log(
            log,
            date_key=f_date,
            kind=f_kind,
            market=f_market,
            stock_kw=stock_kw,
        )
        st.caption(f"共 {len(log)} 条记录，筛选后 {len(filtered)} 条")

        weekly_md = build_weekly_report(
            log,
            st.session_state.get("watchlist") or [],
            st.session_state.get("watch_snapshots") or {},
        )
        battle_md = build_battle_plan(
            st.session_state.get("watchlist") or [],
            st.session_state.get("watch_snapshots") or {},
            query_label=format_query_datetime(),
            pct_up=float(st.session_state.get("alert_pct_up", 5.0)),
            pct_down=float(st.session_state.get("alert_pct_down", -5.0)),
            score_low=float(st.session_state.get("alert_score_low", 40.0)),
            score_high=float(st.session_state.get("alert_score_high", 65.0)),
            price_targets=st.session_state.get("price_targets"),
        )
        h1, h2 = st.columns(2)
        with h1:
            st.download_button(
                "📅 下载周报 (.md)",
                data=weekly_md.encode("utf-8"),
                file_name="分析周报.md",
                mime="text/markdown",
                key="hist_weekly_md",
                use_container_width=True,
            )
        with h2:
            st.download_button(
                "📋 今日作战清单",
                data=battle_md.encode("utf-8"),
                file_name="今日作战清单.md",
                mime="text/markdown",
                key="hist_battle_plan_dl",
                use_container_width=True,
            )

        with st.expander("📈 趋势", expanded=False):
            stock_opts_trend = unique_stocks_from_log(log)
            if stock_opts_trend:
                trend_ticker = st.selectbox(
                    "选择标的查看趋势",
                    stock_opts_trend[:40],
                    key="hist_trend_ticker",
                )
                snaps_hist = st.session_state.get("history_snapshots") or load_history().get("snapshots", [])
                points = collect_trend_points(log, snaps_hist, trend_ticker, limit=10)
                if points:
                    score_d, pct_d = trend_delta(points)
                    hints: list[str] = []
                    if pct_d is not None:
                        hints.append(f"涨跌幅 {pct_d:+.2f}%")
                    if score_d is not None:
                        hints.append(f"评分 {score_d:+.1f}")
                    if hints:
                        st.caption("区间变化：" + " · ".join(hints))
                    trend_df = pd.DataFrame(
                        [
                            {
                                "时间": p.at,
                                "涨跌幅%": f"{p.pct:+.2f}" if p.pct is not None else "—",
                                "评分": f"{p.score:.1f}" if p.score is not None else "—",
                                "说明": p.label[:50],
                            }
                            for p in points
                        ]
                    )
                    show_df(trend_df, use_container_width=True, hide_index=True)
                    st.download_button(
                        "下载趋势 (.md)",
                        data=format_trend_markdown(points, ticker=trend_ticker).encode("utf-8"),
                        file_name=f"趋势_{trend_ticker}.md",
                        mime="text/markdown",
                        key="hist_trend_md",
                    )
                else:
                    st.info("该标的暂无带评分的快照记录。")
            else:
                st.caption("历史记录中尚未识别到股票代码。")

        if filtered:
            import csv
            import io

            buf = io.StringIO()
            rows = [e for _, e in filtered]
            if rows:
                w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
                st.download_button(
                    "导出筛选结果 CSV",
                    data=buf.getvalue().encode("utf-8-sig"),
                    file_name="查询历史.csv",
                    mime="text/csv",
                    key="hist_csv_dl",
                )

        if filtered:
            show_rows = [e for _, e in filtered]
            log_df = pd.DataFrame(show_rows)
            show_cols = [
                c
                for c in (
                    "at",
                    "kind",
                    "label",
                    "market",
                    "board",
                    "stocks",
                    "count",
                    "conclusions_summary",
                )
                if c in log_df.columns
            ]
            if "kind" in log_df.columns:
                log_df = log_df.copy()
                log_df["类型"] = log_df["kind"].map(lambda k: KIND_LABELS.get(str(k), k))
                if "类型" in show_cols or "kind" in show_cols:
                    show_cols = ["at", "类型", "label", "market", "stocks", "conclusions_summary"]
                    show_cols = [c for c in show_cols if c in log_df.columns]
            show_df(log_df[show_cols], use_container_width=True, hide_index=True)

            sel = st.selectbox(
                "选择一条历史恢复",
                range(len(filtered)),
                format_func=lambda i: format_log_option(filtered[i][1]),
                key="hist_pick_restore",
            )
            entry = filtered[int(sel)][1]
        else:
            st.warning("没有符合筛选条件的记录，请放宽日期/类型/股票条件。")
            entry = None

        if entry:
            snap = get_snapshot_by_id(str(entry.get("id")))
            if snap:
                st.markdown("**该次分析结论摘要**")
                concl = snap.get("conclusions") or {}
                if concl.get("panorama_headline"):
                    st.write(f"全景龙头：{concl['panorama_headline']}")
                rep_d = concl.get("route_report")
                if rep_d:
                    st.write(f"异动溯源：{rep_d.get('title')} — {str(rep_d.get('result', ''))[:200]}")
                for row in (concl.get("industry_cluster") or [])[:5]:
                    st.caption(
                        f"· {row.get('行业')}：{str(row.get('基础市场预期', ''))[:80]} → {row.get('参考观察（人工判断）', '')}"
                    )
                for note in (concl.get("per_stock_notes") or [])[:5]:
                    st.caption(f"· {note.get('name')}：{note.get('macro_expectation', '')}")

                if st.button("恢复此记录", type="primary", key="history_restore"):
                    restore_snapshot(snap)
                    st.session_state.query_log = load_history().get("query_log", [])
                    st.session_state.history_snapshots = load_history().get("snapshots", [])
                    st.success("已恢复榜单、全景与溯源结论，请切换到对应标签页查看。")
                    st.rerun()
            else:
                st.warning("该条日志没有完整快照（可能为较早版本）。")

    if st.session_state.get("history_restored_label"):
        st.info(f"已从历史恢复：{st.session_state.history_restored_label}")

    concl_live = st.session_state.get("history_conclusions") or {}
    if concl_live and st.session_state.get("_history_restored"):
        with st.expander("当前会话中的已恢复结论", expanded=False):
            if concl_live.get("route_report"):
                rd = concl_live["route_report"]
                st.markdown(f"**{rd.get('title')}**")
                st.write(rd.get("result"))
            if concl_live.get("per_stock_notes"):
                for n in concl_live["per_stock_notes"][:8]:
                    st.caption(f"{n.get('name')}（{n.get('code')}）· {n.get('industry')} · {n.get('macro_expectation', '')}")

