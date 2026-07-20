"""生成人类可读的股票分析简报（Markdown）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.analysis.mover_insight import ActionRouteReport
from src.analysis.signals import ScoreBreakdown
from src.util.currency import currency_display
from src.util.query_time import format_query_datetime


def _pct(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def _num(v: Any, *, digits: int = 2) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):,.{digits}f}"
    except (TypeError, ValueError):
        return "—"


def one_line_verdict(score: ScoreBreakdown, stats: dict[str, Any] | None) -> str:
    pct = stats.get("涨跌幅%") if stats else None
    parts: list[str] = []
    if score.total >= 65:
        parts.append("综合评分偏高，趋势与动量偏强")
    elif score.total <= 40:
        parts.append("综合评分偏低，需关注风险与流动性")
    else:
        parts.append("综合评分中性，宜结合板块与消息再判断")
    if pct is not None:
        try:
            p = float(pct)
            if p >= 5:
                parts.append("当日涨幅较大")
            elif p <= -5:
                parts.append("当日跌幅较大")
        except (TypeError, ValueError):
            pass
    return "；".join(parts) + "。"


def build_stock_brief_markdown(
    *,
    name: str,
    code: str,
    kind: str = "A",
    market: str = "",
    currency: str = "CNY",
    stats: dict[str, Any] | None,
    score: ScoreBreakdown | None,
    kline_src: str = "",
    query_label: str = "",
    route_report: ActionRouteReport | None = None,
    news: list[dict[str, Any]] | None = None,
    fin_summary: str = "",
) -> str:
    """组装 Markdown 简报，适合复制/下载/转发。"""
    now = query_label or format_query_datetime(datetime.now())
    title = f"{name}（{code}）"
    lines: list[str] = [
        f"# 股票分析简报 · {title}",
        "",
        f"> 生成时间：{now}　|　市场：{market or kind}　|　报价货币：{currency_display(currency)}",
        f"> 行情来源：{kline_src or '—'}",
        "",
        "## 一、30 秒摘要",
        "",
    ]

    if stats:
        lines.extend(
            [
                f"- **最新价**：{_num(stats.get('收盘'))}（{_pct(stats.get('涨跌幅%'))}）",
                f"- **区间**：高 {_num(stats.get('最高'))} / 低 {_num(stats.get('最低'))}",
                f"- **成交量**：{_num(stats.get('成交量'), digits=0)}",
                f"- **最新交易日**：{stats.get('日期') or '—'}",
            ]
        )
    else:
        lines.append("- 暂无最新行情快照。")

    if score:
        lines.extend(
            [
                "",
                f"- **综合评分**：{score.total:.1f} / 100",
                f"- **一句话**：{one_line_verdict(score, stats)}",
            ]
        )

    lines.extend(["", "## 二、评分拆解", ""])
    if score:
        lines.extend(
            [
                "| 维度 | 得分 | 说明 |",
                "|------|------|------|",
                f"| 趋势 | {score.trend:.1f} | MA 结构与方向 |",
                f"| 动量 | {score.momentum:.1f} | 短中期涨跌幅 |",
                f"| 风险 | {score.risk:.1f} | 波动率（越高分越低） |",
                f"| 流动性 | {score.liquidity:.1f} | 成交量相对水平 |",
                "",
            ]
        )
        if score.notes:
            lines.append("**要点：**")
            for n in score.notes:
                lines.append(f"- {n}")
            lines.append("")
    else:
        lines.append("暂无评分数据。\n")

    if fin_summary:
        lines.extend(
            [
                "## 财务对比摘要（A 股）",
                "",
                fin_summary,
                "",
            ]
        )

    if route_report:
        lines.extend(
            [
                "## 三、行动路线（规则推演，非投资建议）",
                "",
                f"### {route_report.title}",
                "",
                f"**结果**　{route_report.result}",
                "",
                f"**过程**　{route_report.process}",
                "",
                "**可能原因**",
            ]
        )
        for c in route_report.causes[:8]:
            lines.append(f"- {c}")
        lines.extend(["", "**参与者风格**"])
        for p in route_report.participants[:6]:
            lines.append(f"- {p}")
        lines.extend(["", "**可能思路**"])
        for b in route_report.playbooks[:6]:
            lines.append(f"- {b}")
        lines.append("")
    else:
        lines.extend(
            [
                "## 三、行动路线",
                "",
                "尚未生成。可在工作台点击「生成行动路线」后重新导出简报。",
                "",
            ]
        )

    lines.extend(["## 四、近期新闻", ""])
    news = news or []
    if not news:
        lines.append("暂无聚合新闻。\n")
    else:
        for n in news[:10]:
            t = str(n.get("标题") or "").strip()
            src = str(n.get("来源") or "")
            when = str(n.get("时间") or "")
            link = str(n.get("链接") or "")
            if link:
                lines.append(f"- [{t}]({link})（{src} {when}）")
            elif t:
                lines.append(f"- {t}（{src} {when}）")
        lines.append("")

    lines.extend(
        [
            "## 五、免责声明",
            "",
            "本简报基于公开行情与新闻的规则型整理，**不构成投资建议**。",
            "资金结构、异动解读等为模型估计，请以交易所及公司公告为准。",
            "",
        ]
    )
    return "\n".join(lines)
