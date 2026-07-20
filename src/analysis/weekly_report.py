"""周报 Markdown（P44）：近 7 日 query_log + 自选股统计。"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from src.analysis.dashboard_stats import compute_dashboard_stats
from src.storage.history_store import KIND_LABELS, log_date_key
from src.util.query_time import format_query_datetime
from src.util.watch_sort import ui_sort_by
from src.util.watchlist_export import sort_watchlist


def _parse_log_at(at: str | None) -> datetime | None:
    s = str(at or "").strip()
    m = re.match(r"(\d{4})年(\d{2})月(\d{2})日", s)
    if not m:
        return None
    try:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def filter_log_last_days(
    log: list[dict[str, Any]],
    *,
    days: int = 7,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """保留 at 落在 [now-days, now] 内的记录（含当天）。"""
    ref = now or datetime.now()
    cutoff = (ref - timedelta(days=max(1, days) - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    out: list[dict[str, Any]] = []
    for entry in log:
        dt = _parse_log_at(str(entry.get("at") or ""))
        if dt is None or dt >= cutoff:
            out.append(entry)
    return out


def _pct_str(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def _score_str(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return "—"


def build_weekly_report(
    query_log: list[dict[str, Any]],
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    days: int = 7,
    now: datetime | None = None,
    title: str = "分析周报",
) -> str:
    """汇总近 N 日查询日志与当前自选股快照。"""
    ref = now or datetime.now()
    recent = filter_log_last_days(query_log, days=days, now=ref)
    period_start = (ref - timedelta(days=max(1, days) - 1)).strftime("%Y年%m月%d日")
    period_end = ref.strftime("%Y年%m月%d日")
    generated = format_query_datetime(ref)

    lines: list[str] = [
        f"# {title}",
        "",
        f"> 周期：{period_start} — {period_end}　|　生成：{generated}",
        "",
        "## 查询概览",
        "",
        f"- 近 **{days}** 日共 **{len(recent)}** 条记录（全量 {len(query_log)} 条）",
    ]

    if recent:
        kind_counts = Counter(str(e.get("kind") or "unknown") for e in recent)
        lines.append("- 按类型：")
        for kind, cnt in kind_counts.most_common():
            label = KIND_LABELS.get(kind, kind)
            lines.append(f"  - {label}：{cnt}")
        dates = sorted({log_date_key(e.get("at")) for e in recent if e.get("at")}, reverse=True)
        if dates:
            lines.append(f"- 活跃日期：{'、'.join(dates[:7])}")
    else:
        lines.append("- （该周期内暂无查询记录）")

    lines.extend(["", "## 自选股快照", ""])
    stats = compute_dashboard_stats(watchlist, snapshots)
    lines.extend(
        [
            f"- 自选 **{stats.watch_count}** 只，有摘要 **{stats.snapshot_count}** 只",
            f"- 均分：**{_score_str(stats.avg_score)}**（{stats.scored_count} 只有评分）",
            f"- 涨跌：↑ {stats.up_count} · ↓ {stats.down_count} · — {stats.flat_count}",
            f"- 当日提醒触发：**{stats.alert_count}** 条",
            "",
        ]
    )

    if watchlist and snapshots:
        sorted_wl = sort_watchlist(
            watchlist,
            snapshots,
            by=ui_sort_by("score"),
            descending=True,
        )
        lines.extend(["### 评分 Top 5", "", "| 名称 | 代码 | 涨跌幅 | 评分 |", "|------|------|--------|------|"])
        for item in sorted_wl[:5]:
            code = str(item.get("代码") or "")
            snap = snapshots.get(code) or {}
            lines.append(
                f"| {item.get('名称') or code} | {code} | {_pct_str(snap.get('pct'))} | {_score_str(snap.get('score'))} |"
            )
        lines.append("")

    if recent:
        lines.extend(["## 近期记录", ""])
        for entry in recent[:15]:
            kind_cn = KIND_LABELS.get(str(entry.get("kind") or ""), entry.get("kind") or "")
            summary = str(entry.get("conclusions_summary") or "")[:80]
            lines.append(
                f"- **{entry.get('at')}** · {kind_cn} · {entry.get('label')}"
                + (f" — {summary}" if summary else "")
            )
        if len(recent) > 15:
            lines.append(f"- … 另有 {len(recent) - 15} 条未列出")
        lines.append("")

    lines.append("---")
    lines.append("*非投资建议 · 由 Stock Assistant 自动生成*")
    return "\n".join(lines)
