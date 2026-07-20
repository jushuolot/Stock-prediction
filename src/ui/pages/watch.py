from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui.df_style import show_df

from src.ui import app_core as C

from src.analysis.brief_merge import (
    build_merged_briefs_html,
    build_merged_briefs_markdown,
    collect_briefs_for_watchlist,
)
from src.analysis.battle_plan import build_battle_plan
from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.risk_radar import compute_risk_radar, risk_radar_markdown
from src.analysis.mover_insight import build_action_route_report
from src.analysis.quick_analyze import batch_run_quick_analysis, refresh_watch_snapshots, run_quick_analysis
from src.analysis.signals import score_stock
from src.providers import eastmoney
from src.providers.eastmoney import KLINE_PERIOD_UI, is_intraday_kline
from src.providers.news_feed import fetch_aggregated_news
from src.storage.history_store import mark_dirty
from src.storage.serialize import route_report_from_session
from src.analysis.compare_stocks import compare_table_rows, compare_to_markdown, compare_two_stocks
from src.analysis.sector_heatmap import aggregate_sector_distribution, sector_bar_values, sector_distribution_rows
from src.analysis.similar_pick import similar_pick_rows, suggest_similar_picks
from src.ui.alert_panel import render_alert_panel
from src.ui.simple_result import plain_score_label, render_analysis_done, render_stock_verdict_card
from src.ui.auto_refresh import auto_refresh_fragment, render_auto_refresh_controls
from src.ui.currency_tool import render_floating_currency_tool
from src.ui.dashboard_panel import render_dashboard_panel
from src.ui.industry_compare import show_industry_compare_block
from src.ui.pro_chart import (
    CHART_INDICATORS,
    DEFAULT_VISIBLE_BARS,
    MAX_VISIBLE_BARS,
    MIN_VISIBLE_BARS,
    PLOTLY_CHART_CONFIG,
    build_pro_chart_multipane,
    last_bar_stats,
)
from src.ui.readable_report_panel import build_and_store_brief, render_readable_brief_panel
from src.ui.sector_alert_panel import render_sector_linkage_panel
from src.ui.speech_summary import render_speech_button
from src.ui.stock_plates_panel import render_stock_plates_panel
from src.util.currency import currency_display, normalize_watchlist
from src.util.data_date_label import (
    build_kline_caption,
    data_lag_hint,
    format_trade_date_cn,
    metric_date_suffix,
    parse_bar_date,
    snapshot_time_label,
    today_label_cn,
)
from src.util.query_time import format_data_range, format_query_datetime
from src.util.score_badge import pct_badge, score_badge
from src.util.watchlist_export import filter_watchlist, sort_watchlist
from src.util.watchlist_csv_export import watchlist_table_to_csv_bytes
from src.util.recent_viewed import (
    RECENT_CHIP_DISPLAY,
    RECENT_CHIP_ROW,
    chip_label,
    normalize_recent_viewed,
    push_recent_viewed,
    push_recent_viewed_many,
)
from src.util.watch_groups import (
    assign_ticker_to_group,
    filter_watchlist_by_group,
    group_names,
    groups_for_ticker,
    normalize_watch_groups,
)
from src.util.batch_watch_ops import (
    batch_add_to_group,
    batch_remove_from_groups,
    batch_remove_from_watchlist,
    codes_in_watchlist,
)
from src.util.watch_notes import (
    get_note,
    normalize_watch_notes,
    remove_tickers_notes,
    set_note,
)
from src.util.price_targets import get_targets, normalize_price_targets, set_targets
from src.util.watchlist_backup import (
    apply_backup_merge,
    backup_to_json_bytes,
    build_watch_backup,
    parse_backup_bytes,
)
from src.util.watchlist_csv_import import apply_csv_import
from src.util.readonly_mode import is_readonly_mode
from src.util.watch_sort import (
    apply_watch_sort_to_session,
    normalize_watch_sort,
    prefs_from_ui,
    SORT_UI_OPTIONS,
)
from src.util.freshness_badge import freshness_badge, normalize_stale_hours
from src.util.watch_weights import (
    get_weight,
    normalize_watch_weights,
    pie_slices_for_watchlist,
    set_weight,
)
from src.util.pinned_tickers import (
    apply_pinned_order,
    is_pinned,
    normalize_pinned_tickers,
    pin_ticker,
    unpin_ticker,
)
from src.util.fetch_failures_summary import render_fetch_failures_summary
from src.util.retry_fetch_ui import (
    failed_tickers,
    refresh_one_snapshot,
    retry_button_key,
)
from src.analysis.trend_summary import collect_trend_points, format_trend_markdown, trend_delta
from src.analysis.contribution import contribution_table_rows
from src.analysis.portfolio_health import compute_portfolio_health, portfolio_health_markdown
from src.analysis.sector_relative import (
    compute_sector_relative,
    sector_relative_for_ticker,
    sector_relative_table_rows,
)
from src.analysis.sector_leader import (
    compute_sector_leaders,
    sector_leader_table_rows,
)
from src.analysis.institutional_onepager import build_institutional_onepager
from src.analysis.watch_alerts import compute_watch_alerts
from src.analysis.priority_queue import (
    format_priority_section,
    priority_table_rows,
    rank_watchlist_priority,
)
from src.export.priority_bundle import (
    build_priority_export_bundle_md,
    build_priority_export_bundle_zip,
)
from src.util.watch_expander_nav import watch_section_expanded


def _watchlist_display_rows(watchlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snaps = st.session_state.get("watch_snapshots") or {}
    stale_h = normalize_stale_hours(st.session_state.get("stale_hours", 24.0))
    rows: list[dict[str, Any]] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snaps.get(code) or {}
        pct = snap.get("pct")
        score = snap.get("score")
        stale = freshness_badge(snap.get("updated_at"), stale_hours=stale_h)
        verdict = plain_score_label(score)
        rows.append(
            {
                "名称": item.get("名称"),
                "代码": code,
                "结论": verdict,
                "涨跌幅%": pct_badge(pct) if pct is not None else "—",
                "评分": score_badge(score) if score is not None else "—",
                "摘要时间": snapshot_time_label(snap.get("updated_at")),
                "新鲜度": stale or "✓",
                "一句话": snap.get("one_line") or "—",
                "货币": item.get("货币"),
                "类型": item.get("类型"),
                "市场": item.get("市场"),
            }
        )
    return rows


def _record_recent_viewed(code: str, name: str = "") -> None:
    old = normalize_recent_viewed(st.session_state.get("recent_viewed"))
    new = push_recent_viewed(old, code=code, name=name)
    if new != old:
        st.session_state.recent_viewed = new
        mark_dirty()


def _on_watch_code_change() -> None:
    code = str(st.session_state.get("watch_code") or "").strip()
    if not code:
        return
    item = next(
        (x for x in (st.session_state.get("watchlist") or []) if str(x.get("代码") or "") == code),
        None,
    )
    name = str(item.get("名称") or code) if item else code
    _record_recent_viewed(code, name)


def _execute_quick_analysis(item: dict[str, Any], code: str) -> None:
    """一键分析：更新快照、简报、行动路线。"""
    _record_recent_viewed(code, str(item.get("名称") or code))
    q_label = C._stamp_query("watch")
    result = run_quick_analysis(item, C._fetch_one, query_label=q_label)
    st.session_state.watch_snapshots[code] = result.snapshot.as_dict()
    st.session_state["route_report"] = result.route_report
    st.session_state["insight_pick"] = {
        "代码": code,
        "名称": item.get("名称"),
        "市场": item.get("市场"),
    }
    st.session_state[f"brief_md_{code}"] = result.brief_md
    if result.fin_data and result.fin_data.get("ok"):
        st.session_state[f"watch_fin_{code}"] = True
    mark_dirty()
    C._save_history(
        log_kind="insight",
        log_label=f"一键分析 {item.get('名称')}",
        conclusions_summary=result.snapshot.one_line[:120],
    )
    render_analysis_done(
        name=str(item.get("名称") or code),
        code=code,
        score=result.score.total if result.score else result.snapshot.score,
        pct=result.snapshot.pct,
        one_line=result.snapshot.one_line,
    )


def _render_quick_analysis_zone(
    display_wl: list[dict[str, Any]],
    *,
    readonly: bool,
) -> tuple[str | None, dict[str, Any] | None]:
    """自选股表格下方：选股 + 大号一键分析按钮。"""
    codes = [str(x.get("代码") or "") for x in display_wl if x.get("代码")]
    if not codes:
        return None, None
    st.divider()
    st.markdown("### ⚡ 一键分析（在这里点）")
    st.caption("选好股票 → 点下面红色按钮，自动出结论、简报和行动路线（约 10–60 秒）。")
    if "watch_code" not in st.session_state or st.session_state.watch_code not in codes:
        st.session_state.watch_code = codes[0]
    code = st.selectbox(
        "选择要分析的股票",
        options=codes,
        key="watch_code",
        on_change=_on_watch_code_change,
    )
    item = next((x for x in display_wl if str(x.get("代码") or "") == code), None)
    if not item:
        return code, None
    snap_sel = (st.session_state.get("watch_snapshots") or {}).get(code) or {}
    render_stock_verdict_card(
        name=str(item.get("名称") or code),
        code=code,
        score=snap_sel.get("score"),
        pct=snap_sel.get("pct"),
        one_line=str(snap_sel.get("one_line") or ""),
    )
    if readonly:
        st.caption("只读模式：不可运行一键分析。")
    else:
        c_qa, c_rf = st.columns([3, 1])
        with c_qa:
            if st.button(
                "⚡ 一键分析",
                type="primary",
                key="watch_quick",
                use_container_width=True,
            ):
                try:
                    with st.spinner("并行拉取行情、新闻、财务对比并生成简报…"):
                        _execute_quick_analysis(item, code)
                except Exception as exc:
                    st.error(f"一键分析失败：{exc}")
        with c_rf:
            if st.button("🔄 刷新这只", key="watch_refresh_one", use_container_width=True):
                new_snap, ok = refresh_one_snapshot(
                    item,
                    C._fetch_one,
                    query_label=C._stamp_query("watch"),
                )
                if "watch_snapshots" not in st.session_state:
                    st.session_state.watch_snapshots = {}
                st.session_state.watch_snapshots[code] = new_snap
                mark_dirty()
                if ok:
                    st.success("摘要已更新")
                else:
                    st.warning("拉取失败，请重试")
                st.rerun()
    return code, item


def _render_recent_viewed_chips() -> None:
    recent = normalize_recent_viewed(st.session_state.get("recent_viewed"))
    if not recent:
        return
    shown = recent[:RECENT_CHIP_DISPLAY]
    st.caption(f"最近查看（最新在左，共 {len(recent)} 只）")
    for row_start in range(0, len(shown), RECENT_CHIP_ROW):
        chunk = shown[row_start : row_start + RECENT_CHIP_ROW]
        cols = st.columns(len(chunk))
        for i, entry in enumerate(chunk):
            with cols[i]:
                idx = row_start + i
                if st.button(
                    chip_label(entry),
                    key=f"recent_viewed_{idx}_{entry.get('code')}",
                    use_container_width=True,
                ):
                    st.session_state.watch_code = entry["code"]
                    _record_recent_viewed(entry["code"], entry.get("name", entry["code"]))
                    st.rerun()


def render() -> None:
    st.subheader("自选分析")
    st.caption(
        "**三步：** ① 表格看自选 → ② 在 **「⚡ 一键分析」** 区选股票点红按钮 "
        "→ ③ 往下看 K 线与简报下载。"
    )
    _render_recent_viewed_chips()
    C._show_query_banner("watch", extra=f"今天 {today_label_cn()}")
    readonly = is_readonly_mode()
    if st.session_state.watchlist:
        st.session_state.watchlist = normalize_watchlist(st.session_state.watchlist)
    if not st.session_state.watchlist:
        st.info("还没有自选股：请打开 **② 发现标的**，搜到后点 **加入自选**。")
    else:
        snaps_early = st.session_state.get("watch_snapshots") or {}
        render_dashboard_panel(
            watchlist=st.session_state.watchlist,
            snapshots=snaps_early,
            pct_up=float(st.session_state.get("alert_pct_up", 5.0)),
            pct_down=float(st.session_state.get("alert_pct_down", -5.0)),
            score_low=float(st.session_state.get("alert_score_low", 40.0)),
            score_high=float(st.session_state.get("alert_score_high", 65.0)),
            stale_hours=float(st.session_state.get("stale_hours", 24.0)),
        )
        c_refresh, c_hint = st.columns([1, 2])
        with c_refresh:
            if readonly:
                st.caption("只读模式：不可刷新摘要。")
            elif st.button("刷新全部摘要", key="watch_refresh_all", use_container_width=True):
                with st.spinner("正在批量拉取日 K 与评分…"):
                    st.session_state.watch_snapshots = refresh_watch_snapshots(
                        st.session_state.watchlist,
                        C._fetch_one,
                        query_label=C._stamp_query("watch"),
                    )
                    mark_dirty()
                st.success("自选股摘要已更新。")
        with c_hint:
            st.caption("摘要含涨跌幅、评分、一句话；完整分析请对单标的点「一键分析」。")

        snaps = st.session_state.get("watch_snapshots") or {}
        if snaps and not readonly:
            render_fetch_failures_summary(st.session_state.watchlist, snaps)
        groups = normalize_watch_groups(st.session_state.get("watch_groups") or {})
        st.session_state.watch_groups = groups
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            filter_kw = st.text_input("筛选", key="watch_filter", placeholder="名称 / 代码 / 市场")
        with f2:
            group_opts = ["全部"] + group_names(groups)
            filter_group = st.selectbox("分组", group_opts, key="watch_filter_group")
        ws_prefs = normalize_watch_sort(st.session_state.get("watch_sort") or {})
        if "watch_sort_by" not in st.session_state:
            ui_init = apply_watch_sort_to_session(ws_prefs)
            st.session_state.watch_sort_by = ui_init["by_ui"]
            st.session_state.watch_sort_desc = ui_init["desc"]
        with f3:
            sort_by = st.selectbox("排序", SORT_UI_OPTIONS, key="watch_sort_by")
        with f4:
            sort_desc = st.checkbox("降序", key="watch_sort_desc")
        new_ws = prefs_from_ui(sort_by, sort_desc)
        if new_ws != ws_prefs:
            st.session_state.watch_sort = new_ws
            mark_dirty()
        else:
            st.session_state.watch_sort = new_ws
        grouped_wl = filter_watchlist_by_group(st.session_state.watchlist, groups, filter_group)
        filtered_wl = filter_watchlist(grouped_wl, filter_kw)
        display_wl = sort_watchlist(
            filtered_wl,
            snaps,
            by=sort_by,
            descending=sort_desc,
        )
        pinned = normalize_pinned_tickers(st.session_state.get("pinned_tickers") or [])
        st.session_state.pinned_tickers = pinned
        display_wl = apply_pinned_order(display_wl, pinned)
        picked_code: str | None = None
        picked_item: dict[str, Any] | None = None
        wl_main = pd.DataFrame(_watchlist_display_rows(display_wl))
        show_cols_main = [
            c
            for c in [
                "名称", "代码", "结论", "涨跌幅%", "评分", "摘要时间", "一句话", "新鲜度", "货币", "类型", "市场"
            ]
            if c in wl_main.columns
        ]
        st.markdown("**你的自选股一览**（绿=偏强 · 红=偏弱 · 黄=中性）")
        show_df(
            wl_main[show_cols_main] if show_cols_main else wl_main,
            use_container_width=True,
            hide_index=True,
            column_config={
                "结论": st.column_config.TextColumn("结论", help="偏强/中性/偏弱/待分析"),
                "货币": st.column_config.TextColumn("货币", help="报价货币：A股 CNY / 港股 HKD / 美股 USD"),
                "一句话": st.column_config.TextColumn("一句话", width="large"),
            },
        )
        picked_code, picked_item = _render_quick_analysis_zone(display_wl, readonly=readonly)
        notes = normalize_watch_notes(st.session_state.get("watch_notes") or {})
        csv_bytes = watchlist_table_to_csv_bytes(
            display_wl,
            snaps,
            watch_notes=notes,
            watch_groups=groups,
        )
        if csv_bytes:
            st.download_button(
                "📊 导出 CSV",
                data=csv_bytes,
                file_name="自选股.csv",
                mime="text/csv",
                key="watch_csv_dl",
                use_container_width=True,
            )

        backup_payload = build_watch_backup(
            watchlist=st.session_state.watchlist,
            watch_snapshots=snaps,
            watch_groups=groups,
            watch_notes=notes,
        )
        b1, b2, b3 = st.columns(3)
        with b1:
            st.download_button(
                "💾 下载 JSON 备份",
                data=backup_to_json_bytes(backup_payload),
                file_name="自选股备份.json",
                mime="application/json",
                key="watch_json_backup_dl",
                use_container_width=True,
            )
        with b2:
            if readonly:
                st.caption("只读模式：不可导入备份。")
            else:
                uploaded = st.file_uploader(
                    "导入 JSON 备份（合并）",
                    type=["json"],
                    key="watch_json_backup_ul",
                )
                if uploaded is not None:
                    if st.button("确认合并导入", key="watch_json_backup_apply", use_container_width=True):
                        try:
                            raw = uploaded.getvalue()
                            backup = parse_backup_bytes(raw)
                            wl, merged_snaps, merged_groups, merged_notes, stats = apply_backup_merge(
                                watchlist=st.session_state.watchlist,
                                watch_snapshots=snaps,
                                watch_groups=groups,
                                watch_notes=notes,
                                backup=backup,
                            )
                            st.session_state.watchlist = wl
                            st.session_state.watch_snapshots = merged_snaps
                            st.session_state.watch_groups = merged_groups
                            st.session_state.watch_notes = merged_notes
                            mark_dirty()
                            C._save_history(log_kind="watchlist", log_label="导入 JSON 备份")
                            st.success(
                                f"已合并：新增 {stats['watchlist_added']} 只自选，"
                                f"快照 {stats['snapshots_merged']} 条，分组 {stats['groups_merged']} 组。"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"导入失败：{e}")
        with b3:
            if readonly:
                st.caption("只读模式：不可导入 CSV。")
            else:
                csv_upload = st.file_uploader(
                    "导入 CSV（代码列，合并）",
                    type=["csv"],
                    key="watch_csv_import_ul",
                )
                if csv_upload is not None:
                    if st.button("确认 CSV 合并导入", key="watch_csv_import_apply", use_container_width=True):
                        try:
                            wl, stats = apply_csv_import(
                                st.session_state.watchlist,
                                csv_upload.getvalue(),
                            )
                            st.session_state.watchlist = wl
                            mark_dirty()
                            C._save_history(log_kind="watchlist", log_label=f"CSV 导入 {stats['added']} 只")
                            st.success(
                                f"CSV 已合并：解析 {stats['parsed']} 条，"
                                f"新增 {stats['added']} 只，"
                                f"重复跳过 {stats['duplicates']} 只。"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"CSV 导入失败：{e}")

        if not readonly:
            with st.expander("📌 置顶", expanded=False):
                pin_codes = [
                    str(x.get("代码") or "")
                    for x in st.session_state.watchlist
                    if x.get("代码")
                ]
                if pin_codes:
                    pick_pin = st.selectbox("选择标的", pin_codes, key="watch_pin_pick")
                    p1, p2 = st.columns(2)
                    with p1:
                        if st.button("置顶", key="watch_pin_add", use_container_width=True):
                            st.session_state.pinned_tickers = pin_ticker(pinned, pick_pin)
                            mark_dirty()
                            st.rerun()
                    with p2:
                        if st.button(
                            "取消置顶",
                            key="watch_pin_remove",
                            use_container_width=True,
                            disabled=not is_pinned(pinned, pick_pin),
                        ):
                            st.session_state.pinned_tickers = unpin_ticker(pinned, pick_pin)
                            mark_dirty()
                            st.rerun()
                    if pinned:
                        st.caption("已置顶：" + "、".join(pinned))
                else:
                    st.caption("暂无自选股可置顶。")

        if not readonly:
            with st.expander("🏷 分组管理", expanded=False):
                new_group = st.text_input("新建分组名", key="watch_new_group", placeholder="如 核心持仓")
                if st.button("创建分组", key="watch_create_group", disabled=not new_group.strip()):
                    gname = new_group.strip()
                    if gname not in groups:
                        groups[gname] = []
                        st.session_state.watch_groups = groups
                        mark_dirty()
                        st.rerun()
                codes_all = [str(x.get("代码") or "") for x in st.session_state.watchlist if x.get("代码")]
                if codes_all and group_names(groups):
                    pick_code = st.selectbox("选择标的", codes_all, key="watch_group_pick_code")
                    pick_group = st.selectbox(
                        "加入分组",
                        group_names(groups),
                        key="watch_group_pick_group",
                    )
                    if st.button("加入分组", key="watch_group_assign", use_container_width=True):
                        st.session_state.watch_groups = assign_ticker_to_group(
                            groups, ticker=pick_code, group_name=pick_group
                        )
                        mark_dirty()
                        st.success(f"{pick_code} 已加入「{pick_group}」")
                        st.rerun()
                    assigned = groups_for_ticker(groups, pick_code)
                    if assigned:
                        st.caption(f"当前分组：{'、'.join(assigned)}")
                elif not group_names(groups):
                    st.caption("先创建分组，再把标的加入。")
        else:
            codes_all = [str(x.get("代码") or "") for x in st.session_state.watchlist if x.get("代码")]

        with st.expander("📈 趋势", expanded=False):
            trend_codes = [str(x.get("代码") or "") for x in display_wl if x.get("代码")] or codes_all
            if trend_codes:
                trend_code = st.selectbox("查看标的", trend_codes, key="watch_trend_code")
                log = st.session_state.get("query_log") or []
                snaps_hist = st.session_state.get("history_snapshots") or []
                points = collect_trend_points(log, snaps_hist, trend_code, limit=8)
                if points:
                    score_d, pct_d = trend_delta(points)
                    hints: list[str] = []
                    if pct_d is not None:
                        hints.append(f"涨跌幅 {pct_d:+.2f}%")
                    if score_d is not None:
                        hints.append(f"评分 {score_d:+.1f}")
                    if hints:
                        st.caption("最近区间变化（新→旧）：" + " · ".join(hints))
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
                        data=format_trend_markdown(points, ticker=trend_code).encode("utf-8"),
                        file_name=f"趋势_{trend_code}.md",
                        mime="text/markdown",
                        key="watch_trend_md",
                        use_container_width=True,
                    )
                else:
                    st.info("暂无该标的的历史评分/涨跌幅快照，请先「一键分析」或「刷新全部摘要」。")
            else:
                st.caption("添加自选股后可查看分析趋势。")

        if snaps:
            q_watch = C._query_label("watch") or format_query_datetime()
            alert_kw = dict(
                pct_up=float(st.session_state.get("alert_pct_up", 5.0)),
                pct_down=float(st.session_state.get("alert_pct_down", -5.0)),
                score_low=float(st.session_state.get("alert_score_low", 40.0)),
                score_high=float(st.session_state.get("alert_score_high", 65.0)),
                price_targets=st.session_state.get("price_targets"),
            )
            watch_alerts = compute_watch_alerts(display_wl, snaps, **alert_kw)
            priority_ranks = rank_watchlist_priority(
                display_wl,
                snaps,
                alerts=watch_alerts,
                stale_hours=float(st.session_state.get("stale_hours", 24.0)),
                brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                **alert_kw,
            )
            digest = build_watchlist_digest(
                display_wl,
                snaps,
                query_label=q_watch,
                watch_notes=notes,
                alerts=watch_alerts,
            )
            battle_md = build_battle_plan(
                display_wl,
                snaps,
                query_label=q_watch,
                alerts=watch_alerts,
                **alert_kw,
            )
            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "📋 下载今日自选股速览 (.md)",
                    data=digest.encode("utf-8"),
                    file_name="自选股速览.md",
                    mime="text/markdown",
                    key="watch_digest_dl",
                    use_container_width=True,
                )
            with d2:
                st.download_button(
                    "📋 今日作战清单",
                    data=battle_md.encode("utf-8"),
                    file_name="今日作战清单.md",
                    mime="text/markdown",
                    key="watch_battle_plan_dl",
                    use_container_width=True,
                )
            if priority_ranks:
                top_priority = priority_ranks[0]
                bundle_md = build_priority_export_bundle_md(
                    display_wl,
                    snaps,
                    priority=top_priority,
                    ranks=priority_ranks,
                    query_label=q_watch,
                    alerts=watch_alerts,
                    watch_notes=notes,
                    query_log=st.session_state.get("query_log") or [],
                    history_snapshots=st.session_state.get("history_snapshots") or [],
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                    stale_hours=float(st.session_state.get("stale_hours", 24.0)),
                    **alert_kw,
                )
                bundle_zip, bundle_zip_name = build_priority_export_bundle_zip(
                    display_wl,
                    snaps,
                    priority=top_priority,
                    ranks=priority_ranks,
                    query_label=q_watch,
                    alerts=watch_alerts,
                    watch_notes=notes,
                    query_log=st.session_state.get("query_log") or [],
                    history_snapshots=st.session_state.get("history_snapshots") or [],
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                    stale_hours=float(st.session_state.get("stale_hours", 24.0)),
                    **alert_kw,
                )
                b_md, b_zip = st.columns(2)
                with b_md:
                    st.download_button(
                        "📦 合并导出 (.md)",
                        data=bundle_md.encode("utf-8"),
                        file_name=f"合并导出_{top_priority.code}.md",
                        mime="text/markdown",
                        key="watch_bundle_md_dl",
                        use_container_width=True,
                    )
                with b_zip:
                    st.download_button(
                        "📦 合并导出 (.zip)",
                        data=bundle_zip,
                        file_name=bundle_zip_name,
                        mime="application/zip",
                        key="watch_bundle_zip_dl",
                        use_container_width=True,
                    )
                st.caption(
                    f"合并包含作战清单 + 速览 + 优先标的 **{top_priority.name}（{top_priority.code}）** 一页纸。"
                )

            with st.expander(
                "📋 作战清单",
                expanded=watch_section_expanded(st.session_state, "battle_plan", default=False),
            ):
                preview = battle_md if len(battle_md) <= 2400 else battle_md[:2400] + "\n\n…"
                st.markdown(preview)
                st.caption("完整版请点上方「📋 今日作战清单」下载。")

            with st.expander(
                "🎯 今日优先关注",
                expanded=watch_section_expanded(
                    st.session_state,
                    "priority_queue",
                    default=bool(priority_ranks and priority_ranks[0].score > 0),
                ),
            ):
                if priority_ranks:
                    st.markdown(format_priority_section(priority_ranks))
                    show_df(
                        pd.DataFrame(priority_table_rows(priority_ranks)),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.caption("暂无优先排序，请先刷新全部摘要。")

        def _brief_for_code(c: str) -> str | None:
            v = st.session_state.get(f"brief_md_{c}")
            return str(v) if v else None

        briefs = collect_briefs_for_watchlist(display_wl, _brief_for_code)
        if briefs:
            q_merge = C._query_label("watch") or format_query_datetime()
            merged_md = build_merged_briefs_markdown(
                display_wl, briefs, query_label=q_merge
            )
            merged_html = build_merged_briefs_html(
                display_wl, briefs, query_label=q_merge
            )
            m1, m2 = st.columns(2)
            with m1:
                st.download_button(
                    "📚 下载分析合集 (.md)",
                    data=merged_md.encode("utf-8"),
                    file_name="自选股分析合集.md",
                    mime="text/markdown",
                    key="watch_merge_md",
                    use_container_width=True,
                )
            with m2:
                st.download_button(
                    "🖨 下载合集 HTML（可打印 PDF）",
                    data=merged_html.encode("utf-8"),
                    file_name="自选股分析合集.html",
                    mime="text/html",
                    key="watch_merge_html",
                    use_container_width=True,
                )
            st.caption(f"已合并 {len(briefs)} 份一键分析简报；HTML 用浏览器「打印 → 另存为 PDF」。")

        render_auto_refresh_controls() if not readonly else None
        if not readonly:
            auto_refresh_fragment(C._fetch_one)

        render_alert_panel(watchlist=display_wl, snapshots=snaps)

        if display_wl:
            with st.expander("⚖ 权重", expanded=False):
                ww = normalize_watch_weights(st.session_state.get("watch_weights") or {})
                slices = pie_slices_for_watchlist(display_wl, ww)
                if slices:
                    labels = [f"{s['name']} ({s['code']})" for s in slices if s["pct"] > 0]
                    values = [s["pct"] for s in slices if s["pct"] > 0]
                    if not labels:
                        labels = [f"{s['name']} ({s['code']})" for s in slices]
                        values = [s["pct"] for s in slices]
                    fig_w = go.Figure(
                        data=[
                            go.Pie(
                                labels=labels,
                                values=values,
                                hole=0.35,
                                textinfo="label+percent",
                            )
                        ]
                    )
                    fig_w.update_layout(title="组合权重（展示用）", height=360, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_w, use_container_width=True, config=PLOTLY_CHART_CONFIG)
                    tbl = pd.DataFrame(
                        [
                            {
                                "名称": s["name"],
                                "代码": s["code"],
                                "原始权重%": f"{s['raw']:.1f}" if s["raw"] is not None else "—",
                                "归一化%": f"{s['pct']:.1f}",
                            }
                            for s in slices
                        ]
                    )
                    show_df(tbl, use_container_width=True, hide_index=True)
                    has_custom = any(s["raw"] is not None for s in slices)
                    st.caption(
                        "等权分配" if not has_custom else "已按原始权重归一化至 100%（仅展示，不影响评分/提醒）"
                    )
                if not readonly and display_wl:
                    st.session_state.watch_weights = ww
                    pick_w = st.selectbox(
                        "设置标的权重",
                        [str(x.get("代码") or "") for x in display_wl if x.get("代码")],
                        key="watch_weight_pick",
                    )
                    cur_w = get_weight(ww, pick_w)
                    weight_in = st.number_input(
                        "权重 %（留 0 清除）",
                        min_value=0.0,
                        value=float(cur_w or 0.0),
                        step=1.0,
                        key=f"watch_weight_val_{pick_w}",
                    )
                    if st.button("保存权重", key="watch_weight_save", use_container_width=True):
                        st.session_state.watch_weights = set_weight(
                            ww, pick_w, weight_in if weight_in > 0 else None
                        )
                        mark_dirty()
                        st.success("权重已保存。")
                        st.rerun()

        if display_wl and snaps:
            with st.expander("💚 自选健康分", expanded=False):
                ph = compute_portfolio_health(
                    display_wl,
                    snaps,
                    stale_hours=float(st.session_state.get("stale_hours", 24.0)),
                    pct_up=float(st.session_state.get("alert_pct_up", 5.0)),
                    pct_down=float(st.session_state.get("alert_pct_down", -5.0)),
                    score_low=float(st.session_state.get("alert_score_low", 40.0)),
                    score_high=float(st.session_state.get("alert_score_high", 65.0)),
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                )
                st.markdown(portfolio_health_markdown(ph))

        if display_wl and snaps:
            with st.expander("📈 涨跌贡献", expanded=False):
                ww_c = normalize_watch_weights(st.session_state.get("watch_weights") or {})
                portfolio_pct, contrib_rows = contribution_table_rows(display_wl, snaps, ww_c)
                if portfolio_pct is not None:
                    st.metric("组合加权涨跌幅", f"{portfolio_pct:+.2f}%")
                    show_df(
                        pd.DataFrame(contrib_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(
                        "贡献点 = 归一化权重 × 个股涨跌幅；贡献占比相对组合涨跌分解。"
                        "权重来自 ⚖ 权重设置，未设则等权。"
                    )
                else:
                    st.caption("暂无涨跌幅摘要，请先刷新全部摘要。")

        if display_wl and snaps:
            with st.expander("🗺 板块分布", expanded=False):
                buckets = aggregate_sector_distribution(
                    display_wl,
                    snaps,
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                )
                if buckets:
                    rows = sector_distribution_rows(buckets)
                    show_df(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    labels, counts = sector_bar_values(buckets)
                    fig_sector = go.Figure(
                        data=[go.Bar(x=labels, y=counts, marker_color="#4e79a7")]
                    )
                    fig_sector.update_layout(
                        title="自选数量按板块",
                        xaxis_title="板块",
                        yaxis_title="数量",
                        height=320,
                        margin=dict(l=40, r=20, t=40, b=80),
                    )
                    st.plotly_chart(fig_sector, use_container_width=True, config=PLOTLY_CHART_CONFIG)
                    st.caption("板块来自摘要 fin_summary 或简报财务段；无数据记为「未知」。")
                else:
                    st.caption("暂无板块分布数据。")

        if display_wl and snaps:
            with st.expander(
                "🏆 相对板块",
                expanded=watch_section_expanded(st.session_state, "sector_relative", default=False),
            ):
                rel_rows = compute_sector_relative(
                    display_wl,
                    snaps,
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                )
                if rel_rows:
                    show_df(
                        pd.DataFrame(sector_relative_table_rows(rel_rows)),
                        use_container_width=True,
                        hide_index=True,
                    )
                    outperform = sum(1 for r in rel_rows if r.label == "跑赢板块")
                    underperform = sum(1 for r in rel_rows if r.label == "跑输板块")
                    st.caption(
                        f"傻瓜结论：跑赢板块 {outperform} 只 · 跑输板块 {underperform} 只。"
                        "板块均值为自选内同板块快照均值（公开数据，非机构持仓）。"
                    )
                else:
                    st.caption("暂无相对板块数据，请先刷新全部摘要。")

        if display_wl and snaps:
            with st.expander("👑 板块龙头对标", expanded=False):
                leader_rows = compute_sector_leaders(
                    display_wl,
                    snaps,
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                )
                if leader_rows:
                    show_df(
                        pd.DataFrame(sector_leader_table_rows(leader_rows)),
                        use_container_width=True,
                        hide_index=True,
                    )
                    leaders = sum(1 for r in leader_rows if r.is_leader)
                    st.caption(
                        f"傻瓜结论：同板块内 {leaders} 只龙头 · "
                        "龙头按评分优先、涨跌幅次之（自选内公开快照，非外部排名）。"
                    )
                else:
                    st.caption("暂无板块龙头数据，请先刷新全部摘要。")

        if display_wl and snaps:
            similar = suggest_similar_picks(
                display_wl,
                snaps,
                brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
            )
            if similar:
                with st.expander("🔗 相似股推荐", expanded=False):
                    st.caption("同板块自选内按评分推荐（仅用本地快照，非外部荐股）")
                    show_df(
                        pd.DataFrame(similar_pick_rows(similar)),
                        use_container_width=True,
                        hide_index=True,
                    )

        if len(display_wl) >= 2:
            with st.expander("📊 双股对比", expanded=False):
                codes = [str(x.get("代码") or "") for x in display_wl if x.get("代码")]
                ca, cb = st.columns(2)
                with ca:
                    code_a = st.selectbox("标的 A", options=codes, key="compare_code_a")
                with cb:
                    other = [c for c in codes if c != code_a] or codes
                    code_b = st.selectbox("标的 B", options=other, key="compare_code_b")
                item_a = next((x for x in display_wl if str(x.get("代码") or "") == code_a), None)
                item_b = next((x for x in display_wl if str(x.get("代码") or "") == code_b), None)
                if item_a and item_b and code_a != code_b:
                    result = compare_two_stocks(
                        item_a,
                        item_b,
                        snaps.get(code_a),
                        snaps.get(code_b),
                    )
                    tbl = pd.DataFrame(compare_table_rows(result))
                    show_df(tbl, use_container_width=True, hide_index=True)
                    if result.pct_delta is not None or result.score_delta is not None:
                        hints: list[str] = []
                        if result.pct_delta is not None:
                            hints.append(
                                f"涨跌幅：A 比 B {'高' if result.pct_delta >= 0 else '低'} {abs(result.pct_delta):.2f} 个百分点"
                            )
                        if result.score_delta is not None:
                            hints.append(
                                f"评分：A 比 B {'高' if result.score_delta >= 0 else '低'} {abs(result.score_delta):.1f} 分"
                            )
                        st.caption(" · ".join(hints))
                    cmp_md = compare_to_markdown(result)
                    st.download_button(
                        "下载对比 (.md)",
                        data=cmp_md.encode("utf-8"),
                        file_name=f"双股对比_{code_a}_{code_b}.md",
                        mime="text/markdown",
                        key="compare_md_dl",
                        use_container_width=True,
                    )
                elif code_a == code_b:
                    st.info("请选择两只不同标的。")
                else:
                    st.caption("请先刷新摘要以填充涨跌幅与评分。")

        c_batch, c_batch_hint = st.columns([1, 2])
        with c_batch:
            if readonly:
                st.caption("只读模式：不可批量分析。")
            elif st.button("⚡ 深度分析前 3 只", key="watch_batch_quick", use_container_width=True):
                with st.spinner("正在对前 3 只自选股做完整一键分析（约 30–90 秒）…"):
                    q_label = C._stamp_query("watch")
                    results = batch_run_quick_analysis(
                        st.session_state.watchlist,
                        C._fetch_one,
                        max_items=3,
                        query_label=q_label,
                    )
                    if not results:
                        st.error("批量分析失败，请检查网络或稍后重试。")
                    else:
                        if "watch_snapshots" not in st.session_state:
                            st.session_state.watch_snapshots = {}
                        batch_entries = [
                            (code, str(res.snapshot.name or code))
                            for code, res in results.items()
                        ]
                        if batch_entries:
                            st.session_state.recent_viewed = push_recent_viewed_many(
                                st.session_state.get("recent_viewed"),
                                batch_entries,
                            )
                        for code, res in results.items():
                            st.session_state.watch_snapshots[code] = res.snapshot.as_dict()
                            st.session_state[f"brief_md_{code}"] = res.brief_md
                        first = next(iter(results.values()))
                        st.session_state["route_report"] = first.route_report
                        st.session_state["insight_pick"] = {
                            "代码": first.snapshot.code,
                            "名称": first.snapshot.name,
                            "市场": next(
                                (x.get("市场") for x in st.session_state.watchlist if x.get("代码") == first.snapshot.code),
                                "",
                            ),
                        }
                        mark_dirty()
                        C._save_history(
                            log_kind="insight",
                            log_label=f"批量一键分析 {len(results)} 只",
                            conclusions_summary=f"完成{len(results)}只",
                        )
                        st.success(f"已完成 {len(results)} 只的深度分析与简报。")
        with c_batch_hint:
            st.caption("依次生成简报并写入各标的；适合早晨快速过一遍重点自选。")

        fail_codes = failed_tickers(display_wl, snaps) if snaps else []
        if fail_codes and not readonly:
            st.caption("以下标的摘要拉取失败，可逐行重试：")
            for code in fail_codes:
                item_fail = next(
                    (x for x in display_wl if str(x.get("代码") or "") == code),
                    None,
                )
                if not item_fail:
                    continue
                snap_fail = snaps.get(code) or {}
                fc1, fc2 = st.columns([4, 1])
                with fc1:
                    st.text(
                        f"{item_fail.get('名称')} ({code}) — {snap_fail.get('one_line') or '拉取失败'}"
                    )
                with fc2:
                    if st.button("🔄 重试", key=retry_button_key(code), use_container_width=True):
                        new_snap, ok = refresh_one_snapshot(
                            item_fail,
                            C._fetch_one,
                            query_label=C._stamp_query("watch"),
                        )
                        if "watch_snapshots" not in st.session_state:
                            st.session_state.watch_snapshots = {}
                        st.session_state.watch_snapshots[code] = new_snap
                        mark_dirty()
                        if ok:
                            st.success(f"{code} 摘要已更新。")
                        else:
                            st.warning(f"{code} 仍拉取失败。")
                        st.rerun()

        if not readonly:
            with st.expander("📦 批量操作", expanded=False):
                pick_codes = [
                    str(x.get("代码") or "")
                    for x in display_wl
                    if x.get("代码")
                ] or [str(x.get("代码") or "") for x in st.session_state.watchlist if x.get("代码")]
                batch_sel = st.multiselect(
                    "选择标的（当前筛选列表）",
                    options=pick_codes,
                    key="watch_batch_sel",
                )
                b_rm, b_grp = st.columns(2)
                with b_rm:
                    if st.button(
                        "批量移出自选",
                        key="watch_batch_remove",
                        use_container_width=True,
                        disabled=not batch_sel,
                    ):
                        valid = codes_in_watchlist(st.session_state.watchlist, batch_sel)
                        new_wl, removed = batch_remove_from_watchlist(st.session_state.watchlist, valid)
                        st.session_state.watchlist = new_wl
                        st.session_state.watch_groups = batch_remove_from_groups(groups, removed)
                        for code in removed:
                            st.session_state.get("watch_snapshots", {}).pop(code, None)
                            st.session_state.pop(f"brief_md_{code}", None)
                        st.session_state.watch_notes = remove_tickers_notes(
                            normalize_watch_notes(st.session_state.get("watch_notes") or {}),
                            removed,
                        )
                        mark_dirty()
                        C._save_history(log_kind="watchlist", log_label=f"批量删除 {len(removed)} 只")
                        st.success(f"已移除 {len(removed)} 只自选股。")
                        st.rerun()
                with b_grp:
                    if group_names(groups):
                        batch_group = st.selectbox(
                            "加入分组",
                            group_names(groups),
                            key="watch_batch_group",
                        )
                        if st.button(
                            "批量加入分组",
                            key="watch_batch_assign",
                            use_container_width=True,
                            disabled=not batch_sel or not batch_group,
                        ):
                            valid = codes_in_watchlist(st.session_state.watchlist, batch_sel)
                            st.session_state.watch_groups = batch_add_to_group(
                                groups, valid, batch_group
                            )
                            mark_dirty()
                            st.success(f"已将 {len(valid)} 只加入「{batch_group}」。")
                            st.rerun()
                    else:
                        st.caption("请先在「分组管理」中创建分组。")

        render_sector_linkage_panel(watchlist=display_wl)

        st.divider()
        st.subheader("K 线与详情")
        code = picked_code or str(st.session_state.get("watch_code") or "")
        item = picked_item or next(
            (x for x in st.session_state.watchlist if str(x.get("代码") or "") == code),
            None,
        )
        if not item or not code:
            st.info("请先在上方 **⚡ 一键分析** 区选择一只股票。")
            return
        snap_sel = (st.session_state.get("watch_snapshots") or {}).get(code) or {}
        if item and code:
            rel_radar = sector_relative_for_ticker(
                compute_sector_relative(
                    st.session_state.watchlist,
                    st.session_state.get("watch_snapshots") or {},
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                ),
                code,
            )
            radar_flags = compute_risk_radar(
                snap_sel,
                sector_relative=rel_radar,
                stale_hours=float(st.session_state.get("stale_hours", 24.0)),
            )
            with st.expander(
                "⚠️ 风险雷达",
                expanded=any(f.triggered for f in radar_flags),
            ):
                st.markdown(
                    risk_radar_markdown(
                        radar_flags,
                        name=str(item.get("名称") or code),
                        code=code,
                    )
                )
        kind = str(item.get("类型") or "A") if item else "A"
        quote_ccy = str(item.get("货币") or "CNY") if item else "CNY"
        if item:
            st.caption(f"报价货币：**{currency_display(quote_ccy)}**")
            with st.expander("📝 笔记/标注", expanded=False):
                notes = normalize_watch_notes(st.session_state.get("watch_notes") or {})
                saved = get_note(notes, code)
                if readonly:
                    if saved:
                        st.caption(saved)
                    else:
                        st.caption("（无笔记）")
                else:
                    st.session_state.watch_notes = notes
                    draft = st.text_area(
                        "本标的备注（持久保存）",
                        value=saved,
                        height=88,
                        key=f"watch_note_{code}",
                        placeholder="如：目标价、持仓逻辑、下次复查事项…",
                    )
                    if st.button("保存笔记", key=f"watch_note_save_{code}", use_container_width=True):
                        st.session_state.watch_notes = set_note(notes, code, draft)
                        mark_dirty()
                        st.success("笔记已保存。")
                    elif saved:
                        st.caption(f"已保存：{saved[:120]}{'…' if len(saved) > 120 else ''}")
            with st.expander("🎯 价格目标", expanded=False):
                targets = normalize_price_targets(st.session_state.get("price_targets") or {})
                cur = get_targets(targets, code)
                snap_one = (st.session_state.get("watch_snapshots") or {}).get(code) or {}
                price = snap_one.get("price")
                if price is not None:
                    st.caption(f"摘要现价：**{float(price):.2f}**")
                if readonly:
                    parts = []
                    if cur.get("above") is not None:
                        parts.append(f"≥ {cur['above']:.2f}")
                    if cur.get("below") is not None:
                        parts.append(f"≤ {cur['below']:.2f}")
                    st.caption(" / ".join(parts) if parts else "（未设置）")
                else:
                    st.session_state.price_targets = targets
                    t1, t2 = st.columns(2)
                    with t1:
                        above_in = st.number_input(
                            "≥ 止盈/卖出",
                            min_value=0.0,
                            value=float(cur.get("above") or 0.0),
                            step=0.01,
                            key=f"watch_pt_above_{code}",
                        )
                    with t2:
                        below_in = st.number_input(
                            "≤ 买入/止损",
                            min_value=0.0,
                            value=float(cur.get("below") or 0.0),
                            step=0.01,
                            key=f"watch_pt_below_{code}",
                        )
                    if st.button("保存价格目标", key=f"watch_pt_save_{code}", use_container_width=True):
                        st.session_state.price_targets = set_targets(
                            targets,
                            code,
                            above=above_in if above_in > 0 else None,
                            below=below_in if below_in > 0 else None,
                        )
                        mark_dirty()
                        st.success("价格目标已保存。")
            render_floating_currency_tool(default_from=quote_ccy, watch_code=code)
            snap_one = (st.session_state.get("watch_snapshots") or {}).get(code) or {}
            rel_for_code = sector_relative_for_ticker(
                compute_sector_relative(
                    st.session_state.watchlist,
                    st.session_state.get("watch_snapshots") or {},
                    brief_for_code=lambda c: st.session_state.get(f"brief_md_{c}"),
                ),
                code,
            )
            log_one = st.session_state.get("query_log") or []
            snaps_hist_one = st.session_state.get("snapshots") or []
            trend_pts_one = collect_trend_points(log_one, snaps_hist_one, code, limit=6)
            alerts_one = [
                a
                for a in compute_watch_alerts(
                    [item],
                    {code: snap_one},
                    pct_up=float(st.session_state.get("alert_pct_up", 5.0)),
                    pct_down=float(st.session_state.get("alert_pct_down", -5.0)),
                    score_low=float(st.session_state.get("alert_score_low", 40.0)),
                    score_high=float(st.session_state.get("alert_score_high", 65.0)),
                    price_targets=st.session_state.get("price_targets"),
                )
                if a.code == code
            ]
            one_pager_md = build_institutional_onepager(
                name=str(item.get("名称") or code),
                code=code,
                snap=snap_one,
                sector_relative=rel_for_code,
                trend_points=trend_pts_one,
                alerts=alerts_one,
                query_label=C._query_label("watch") or format_query_datetime(),
            )
            with st.expander(
                "📄 机构一页纸",
                expanded=watch_section_expanded(
                    st.session_state, "institutional_onepager", default=False
                ),
            ):
                op_preview = (
                    one_pager_md
                    if len(one_pager_md) <= 3200
                    else one_pager_md[:3200] + "\n\n…"
                )
                st.markdown(op_preview)
                st.download_button(
                    "📄 下载机构式一页纸",
                    data=one_pager_md.encode("utf-8"),
                    file_name=f"一页纸_{code}.md",
                    mime="text/markdown",
                    key=f"watch_onepager_{code}",
                    use_container_width=True,
                )
            one_line = str(snap_one.get("one_line") or "").strip()
            if one_line and one_line not in ("—", "暂无评分。"):
                render_speech_button(text=one_line, key=f"speech_{code}")
        is_a6 = item and C._is_a_share_code6(code) and kind == "A"
        watch_df: pd.DataFrame | None = None
        watch_ksrc = ""
        watch_stats: dict[str, Any] | None = None
        watch_score = None

        if item:
            with st.expander("K线", expanded=False):
                chart_h = st.selectbox(
                    "图高度",
                    [720, 900, 1080],
                    index=1,
                    format_func=lambda x: f"{x}px",
                    key="watch_chart_h",
                )
                if "watch_visible_bars" not in st.session_state:
                    st.session_state.watch_visible_bars = DEFAULT_VISIBLE_BARS
                kline = st.radio(
                    "周期",
                    options=list(KLINE_PERIOD_UI),
                    horizontal=True,
                    key="watch_kline_period",
                )
                z1, z2, z3, z4 = st.columns([1, 1, 2, 2])
                with z1:
                    if st.button("拉长K线", help="减少可见 K 线根数，单根更宽", key="watch_zoom_in"):
                        st.session_state.watch_visible_bars = max(
                            MIN_VISIBLE_BARS,
                            int(st.session_state.watch_visible_bars) - 30,
                        )
                        st.rerun()
                with z2:
                    if st.button("缩短K线", help="增加可见 K 线根数，单根更窄", key="watch_zoom_out"):
                        st.session_state.watch_visible_bars = min(
                            MAX_VISIBLE_BARS,
                            int(st.session_state.watch_visible_bars) + 30,
                        )
                        st.rerun()
                with z3:
                    st.caption(f"当前可见约 **{st.session_state.watch_visible_bars}** 根 · 滚轮可缩放")
                with z4:
                    indicator = st.selectbox(
                        "副图指标",
                        options=list(CHART_INDICATORS),
                        index=0,
                        key="watch_indicator",
                    )
                intraday = is_intraday_kline(kline)
                day_opts = [5, 10, 30] if intraday else [30, 90, 180, 365, 730]
                day_idx = 1 if intraday else 2
                days = st.selectbox(
                    "回看天数",
                    options=day_opts,
                    index=min(day_idx, len(day_opts) - 1),
                    key="watch_days",
                )
                end = date.today()
                start = end - timedelta(days=int(days) + 10)
                try:
                    watch_df, watch_ksrc = C._fetch_one(item, start=start, end=end, kline=kline)
                except Exception as e:
                    st.error(f"获取行情失败：{e}")
                else:
                    df, ksrc = watch_df, watch_ksrc
                    q_label = C._stamp_query("watch")
                    stats = last_bar_stats(df)
                    bar_d = parse_bar_date(stats.get("日期"))
                    ds = metric_date_suffix(bar_d)
                    title = f"{item.get('名称', '')}（{code}）"
                    if stats:
                        m1, m2, m3, m4, m5 = st.columns(5)
                        pct = stats.get("涨跌幅%") or 0
                        m1.metric(f"收盘{ds}", f"{stats.get('收盘', 0):.2f}")
                        m2.metric(f"涨跌{ds}", f"{pct:+.2f}%", delta=f"{stats.get('涨跌额', 0):+.2f}")
                        m3.metric(f"最高{ds}", f"{stats.get('最高', 0):.2f}")
                        m4.metric(f"最低{ds}", f"{stats.get('最低', 0):.2f}")
                        vol = stats.get("成交量")
                        m5.metric(f"成交量{ds}", f"{vol:,.0f}" if vol is not None else "—")
                        st.caption(
                            build_kline_caption(
                                stats,
                                ksrc=ksrc,
                                query_label=q_label,
                                range_text=format_data_range(start, end),
                                currency=currency_display(quote_ccy),
                            )
                        )
                        lag = data_lag_hint(bar_d)
                        if lag:
                            st.warning(lag)
                        if "Yahoo" in ksrc and "东财" in ksrc:
                            st.caption("💡 当前走 Yahoo 备用源，A 股日线可能比东财慢 1–3 个交易日。")
                    else:
                        st.info(
                            f"报价货币：{currency_display(quote_ccy)}　|　"
                            f"行情来源：{ksrc}　|　本次查询：{q_label}"
                        )
                    if intraday and kind != "A":
                        st.warning("分钟 K 线仅支持沪深京 A 股东方财富；当前标的将尝试日线或可能无数据。")
                    chart_title = f"{title} · {currency_display(quote_ccy)}"
                    if bar_d:
                        chart_title += f" · K线至 {format_trade_date_cn(bar_d)}"
                    fig = build_pro_chart_multipane(
                        df,
                        chart_title,
                        indicator=indicator,
                        show_ma=(5, 10, 20, 60),
                        visible_bars=int(st.session_state.watch_visible_bars),
                        height=int(chart_h),
                    )
                    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CHART_CONFIG)
                    s = score_stock(df)
                    watch_stats = stats
                    watch_score = s
                    st.markdown("**技术面拆分**（数字越大通常越好，除风险外）")
                    show_df(
                        pd.DataFrame(
                            [
                                {"项目": "综合评分", "数值": f"{s.total:.1f}", "说明": plain_score_label(s.total)},
                                {"项目": "趋势", "数值": f"{s.trend:.1f}", "说明": "走势方向"},
                                {"项目": "动量", "数值": f"{s.momentum:.1f}", "说明": "近期力度"},
                                {"项目": "风险", "数值": f"{s.risk:.1f}", "说明": "波动风险（越低越好）"},
                                {"项目": "流动性", "数值": f"{s.liquidity:.1f}", "说明": "成交活跃度"},
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if s.notes:
                        st.caption("补充说明：" + "；".join(s.notes[:3]))
                    st.data_editor(
                        df.sort_values("日期", ascending=False).head(200),
                        use_container_width=True,
                        hide_index=True,
                    )

            with st.expander("财务对比", expanded=False):
                show_industry_compare_block(
                    code=code,
                    kind=kind,
                    lazy=True,
                    load_key=f"watch_fin_{code}",
                )

            if is_a6:
                with st.expander("所属板块", expanded=False):
                    render_stock_plates_panel(
                        code=code,
                        name=str(item.get("名称") or ""),
                        key_prefix=f"watch_{code}",
                        on_add_watchlist=C._add_a_watchlist_by_code,
                        lazy=True,
                    )

            st.divider()
            st.subheader("报告与下载")
            st.caption("一键分析在上方；这里可单独补 **行动路线** 或 **可读简报**。")
            code6 = code if kind == "A" and code.isdigit() else None
            yh = str(item.get("Yahoo") or code)
            news_watch = fetch_aggregated_news(code6=code6, yahoo_ticker=yh, limit=15)

            gen_route = False
            gen_brief = False
            if readonly:
                st.caption("只读模式：不可生成新简报。")
            else:
                btn_route, btn_brief = st.columns(2)
                with btn_route:
                    gen_route = st.button("生成行动路线", type="primary", key="watch_route", use_container_width=True)
                with btn_brief:
                    gen_brief = st.button("生成可读简报", key="watch_brief", use_container_width=True)

            if gen_route:
                if watch_df is None or watch_df.empty:
                    route_end = date.today()
                    route_start = route_end - timedelta(days=100)
                    try:
                        watch_df, watch_ksrc = C._fetch_one(
                            item, start=route_start, end=route_end, kline="日K"
                        )
                        watch_stats = last_bar_stats(watch_df)
                        watch_score = score_stock(watch_df)
                    except Exception as e:
                        st.error(f"无法生成报告：{e}")
                        watch_df = None
                if watch_df is not None and not watch_df.empty:
                    q_label = C._stamp_query("insight")
                    with st.spinner("正在聚合行情与新闻…"):
                        rep = build_action_route_report(
                            name=str(item.get("名称") or ""),
                            code=code,
                            kind=kind,
                            df=watch_df,
                            kline_src=watch_ksrc,
                            query_label=q_label,
                        )
                    st.session_state["route_report"] = rep
                    st.session_state["insight_pick"] = {
                        "代码": code,
                        "名称": item.get("名称"),
                        "市场": item.get("市场"),
                    }
                    mark_dirty()
                    C._save_history(log_kind="insight", log_label=f"工作台溯源 {item.get('名称')}")
                    st.success("行动路线已生成，见下方展开区。")

            if gen_brief:
                if watch_df is None or watch_df.empty:
                    st.warning("请先在上方「K线」区加载行情（展开后自动拉取）。")
                else:
                    rep_brief = route_report_from_session(st.session_state.get("route_report"))
                    pick = st.session_state.get("insight_pick") or {}
                    if pick and str(pick.get("代码") or "") != str(code):
                        rep_brief = None
                    with st.spinner("正在整理可读简报…"):
                        build_and_store_brief(
                            session_key=f"brief_md_{code}",
                            name=str(item.get("名称") or ""),
                            code=code,
                            kind=kind,
                            market=str(item.get("市场") or ""),
                            currency=quote_ccy,
                            stats=watch_stats,
                            score=watch_score,
                            kline_src=watch_ksrc,
                            query_label=C._query_label("watch") or format_query_datetime(),
                            route_report=rep_brief,
                            news=news_watch,
                        )
                    st.success("可读简报已生成，见下方。")

            rep_inline = route_report_from_session(st.session_state.get("route_report"))
            pick_inline = st.session_state.get("insight_pick") or {}
            if rep_inline and str(pick_inline.get("代码") or "") == str(code):
                with st.expander("📋 行动路线", expanded=False):
                    C._render_route_report_block(rep_inline)

            brief_md = st.session_state.get(f"brief_md_{code}")
            if brief_md:
                snap_b = (st.session_state.get("watch_snapshots") or {}).get(code) or {}
                render_readable_brief_panel(
                    brief_md=brief_md,
                    file_stem=f"{item.get('名称', '')}_{code}",
                    key_prefix=f"watch_brief_{code}",
                    one_line=str(snap_b.get("one_line") or ""),
                    score=snap_b.get("score"),
                )

            with st.expander("重大新闻（多源）", expanded=False):
                if not news_watch:
                    st.info("暂无新闻或接口不可用。")
                else:
                    for n in news_watch:
                        ntitle = n.get("标题") or ""
                        link = n.get("链接") or ""
                        src = n.get("来源") or ""
                        when = n.get("时间") or ""
                        if link:
                            st.markdown(f"- [{ntitle}]({link})（{src} {when}）")
                        else:
                            st.write(f"- {ntitle}（{src} {when}）")

