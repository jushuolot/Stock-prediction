"""机构式一页纸（P74）：公开快照 + 财务摘要 + 板块相对 + 趋势 + 提醒拼装 Markdown。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.analysis.sector_relative import SectorRelativeRow
from src.analysis.trend_summary import TrendPoint, trend_delta
from src.analysis.watch_alerts import WatchAlert
from src.util.query_time import format_query_datetime


def _score_label(score: float | None) -> str:
    if score is None:
        return "待分析"
    if score >= 65:
        return "偏强"
    if score <= 40:
        return "偏弱"
    return "中性"


def _pct_text(pct: float | None) -> str:
    if pct is None:
        return "—"
    return f"{pct:+.2f}%"


def _next_steps(
    *,
    score: float | None,
    sector_row: SectorRelativeRow | None,
    alerts: list[WatchAlert],
) -> list[str]:
    steps: list[str] = []
    if score is None:
        steps.append("先点「刷新全部摘要」或「一键分析」补齐评分与涨跌幅。")
    elif score >= 65:
        steps.append("评分偏强：可结合板块相对强弱决定是否加仓或止盈。")
    elif score <= 40:
        steps.append("评分偏弱：优先核对财务摘要与提醒项，控制仓位。")
    else:
        steps.append("评分中性：等待板块或趋势出现更清晰信号再行动。")
    if sector_row:
        if sector_row.label == "跑赢板块":
            steps.append("相对板块偏强：可关注是否持续领先同板块自选。")
        elif sector_row.label == "跑输板块":
            steps.append("相对板块偏弱：对比同板块自选，评估是否换强留弱。")
        elif sector_row.label == "板块仅本只":
            steps.append("自选同板块仅本只：可在搜索页找同板块标的加入对比。")
    if alerts:
        steps.append(f"当前有 {len(alerts)} 条提醒触发，建议先处理价格目标或涨跌幅阈值。")
    else:
        steps.append("暂无阈值提醒：可在「智能提醒」设置涨跌幅/评分/价格目标。")
    steps.append("数据均来自东财/Yahoo 等公开源，仅供研究，非投资建议。")
    return steps


def build_institutional_onepager(
    *,
    name: str,
    code: str,
    snap: dict[str, Any] | None,
    sector_relative: SectorRelativeRow | None = None,
    trend_points: list[TrendPoint] | None = None,
    alerts: list[WatchAlert] | None = None,
    query_label: str = "",
) -> str:
    """拼装中文一页纸：结论 / 相对板块 / 风险 / 下一步。"""
    snap = snap or {}
    alerts = alerts or []
    now = query_label or format_query_datetime(datetime.now())
    pct = snap.get("pct")
    score = snap.get("score")
    try:
        pct_f = float(pct) if pct is not None else None
    except (TypeError, ValueError):
        pct_f = None
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None
    fin = str(snap.get("fin_summary") or "—").strip() or "—"
    one_line = str(snap.get("one_line") or "—").strip() or "—"
    sl = _score_label(score_f)

    lines: list[str] = [
        f"# {name}（{code}）机构式一页纸",
        "",
        f"> 生成时间：{now}　|　数据来源：公开行情/财务摘要（东财/Yahoo 等）",
        "",
        "## 结论",
        "",
        f"- **综合判断**：评分 **{sl}**（{score_f:.1f} 分）" if score_f is not None else "- **综合判断**：待分析",
        f"- **当日涨跌**：{_pct_text(pct_f)}",
        f"- **一句话**：{one_line}",
        f"- **财务摘要**：{fin}",
        "",
        "## 相对板块",
        "",
    ]
    if sector_relative:
        sr = sector_relative
        lines.extend(
            [
                f"- **板块**：{sr.sector}",
                f"- **相对结论**：**{sr.label}** — {sr.fool_conclusion}",
                f"- 个股涨跌幅 {_pct_text(sr.ticker_pct)} vs 板块均 {_pct_text(sr.sector_avg_pct)}"
                + (f"（差 {sr.pct_vs_sector:+.2f} 个百分点）" if sr.pct_vs_sector is not None else ""),
            ]
        )
        if sr.ticker_score is not None and sr.sector_avg_score is not None:
            lines.append(
                f"- 个股评分 {sr.ticker_score:.1f} vs 板块均 {sr.sector_avg_score:.1f}"
                + (f"（差 {sr.score_vs_sector:+.1f} 分）" if sr.score_vs_sector is not None else "")
            )
    else:
        lines.append("- 暂无板块相对数据，请先刷新自选摘要。")
    lines.extend(["", "## 风险", ""])
    risk_items: list[str] = []
    if score_f is not None and score_f <= 40:
        risk_items.append("评分偏低，波动与回撤风险需重点留意。")
    if pct_f is not None and pct_f <= -5:
        risk_items.append(f"当日跌幅较大（{_pct_text(pct_f)}），短线情绪偏弱。")
    if pct_f is not None and pct_f >= 8:
        risk_items.append(f"当日涨幅较大（{_pct_text(pct_f)}），注意追高风险。")
    for a in alerts:
        risk_items.append(f"{a.name}（{a.code}）：{a.message}")
    if trend_points and len(trend_points) >= 2:
        score_d, pct_d = trend_delta(trend_points)
        if score_d is not None and score_d <= -5:
            risk_items.append(f"近期评分回落 {score_d:+.1f} 分（历史快照对比）。")
        if pct_d is not None and pct_d <= -8:
            risk_items.append(f"近期涨跌幅走弱 {pct_d:+.2f} 个百分点（历史快照对比）。")
    if not risk_items:
        risk_items.append("暂无显著风险触发项；仍须结合仓位与基本面自行判断。")
    for item in risk_items:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步", ""])
    for step in _next_steps(score=score_f, sector_row=sector_relative, alerts=alerts):
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def build_onepager_push_summary(
    *,
    name: str,
    code: str,
    snap: dict[str, Any] | None,
    sector_relative: SectorRelativeRow | None = None,
    alert_message: str = "",
) -> str:
    """cron/webhook 用精简一页纸段落（P77）。"""
    snap = snap or {}
    pct = snap.get("pct")
    score = snap.get("score")
    try:
        pct_f = float(pct) if pct is not None else None
    except (TypeError, ValueError):
        pct_f = None
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None
    fin = str(snap.get("fin_summary") or "—").strip() or "—"
    one_line = str(snap.get("one_line") or "—").strip() or "—"
    lines: list[str] = [
        "## 机构式一页纸（重点提醒标的）",
        "",
        f"**{name}（{code}）** — {_score_label(score_f)}"
        + (f" · 评分 {score_f:.1f}" if score_f is not None else ""),
        f"- 当日涨跌：{_pct_text(pct_f)}",
        f"- 一句话：{one_line}",
        f"- 财务摘要：{fin}",
    ]
    if alert_message:
        lines.append(f"- 触发提醒：{alert_message}")
    if sector_relative:
        sr = sector_relative
        lines.append(
            f"- 相对板块：**{sr.label}**（{sr.sector}）— {sr.fool_conclusion}"
        )
        if sr.pct_vs_sector is not None:
            lines.append(f"- 涨跌幅 vs 板块均：{sr.pct_vs_sector:+.2f} 个百分点")
        if sr.score_vs_sector is not None:
            lines.append(f"- 评分 vs 板块均：{sr.score_vs_sector:+.1f} 分")
    lines.append("- 数据来自公开源，仅供研究，非投资建议。")
    lines.append("")
    return "\n".join(lines)
