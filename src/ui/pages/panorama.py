from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.df_style import show_df

from src.ui import app_core as C

from src.analysis.global_anomaly import analyze_one_mover_deep
from src.analysis.industry_recommend import build_industry_clusters
from src.analysis.timeframe_impact import slices_to_rows
from src.storage.history_store import mark_dirty
from src.storage.serialize import capital_mix_to_dict, panorama_detail_from_dict
from src.util.query_time import format_query_datetime


def render(*, embedded: bool = False) -> None:
    if not embedded:
        st.subheader("全球股市 · 异动全景")
    st.caption(
        "先在 **涨跌幅榜** 刷新榜单。快速模式用榜单快照（约 1 秒）；"
        "深度模式仅对 1 只拉 K 线/新闻（约 10–30 秒）。"
    )
    C._show_query_banner("panorama")
    movers_p = st.session_state.get("movers_df")
    if movers_p is None or movers_p.empty:
        st.info("请先在 **涨跌幅榜** 子页刷新榜单，再回来点「快速生成异动列表」。")
    else:
        st.write(
            f"当前榜单：{st.session_state.get('movers_market', 'A股')} · "
            f"{st.session_state.get('movers_board', '')} · 共 {len(movers_p)} 只"
        )
        c1, c2 = st.columns([2, 1])
        with c1:
            batch_n = st.slider("快速分析只数", 5, min(30, len(movers_p)), min(15, len(movers_p)))
        with c2:
            st.caption(f"榜单查询：{C._query_label('movers') or '—'}")

        if st.button("快速生成异动列表（推荐）", type="primary", use_container_width=True):
            q = C._stamp_query("panorama")
            movers_csv = movers_p.to_csv(index=False)
            progress = st.progress(0, text="准备中…")
            progress.progress(0.2, text=f"正在快速分析 {batch_n} 只（榜单快照，无网络）…")
            summaries, details = C._cached_panorama_batch(
                movers_csv,
                str(st.session_state.get("movers_market") or "A股"),
                int(batch_n),
                q,
            )
            progress.progress(1.0, text="完成")
            st.session_state["panorama_summary"] = pd.DataFrame(summaries)
            st.session_state["panorama_details"] = [
                panorama_detail_from_dict(d) for d in details
            ]
            st.session_state["panorama_fp"] = C._movers_csv_fingerprint(movers_p)
            cluster = build_industry_clusters(summaries)
            st.session_state["panorama_industry_cluster"] = cluster.to_dict("records") if not cluster.empty else []
            progress.empty()
            mark_dirty()
            C._save_history(
                log_kind="panorama_fast",
                log_label=f"{st.session_state.get('movers_market')} {st.session_state.get('movers_board')} 异动全景×{batch_n}",
                market=str(st.session_state.get("movers_market") or ""),
                board=str(st.session_state.get("movers_board") or ""),
                count=int(batch_n),
            )

        summary = st.session_state.get("panorama_summary")
        details = [
            panorama_detail_from_dict(d)
            for d in (st.session_state.get("panorama_details") or [])
        ]
        if summary is not None and not summary.empty:
            st.markdown("### 异动列表（快速 · 含资金推测占比）")
            show_df(summary, use_container_width=True, hide_index=True)
            st.caption(
                f"本次分析：{C._query_label('panorama') or format_query_datetime()} · "
                f"模式：快速（榜单快照）"
            )

            st.markdown("### 按行业 · 基础市场预期与参考观察")
            cluster = build_industry_clusters(summary.to_dict("records"))
            if not cluster.empty:
                show_df(cluster, use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("### 单只明细 / 深度分析")
            pick_names = [f"{d['name']}（{d['code']}）" for d in details]
            sel_i = st.selectbox("选择标的", range(len(pick_names)), format_func=lambda i: pick_names[i])
            one = details[int(sel_i)]
            deep_intra = st.checkbox("深度含分/时日内线", value=False, key="panorama_deep_intra")

            if st.button("深度分析选中 1 只", type="secondary", use_container_width=True):
                row = movers_p.loc[movers_p["代码"].astype(str) == str(one["code"])].iloc[0].to_dict()
                q = C._stamp_query("panorama")
                with st.spinner(f"正在深度分析 {one['name']}（约 10–30 秒）…"):
                    deep_a = analyze_one_mover_deep(
                        row,
                        market=str(st.session_state.get("movers_market") or "A股"),
                        query_label=q,
                        include_intraday=deep_intra,
                    )
                details[int(sel_i)] = {
                    "code": deep_a.code,
                    "name": deep_a.name,
                    "market": deep_a.market,
                    "kind": deep_a.kind,
                    "anomaly_score": deep_a.anomaly_score,
                    "capital": capital_mix_to_dict(deep_a.capital),
                    "timeframes": deep_a.timeframes,
                    "context": deep_a.context,
                    "news": deep_a.news,
                    "snapshot": deep_a.snapshot,
                    "mode": deep_a.mode,
                }
                st.session_state["panorama_details"] = [
                    panorama_detail_from_dict(d) for d in details
                ]
                summary_rows = summary.to_dict("records")
                summary_rows[int(sel_i)] = deep_a.to_summary_dict()
                st.session_state["panorama_summary"] = pd.DataFrame(summary_rows)
                one = st.session_state["panorama_details"][int(sel_i)]
                mark_dirty()
                C._save_history(
                    log_kind="panorama_deep",
                    log_label=f"深度分析 {one['name']}（{one['code']}）",
                )
                st.success("深度分析完成，明细已更新。")

            mode_label = "深度" if one.get("mode") == "deep" else "快速"
            st.markdown(
                f"**{one['name']}（{one['code']}）** · {one['market']} · "
                f"异动分 {one['anomaly_score']:.1f} · {mode_label}"
            )
            mix, cap_notes = C._capital_mix_for_chart(one.get("capital"))
            fig_pie = go.Figure(
                data=[go.Pie(labels=list(mix.keys()), values=list(mix.values()), hole=0.35)]
            )
            fig_pie.update_layout(title="资金结构推测占比", height=320, margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
            for n in cap_notes:
                st.caption(f"· {n}")

            st.markdown("**多周期变化及对股价影响**")
            show_df(
                pd.DataFrame(slices_to_rows(one["timeframes"])),
                use_container_width=True,
                hide_index=True,
            )
            if one.get("mode") != "deep":
                st.info("当前为快速快照。需要日/周/月 K 线与新闻请点「深度分析选中 1 只」。")

            st.markdown("**时事 / 经营 / 上下游 / 行业**")
            for line in one["context"].get("摘要") or []:
                st.markdown(line)
            st.info(one["context"].get("供应链提示") or "")

            if one.get("news"):
                st.markdown("**相关新闻**")
                for n in one["news"][:8]:
                    t = n.get("标题") or ""
                    link = n.get("链接") or ""
                    if link:
                        st.markdown(f"- [{t}]({link})")
                    else:
                        st.write(f"- {t}")

            if st.button("将此标的载入「异动溯源」", key="panorama_to_insight"):
                st.session_state["insight_pick"] = one["snapshot"]
                st.session_state["insight_board"] = st.session_state.get("movers_board", "")
                st.session_state["insight_auto_days"] = 90
                st.session_state["insight_pending"] = True
                st.success("已载入，请切换到「异动溯源」页。")

