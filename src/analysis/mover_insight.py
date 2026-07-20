"""
异动溯源：把「结果」拆成可理解的行动路线（规则型、可解释，非投资建议）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from src.analysis.signals import add_indicators, score_stock
from src.providers.news_feed import fetch_aggregated_news
from src.providers.ticker_util import yahoo_ticker_a


@dataclass
class ActionRouteReport:
    title: str
    result: str
    process: str
    causes: list[str]
    participants: list[str]
    playbooks: list[str]
    news: list[dict[str, Any]]
    data_sources: list[str]
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "result": self.result,
            "process": self.process,
            "causes": list(self.causes),
            "participants": list(self.participants),
            "playbooks": list(self.playbooks),
            "news": list(self.news),
            "data_sources": list(self.data_sources),
            "disclaimer": self.disclaimer,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ActionRouteReport":
        return cls(
            title=str(d.get("title") or ""),
            result=str(d.get("result") or ""),
            process=str(d.get("process") or ""),
            causes=[str(x) for x in (d.get("causes") or [])],
            participants=[str(x) for x in (d.get("participants") or [])],
            playbooks=[str(x) for x in (d.get("playbooks") or [])],
            news=list(d.get("news") or []),
            data_sources=[str(x) for x in (d.get("data_sources") or [])],
            disclaimer=str(d.get("disclaimer") or ""),
        )


def _last_narrative_stats(df: pd.DataFrame) -> dict[str, Any]:
    d = df.sort_values("日期").copy()
    close = pd.to_numeric(d["收盘"], errors="coerce")
    vol = pd.to_numeric(d.get("成交量", pd.Series([np.nan] * len(d))), errors="coerce")
    last = close.iloc[-1]
    prev = close.iloc[-2] if len(close) > 1 else np.nan
    pct_1d = (last / prev - 1) * 100 if np.isfinite(prev) and prev else np.nan
    pct_5d = (last / close.iloc[-6] - 1) * 100 if len(close) >= 6 else np.nan
    pct_20d = (last / close.iloc[-21] - 1) * 100 if len(close) >= 21 else np.nan
    vma = vol.rolling(20).mean().iloc[-1] if len(vol) >= 20 else np.nan
    vratio = float(vol.iloc[-1] / vma) if np.isfinite(vma) and vma > 0 else np.nan
    high_60 = close.tail(60).max() if len(close) >= 10 else last
    low_60 = close.tail(60).min() if len(close) >= 10 else last
    return {
        "收盘": float(last),
        "单日涨跌%": float(pct_1d) if np.isfinite(pct_1d) else None,
        "5日涨跌%": float(pct_5d) if np.isfinite(pct_5d) else None,
        "20日涨跌%": float(pct_20d) if np.isfinite(pct_20d) else None,
        "量比20": float(vratio) if np.isfinite(vratio) else None,
        "60日高": float(high_60),
        "60日低": float(low_60),
    }


def _guess_participants(stats: dict[str, Any], score_notes: list[str]) -> list[str]:
    out: list[str] = []
    vr = stats.get("量比20")
    pct = stats.get("单日涨跌%") or 0
    if vr is not None and vr >= 2.0 and abs(pct) >= 3:
        out.append(
            "【短线/游资风格资金】放量且波动大：常见于题材炒作、消息驱动日，"
            "往往快进快出，对盘口与换手率敏感。"
        )
    elif vr is not None and 1.2 <= vr < 2.0 and pct > 0:
        out.append(
            "【趋势/机构风格资金】温和放量上行：更可能是跟随行业或业绩预期，"
            "持仓周期相对更长，重视均线与基本面叙事。"
        )
    elif vr is not None and vr < 0.8:
        out.append(
            "【观望资金】缩量：多空都在等信号，可能是利好/利空落地后的犹豫期，"
            "或大盘系统性风险偏好下降。"
        )
    else:
        out.append(
            "【混合资金】量价特征不极端：散户追涨杀跌与机构调仓可能同时存在，"
            "需要结合新闻与板块联动判断主导力量。"
        )

    if any("偏弱" in n for n in score_notes):
        out.append("【空头/减仓方】技术面偏弱时，反弹多被视为减仓窗口而非新趋势起点。")
    if any("偏强" in n for n in score_notes):
        out.append("【多头/加仓方】技术面偏强时，回调更容易被视作买入机会（趋势跟随逻辑）。")
    return out


def _guess_playbooks(stats: dict[str, Any], causes: list[str]) -> list[str]:
    pct = stats.get("单日涨跌%") or 0
    vr = stats.get("量比20") or 1.0
    books: list[str] = []
    if pct > 5 and vr >= 1.5:
        books.append(
            "路线A（短线）：消息/题材驱动 → 早盘抢筹 → 冲高分批兑现；"
            "若次日缩量阴包阳，多数短线会选择止盈离场。"
        )
    elif pct > 0 and vr < 1.2:
        books.append(
            "路线B（波段）：基本面或行业逻辑未变 → 回踩均线吸纳 → 以 20/60 日线作为趋势防线；"
            "跌破均线则转为防守。"
        )
    elif pct < -5 and vr >= 1.5:
        books.append(
            "路线C（恐慌/出清）：利空或情绪宣泄 → 放量杀跌 → 反弹先看是否缩量；"
            "未出现承接前不宜盲目抄底。"
        )
    else:
        books.append(
            "路线D（观察）：信号混杂 → 等待「放量突破」或「缩量企稳」二选一确认后再行动。"
        )
    if causes:
        books.append("路线与新闻/公告线索对照：若新闻已充分定价，后续更看资金是否愿意接力。")
    return books


def _extract_causes_from_news(news: list[dict[str, Any]], stats: dict[str, Any]) -> list[str]:
    causes: list[str] = []
    pct = stats.get("单日涨跌%")
    if pct is not None:
        if pct >= 5:
            causes.append(f"价格结果：当日大涨约 {pct:.2f}%，属于显著异动。")
        elif pct <= -5:
            causes.append(f"价格结果：当日大跌约 {pct:.2f}%，属于显著异动。")
        else:
            causes.append(f"价格结果：当日涨跌约 {pct:.2f}%，波动处于常规偏上区间。")

    vr = stats.get("量比20")
    if vr is not None:
        if vr >= 2:
            causes.append(f"量能过程：量比（相对20日均量）约 {vr:.2f}，说明资金参与度明显提升。")
        elif vr <= 0.7:
            causes.append(f"量能过程：量比约 {vr:.2f}，交投清淡，方向选择尚不充分。")

    keywords = ("业绩", "预增", "亏损", "收购", "重组", "中标", "合同", "减持", "增持", "回购", "立案", "监管", "政策", "补贴")
    hit = []
    for n in news[:8]:
        t = (n.get("标题") or "") + (n.get("摘要") or "")
        for kw in keywords:
            if kw in t and kw not in hit:
                hit.append(kw)
    if hit:
        causes.append(f"事件线索（来自新闻标题/摘要关键词）：{', '.join(hit)} — 建议点开原文核对细节。")
    elif news:
        causes.append("事件线索：近期有相关资讯，但标题未命中常见关键词，需人工阅读新闻判断催化。")
    else:
        causes.append("事件线索：暂未聚合到新闻（接口不可用或该标的资讯较少），异动更可能来自板块联动或纯资金博弈。")

    p5 = stats.get("5日涨跌%")
    p20 = stats.get("20日涨跌%")
    if p5 is not None and p20 is not None:
        if p5 > 0 and p20 > 0:
            causes.append("背景：中短期趋势向上，异动可能是趋势加速而非单日随机波动。")
        elif p5 < 0 and p20 < 0:
            causes.append("背景：中短期趋势向下，反弹需警惕「下跌途中反抽」。")
    return causes


def build_action_route_report(
    *,
    name: str,
    code: str,
    kind: str,
    df: pd.DataFrame,
    kline_src: str,
    board_hint: str = "",
    query_label: str = "",
) -> ActionRouteReport:
    stats = _last_narrative_stats(df)
    score = score_stock(df)

    yahoo = ""
    if kind == "A" and code.isdigit() and len(code) == 6:
        yahoo = yahoo_ticker_a(code)
    elif kind in ("US", "HK"):
        yahoo = code.upper()

    news = fetch_aggregated_news(
        code6=code if kind == "A" else None,
        yahoo_ticker=yahoo or None,
        limit=12,
    )
    causes = _extract_causes_from_news(news, stats)
    participants = _guess_participants(stats, score.notes)
    playbooks = _guess_playbooks(stats, causes)

    process_lines = []
    if query_label:
        process_lines.append(f"- 本次查询时间：{query_label}")
    process_lines.append(
        f"- 数据区间：{df['日期'].min().date()} ~ {df['日期'].max().date()}（来源：{kline_src}）"
    )
    if stats.get("5日涨跌%") is not None:
        process_lines.append(f"- 近5日累计涨跌约 {stats['5日涨跌%']:.2f}%")
    if stats.get("20日涨跌%") is not None:
        process_lines.append(f"- 近20日累计涨跌约 {stats['20日涨跌%']:.2f}%")
    if stats.get("量比20") is not None:
        process_lines.append(f"- 最新交易日量比(20) ≈ {stats['量比20']:.2f}")
    process_lines.append(f"- 量化评分 {score.total:.1f}（趋势/动量/风险/流动性加权，见自选股页明细）")
    for n in score.notes[:4]:
        process_lines.append(f"  · {n}")

    result = (
        f"{name}（{code}）"
        + (f" 出现在【{board_hint}】" if board_hint else "")
        + f"；最新收盘 {stats.get('收盘', 0):.2f}"
    )

    sources = [kline_src]
    if news:
        srcs = sorted({str(n.get("来源") or "") for n in news if n.get("来源")})
        sources.append("新闻：" + "、".join(srcs))

    return ActionRouteReport(
        title=f"异动溯源 · {name}（{code}）",
        result=result,
        process="\n".join(process_lines),
        causes=causes,
        participants=participants,
        playbooks=playbooks,
        news=news,
        data_sources=sources,
        disclaimer="以上为基于公开行情与新闻的规则化推演，不构成投资建议；参与者动机为概率性描述。",
    )


def build_action_route_report_from_snapshot(
    *,
    name: str,
    code: str,
    snapshot: dict[str, Any],
    board_hint: str = "",
    query_label: str = "",
) -> ActionRouteReport:
    """K 线拉取失败时，用榜单/自选里的实时字段生成简版溯源报告。"""
    price = snapshot.get("最新价")
    pct = snapshot.get("涨跌幅%")
    vol = snapshot.get("成交量")
    amt = snapshot.get("成交额")
    turn = snapshot.get("换手率%")
    src = str(snapshot.get("数据来源") or "榜单快照")

    stats: dict[str, Any] = {
        "收盘": float(price) if price is not None else None,
        "单日涨跌%": float(pct) if pct is not None else None,
        "5日涨跌%": None,
        "20日涨跌%": None,
        "量比20": None,
    }

    yahoo = str(snapshot.get("Yahoo代码") or "").strip()
    if not yahoo and code.isdigit() and len(code) == 6:
        yahoo = yahoo_ticker_a(code)
    if not yahoo:
        yahoo = code
    news = fetch_aggregated_news(
        code6=code if code.isdigit() and len(code) == 6 else None,
        yahoo_ticker=yahoo or None,
        limit=12,
    )
    causes = _extract_causes_from_news(news, stats)
    causes.insert(
        0,
        "说明：历史 K 线暂不可用，以下基于榜单/自选中的最新价与涨跌幅等快照字段推演。",
    )
    if turn is not None:
        causes.append(f"榜单快照：换手率约 {float(turn):.2f}%。")
    if vol is not None and amt is not None:
        causes.append(f"榜单快照：成交量 {vol}，成交额 {amt}。")

    participants = _guess_participants(stats, [])
    playbooks = _guess_playbooks(stats, causes)

    result = (
        f"{name}（{code}）"
        + (f" 出现在【{board_hint}】" if board_hint else "")
        + (f"；榜单最新价 {price}" if price is not None else "")
        + (f"，涨跌幅 {pct:.2f}%" if pct is not None else "")
    )
    qline = f"- 本次查询时间：{query_label}\n" if query_label else ""
    process = (
        qline
        + f"- 数据来源：{src}（无完整 K 线，无法计算均线/量比/量化评分）\n"
        + f"- 榜单字段：最新价={price}，涨跌幅%={pct}，涨跌额={snapshot.get('涨跌额')}"
    )
    sources = [src]
    if news:
        srcs = sorted({str(n.get("来源") or "") for n in news if n.get("来源")})
        sources.append("新闻：" + "、".join(srcs))

    return ActionRouteReport(
        title=f"异动溯源 · {name}（{code}）· 简版",
        result=result,
        process=process,
        causes=causes,
        participants=participants,
        playbooks=playbooks,
        news=news,
        data_sources=sources,
        disclaimer="简版报告仅含榜单快照与新闻，不构成投资建议。完整分析请在 K 线可用后重新生成。",
    )
