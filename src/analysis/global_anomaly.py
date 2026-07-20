"""
全球股市异动全景：榜单 → 资金推测 → 多周期影响 → 情境分析 → 行业归类。

快速模式：仅用榜单快照（秒级完成批量）。
深度模式：单只拉 K 线 / 新闻 / 日内线（较慢）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal

import pandas as pd

from src.analysis.capital_attribution import CapitalMix, estimate_capital_mix
from src.analysis.context_analysis import analyze_context
from src.analysis.timeframe_impact import (
    TimeframeSlice,
    analyze_timeframes,
    snapshot_timeframe_slices,
)
from src.providers import market_data, yahoo
from src.providers.news_feed import fetch_aggregated_news
from src.providers.ticker_util import yahoo_ticker_a

AnalysisMode = Literal["fast", "deep"]


@dataclass
class MoverDeepAnalysis:
    code: str
    name: str
    market: str
    kind: str
    anomaly_score: float
    capital: CapitalMix
    timeframes: list
    context: dict[str, Any]
    news: list[dict[str, Any]]
    snapshot: dict[str, Any]
    mode: AnalysisMode = "fast"

    def to_summary_dict(self) -> dict[str, Any]:
        cap = self.capital.as_dict()
        macro = str(self.context.get("宏观预期") or "")
        return {
            "代码": self.code,
            "名称": self.name,
            "市场": self.market,
            "类型": self.kind,
            "涨跌幅%": self.snapshot.get("涨跌幅%"),
            "异动分": round(self.anomaly_score, 1),
            "行业": self.context.get("行业"),
            "分析模式": "快速" if self.mode == "fast" else "深度",
            **cap,
            "宏观预期": macro[:60] + "…" if len(macro) > 60 else macro,
        }


def _anomaly_score(pct: float | None, turn: float | None, vr: float | None) -> float:
    p = abs(float(pct or 0))
    t = float(turn or 0)
    v = float(vr or 1)
    return min(100.0, p * 4 + t * 1.5 + max(0, v - 1) * 12)


def _row_kind_market(row: dict[str, Any], default_market: str) -> tuple[str, str]:
    kind = str(row.get("类型") or "").upper()
    market = str(row.get("市场") or default_market)
    if kind in ("A", "HK", "US"):
        return kind, market
    if "港" in market:
        return "HK", market
    if "美" in market:
        return "US", market
    return "A", market


def _snapshot_volume_ratio(row: dict[str, Any]) -> float | None:
    v = row.get("量比20") or row.get("量比")
    if v is not None:
        try:
            return float(v)
        except (TypeError, ValueError):
            pass
    pct = abs(float(row.get("涨跌幅%") or 0))
    turn = float(row.get("换手率%") or 0)
    if pct >= 7 and turn >= 8:
        return 2.5
    if pct >= 3 and turn >= 3:
        return 1.6
    if turn < 1 and pct < 2:
        return 0.7
    return 1.2


def analyze_one_mover_fast(
    row: dict[str, Any],
    *,
    market: str = "A股",
    query_label: str = "",
) -> MoverDeepAnalysis:
    """仅用榜单字段：资金推测 + 行业归类（无网络请求）。"""
    kind, mkt = _row_kind_market(row, market)
    code = str(row.get("代码") or "").strip()
    name = str(row.get("名称") or "").strip()
    pct = row.get("涨跌幅%")
    turn = row.get("换手率%")
    vratio = _snapshot_volume_ratio(row)
    amt = row.get("成交额")

    capital = estimate_capital_mix(
        pct_change=pct,
        turnover_pct=turn,
        volume_ratio=vratio,
        amount=amt,
        market=mkt,
        kind=kind,
    )

    ctx = analyze_context(name=name, news=[], sector="", industry="")
    if query_label:
        ctx["摘要"] = [f"**本次查询时间**：{query_label}", "**模式**：快速（榜单快照）"] + list(
            ctx.get("摘要") or []
        )
    else:
        ctx["摘要"] = ["**模式**：快速（榜单快照，未拉 K 线/新闻）"] + list(ctx.get("摘要") or [])

    snap = dict(row)
    snap["量比20"] = vratio

    return MoverDeepAnalysis(
        code=code,
        name=name,
        market=mkt,
        kind=kind,
        anomaly_score=_anomaly_score(pct, turn, vratio),
        capital=capital,
        timeframes=snapshot_timeframe_slices(pct, turn),
        context=ctx,
        news=[],
        snapshot=snap,
        mode="fast",
    )


def analyze_one_mover_deep(
    row: dict[str, Any],
    *,
    market: str = "A股",
    query_label: str = "",
    include_intraday: bool = True,
) -> MoverDeepAnalysis:
    """单只深度：K 线 + 新闻 + 可选日内线。"""
    kind, mkt = _row_kind_market(row, market)
    code = str(row.get("代码") or "").strip()
    name = str(row.get("名称") or "").strip()
    yh = str(row.get("Yahoo代码") or code).strip()
    if kind == "A" and code.isdigit() and len(code) == 6:
        yh = yahoo_ticker_a(code) or yh

    pct = row.get("涨跌幅%")
    turn = row.get("换手率%")
    amt = row.get("成交额")
    vratio = _snapshot_volume_ratio(row)

    daily_df = None
    end = date.today()
    start = end - timedelta(days=400)
    try:
        if kind == "A" and code.isdigit() and len(code) == 6:
            daily_df, _ = market_data.fetch_kline_multi(
                kind="A", code=code, kline="日线", start=start, end=end
            )
        elif yh:
            daily_df = yahoo.fetch_history(yh, start=start, end=end, interval="1d")
    except Exception:
        daily_df = None

    if daily_df is not None and not daily_df.empty and "成交量" in daily_df.columns:
        vol = pd.to_numeric(daily_df["成交量"], errors="coerce")
        if len(vol) >= 21:
            vma = vol.rolling(20).mean().iloc[-1]
            if vma and vma > 0:
                vratio = float(vol.iloc[-1] / vma)

    capital = estimate_capital_mix(
        pct_change=pct,
        turnover_pct=turn,
        volume_ratio=vratio,
        amount=amt,
        market=mkt,
        kind=kind,
    )

    slices = analyze_timeframes(
        daily_df=daily_df,
        yahoo_ticker=yh,
        kind=kind,
        code=code,
        include_intraday=include_intraday,
    )

    sector, industry = "", ""
    if kind in ("US", "HK") and yh:
        try:
            prof = yahoo.fetch_profile(yh)
            sector, industry = prof.sector, prof.industry
        except Exception:
            pass

    news = fetch_aggregated_news(
        code6=code if kind == "A" and code.isdigit() and len(code) == 6 else None,
        yahoo_ticker=yh,
        limit=10,
    )
    ctx = analyze_context(name=name, news=news, sector=sector, industry=industry)
    prefix = [f"**本次查询时间**：{query_label}", "**模式**：深度（K线+新闻）"] if query_label else [
        "**模式**：深度（K线+新闻）"
    ]
    ctx["摘要"] = prefix + list(ctx.get("摘要") or [])

    snap = dict(row)
    snap["量比20"] = vratio

    return MoverDeepAnalysis(
        code=code,
        name=name,
        market=mkt,
        kind=kind,
        anomaly_score=_anomaly_score(pct, turn, vratio),
        capital=capital,
        timeframes=slices,
        context=ctx,
        news=news,
        snapshot=snap,
        mode="deep",
    )


def analyze_one_mover(
    row: dict[str, Any],
    *,
    market: str = "A股",
    query_label: str = "",
    fetch_intraday: bool = True,
    mode: AnalysisMode = "fast",
) -> MoverDeepAnalysis:
    if mode == "deep":
        return analyze_one_mover_deep(
            row, market=market, query_label=query_label, include_intraday=fetch_intraday
        )
    return analyze_one_mover_fast(row, market=market, query_label=query_label)


def analyze_movers_batch(
    movers: pd.DataFrame,
    *,
    market: str = "A股",
    limit: int = 15,
    query_label: str = "",
    deep: bool = False,
    mode: AnalysisMode | None = None,
) -> list[MoverDeepAnalysis]:
    """
    批量分析榜单前 N 只。
    默认 fast：无网络，10–30 只通常 <1 秒。
    deep=True 已废弃批量深度，请用 analyze_one_mover_deep 单只分析。
    """
    use_fast = mode != "deep" and not deep
    out: list[MoverDeepAnalysis] = []
    n = min(limit, len(movers))
    for i in range(n):
        row = movers.iloc[i].to_dict()
        try:
            if use_fast:
                out.append(
                    analyze_one_mover_fast(
                        row,
                        market=market,
                        query_label=query_label if i == 0 else "",
                    )
                )
            else:
                out.append(
                    analyze_one_mover_deep(
                        row,
                        market=market,
                        query_label=query_label if i == 0 else "",
                        include_intraday=i < 5,
                    )
                )
        except Exception:
            continue
    return out


def summary_dataframe(analyses: list[MoverDeepAnalysis]) -> pd.DataFrame:
    if not analyses:
        return pd.DataFrame()
    return pd.DataFrame([a.to_summary_dict() for a in analyses])
