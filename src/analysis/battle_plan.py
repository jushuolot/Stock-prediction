"""每日作战清单（P80）：从 dashboard stats + alerts + Top 3 行动生成 Markdown 清单。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.analysis.dashboard_stats import DashboardStats, compute_dashboard_stats
from src.analysis.watch_alerts import WatchAlert, compute_watch_alerts, top_alert_ticker
from src.util.query_time import format_query_datetime


def _top_actions(
    stats: DashboardStats,
    alerts: list[WatchAlert],
    *,
    missing_snapshots: int,
) -> list[str]:
    actions: list[str] = []
    top = top_alert_ticker(alerts)
    if top:
        actions.append(
            f"优先处理提醒：**{top.name}（{top.code}）** — {top.message}"
        )
    if stats.alert_count > 1:
        actions.append(f"复核其余 {stats.alert_count - 1} 条提醒（涨跌幅/评分/价格目标）")
    if missing_snapshots > 0:
        actions.append(f"刷新 {missing_snapshots} 只缺失摘要的自选标的")
    if stats.down_count > stats.up_count and stats.down_count >= 2:
        actions.append(
            f"组合偏弱：{stats.down_count} 跌 vs {stats.up_count} 涨，重点查看评分偏低标的"
        )
    elif stats.avg_score is not None and stats.avg_score <= 45:
        actions.append(
            f"组合均分 {stats.avg_score:.1f} 偏低，考虑换强留弱或控制仓位"
        )
    elif stats.alert_count == 0 and stats.snapshot_count >= stats.watch_count:
        actions.append("暂无紧急提醒：按计划复查重点自选与笔记/价格目标")

    fallbacks = [
        "打开「① 分析工作台」→「刷新全部摘要」同步最新涨跌幅与评分",
        "对重点标的下载「机构式一页纸」或查看「⚠️ 风险雷达」",
        "检查「智能提醒」阈值与静默时段是否符合当前策略",
    ]
    for fb in fallbacks:
        if len(actions) >= 3:
            break
        if fb not in actions:
            actions.append(fb)
    return actions[:3]


def build_battle_plan(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    stats: DashboardStats | None = None,
    alerts: list[WatchAlert] | None = None,
    query_label: str = "",
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
    price_targets: dict[str, dict[str, float | None]] | None = None,
) -> str:
    """生成每日作战 Markdown 清单（概况 + 提醒 + Top 3 行动）。"""
    if stats is None:
        stats = compute_dashboard_stats(
            watchlist,
            snapshots,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
        )
    if alerts is None:
        alerts = compute_watch_alerts(
            watchlist,
            snapshots,
            pct_up=pct_up,
            pct_down=pct_down,
            score_low=score_low,
            score_high=score_high,
            price_targets=price_targets,
        )
    now = query_label or format_query_datetime(datetime.now())
    missing = max(0, stats.watch_count - stats.snapshot_count)
    avg_s = f"{stats.avg_score:.1f}" if stats.avg_score is not None else "—"
    actions = _top_actions(stats, alerts, missing_snapshots=missing)

    lines: list[str] = [
        "# 📋 今日作战清单",
        "",
        f"> 生成时间：{now}　|　自选 {stats.watch_count} 只",
        "",
        "## 盘面概况",
        "",
        f"- [ ] 自选 **{stats.watch_count}** 只 · 已摘要 **{stats.snapshot_count}** 只",
        f"- [ ] 涨跌：**{stats.up_count}** 涨 · **{stats.down_count}** 跌 · **{stats.flat_count}** 平/未知",
        f"- [ ] 平均评分 **{avg_s}** · 提醒 **{stats.alert_count}** 条",
        "",
    ]
    if alerts:
        lines.extend(["## 待办提醒", ""])
        for a in alerts[:12]:
            icon = {"hot": "🔥", "warn": "⚠️", "info": "ℹ️"}.get(a.level, "•")
            lines.append(f"- [ ] {icon} **{a.name}（{a.code}）** — {a.message}")
        if len(alerts) > 12:
            lines.append(f"- [ ] … 另有 {len(alerts) - 12} 条提醒")
        lines.append("")
    else:
        lines.extend(["## 待办提醒", "", "- [x] 暂无阈值提醒触发", ""])

    lines.extend(["## 今日行动（Top 3）", ""])
    for i, act in enumerate(actions, start=1):
        lines.append(f"{i}. [ ] {act}")
    lines.extend(
        [
            "",
            "---",
            "",
            "以上为规则型整理，基于公开行情快照，**非投资建议**。",
            "",
        ]
    )
    return "\n".join(lines)
