"""自选股今日速览 / 日报 Markdown（P5）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.analysis.risk_radar import RiskFlag, compute_risk_radar
from src.analysis.sector_relative import compute_sector_relative, sector_relative_for_ticker
from src.analysis.watch_alerts import WatchAlert
from src.util.query_time import format_query_datetime
from src.util.watch_notes import get_note, normalize_watch_notes


def _pct_str(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def format_notes_digest_section(
    watchlist: list[dict[str, Any]],
    watch_notes: dict[str, str] | None,
) -> str:
    """将自选笔记格式化为速览 Markdown 段落（P31）。"""
    notes = normalize_watch_notes(watch_notes or {})
    if not notes:
        return ""
    lines = ["## 自选笔记", ""]
    for item in watchlist:
        code = str(item.get("代码") or "")
        text = get_note(notes, code)
        if not text:
            continue
        name = str(item.get("名称") or code)
        safe = text.replace("|", "｜").replace("\n", " ")
        lines.append(f"- **{name}（{code}）** — {safe}")
    if len(lines) <= 2:
        return ""
    lines.append("")
    return "\n".join(lines)


def format_risk_digest_section(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    alerts: list[WatchAlert],
    *,
    stale_hours: float = 24.0,
) -> str:
    """将提醒标的的风险雷达汇总为速览 Markdown 段落（P83）。"""
    if not alerts:
        return ""
    rel_rows = compute_sector_relative(watchlist, snapshots)
    triggered: list[tuple[str, str, RiskFlag]] = []
    for alert in alerts:
        snap = snapshots.get(alert.code) or {}
        rel = sector_relative_for_ticker(rel_rows, alert.code)
        for flag in compute_risk_radar(
            snap,
            sector_relative=rel,
            stale_hours=stale_hours,
        ):
            if flag.triggered:
                triggered.append((alert.name, alert.code, flag))
    lines = ["## 风险雷达摘要", ""]
    if not triggered:
        lines.extend(["提醒标的暂无额外风险旗标触发。", ""])
        return "\n".join(lines)
    lines.append(f"共 **{len(triggered)}** 条风险旗标（提醒标的）：")
    lines.append("")
    for name, code, flag in triggered[:5]:
        lines.append(f"- ⚠️ **{name}（{code}）** · {flag.kind} — {flag.message}")
    if len(triggered) > 5:
        lines.append(f"- … 另有 {len(triggered) - 5} 条")
    lines.append("")
    return "\n".join(lines)


def format_alerts_digest_section(alerts: list[WatchAlert]) -> str:
    """将提醒列表格式化为速览 Markdown 段落（P23）。"""
    if not alerts:
        return ""
    lines = ["## 提醒摘要", "", f"共 {len(alerts)} 条触发项：", ""]
    for a in alerts:
        icon = {"hot": "🔥", "warn": "⚠️", "info": "ℹ️"}.get(a.level, "•")
        lines.append(f"- {icon} **{a.name}（{a.code}）** — {a.message}")
    lines.append("")
    return "\n".join(lines)


def build_watchlist_digest(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    title: str = "自选股今日速览",
    query_label: str = "",
    alerts: list[WatchAlert] | None = None,
    watch_notes: dict[str, str] | None = None,
    onepager_section: str = "",
    priority_section: str = "",
) -> str:
    now = query_label or format_query_datetime(datetime.now())
    lines: list[str] = [
        f"# {title}",
        "",
        f"> 生成时间：{now}　|　共 {len(watchlist)} 只",
        "",
        "| 名称 | 代码 | 涨跌幅 | 评分 | 一句话 |",
        "|------|------|--------|------|--------|",
    ]
    for item in watchlist:
        code = str(item.get("代码") or "")
        name = str(item.get("名称") or code)
        snap = snapshots.get(code) or {}
        pct = _pct_str(snap.get("pct"))
        score = snap.get("score")
        score_s = f"{float(score):.1f}" if score is not None else "—"
        one = str(snap.get("one_line") or "—").replace("|", "｜")[:80]
        fin = str(snap.get("fin_summary") or "").strip()
        lines.append(f"| {name} | {code} | {pct} | {score_s} | {one} |")
        if fin:
            lines.append(f"| ↳ 财务 | {code} | — | — | {fin.replace('|', '｜')[:100]} |")

    notes_section = format_notes_digest_section(watchlist, watch_notes)
    if notes_section:
        lines.append(notes_section)

    if alerts:
        lines.append(format_alerts_digest_section(alerts))
        lines.append(
            format_risk_digest_section(
                watchlist,
                snapshots,
                alerts,
            )
        )

    prio = str(priority_section or "").strip()
    if prio:
        lines.append(prio)

    section = str(onepager_section or "").strip()
    if section:
        lines.append(section)

    lines.extend(
        [
            "",
            "## 使用说明",
            "",
            "以上为规则型整理，基于公开行情，**非投资建议**。",
            "详细分析请在「① 分析工作台」对单只标的点击 **一键分析** 并下载完整简报。",
            "",
        ]
    )
    return "\n".join(lines)
