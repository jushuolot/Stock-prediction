"""P3：一键分析 — 并行拉行情、评分、简报与 A 股财务摘要。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable

import pandas as pd

from src.analysis.mover_insight import ActionRouteReport, build_action_route_report
from src.analysis.readable_report import build_stock_brief_markdown, one_line_verdict
from src.analysis.signals import ScoreBreakdown, score_stock
from src.providers.news_feed import fetch_aggregated_news
from src.ui.pro_chart import last_bar_stats
from src.util.fetch_cache import get_cached_snapshots, set_cached_snapshots
from src.util.query_time import format_query_datetime


FetchFn = Callable[..., tuple[pd.DataFrame, str]]


@dataclass
class WatchSnapshot:
    code: str
    name: str
    pct: float | None
    score: float | None
    one_line: str
    price: float | None = None
    fin_summary: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QuickAnalysisResult:
    df: pd.DataFrame
    kline_src: str
    stats: dict[str, Any]
    score: ScoreBreakdown
    snapshot: WatchSnapshot
    route_report: ActionRouteReport
    brief_md: str
    fin_data: dict[str, Any] | None
    news: list[dict[str, Any]]


def industry_fin_summary(data: dict[str, Any] | None) -> str:
    """从东财财务对比表提取一行摘要。"""
    if not data or not data.get("ok"):
        return ""
    cols = data.get("columns") or []
    stock = next((r for r in data.get("rows") or [] if r.get("kind") == "stock"), None)
    rank = next((r for r in data.get("rows") or [] if r.get("kind") == "rank"), None)
    if not stock:
        return ""
    cells = stock.get("cells") or []
    idx = {c: i for i, c in enumerate(cols)}
    parts: list[str] = [str(data.get("industry") or "行业")]
    for key in ("ROE", "市盈率(动)", "市净率"):
        i = idx.get(key)
        if i is None or i >= len(cells):
            continue
        val = str(cells[i] or "").strip()
        if val and val != "—":
            parts.append(f"{key}{val}")
    if rank:
        rc = rank.get("cells") or []
        i = idx.get("ROE")
        if i is not None and i < len(rc):
            rk = str(rc[i] or "").strip()
            if rk and rk != "—":
                parts.append(f"ROE{rk}")
    return " · ".join(parts[:6])


def _code6(item: dict[str, Any]) -> str | None:
    kind = str(item.get("类型") or "A")
    code = str(item.get("代码") or "").strip()
    if kind != "A" or not code.replace(".", "").isdigit():
        return None
    return code.split(".")[0].zfill(6)[:6]


def build_watch_snapshot(
    *,
    item: dict[str, Any],
    stats: dict[str, Any] | None,
    score: ScoreBreakdown | None,
    fin_data: dict[str, Any] | None = None,
    query_label: str = "",
) -> WatchSnapshot:
    code = str(item.get("代码") or "")
    name = str(item.get("名称") or code)
    pct = None
    if stats and stats.get("涨跌幅%") is not None:
        try:
            pct = float(stats["涨跌幅%"])
        except (TypeError, ValueError):
            pct = None
    one = one_line_verdict(score, stats) if score else "暂无评分。"
    fin = industry_fin_summary(fin_data)
    price = None
    if stats and stats.get("收盘") is not None:
        try:
            price = float(stats["收盘"])
        except (TypeError, ValueError):
            price = None
    return WatchSnapshot(
        code=code,
        name=name,
        pct=pct,
        score=float(score.total) if score else None,
        one_line=one,
        price=price,
        fin_summary=fin,
        updated_at=query_label or format_query_datetime(datetime.now()),
    )


def analyze_watch_light(
    item: dict[str, Any],
    fetch_fn: FetchFn,
    *,
    days: int = 100,
) -> WatchSnapshot:
    """轻量分析：仅 K 线 + 评分（用于自选股批量刷新）。"""
    end = date.today()
    start = end - timedelta(days=int(days) + 10)
    df, _ = fetch_fn(item, start=start, end=end, kline="日K")
    if df is None or df.empty:
        raise ValueError("无行情数据")
    stats = last_bar_stats(df)
    sc = score_stock(df)
    return build_watch_snapshot(item=item, stats=stats, score=sc)


def refresh_watch_snapshots(
    watchlist: list[dict[str, Any]],
    fetch_fn: FetchFn,
    *,
    max_items: int = 15,
    query_label: str = "",
) -> dict[str, dict[str, Any]]:
    """批量刷新自选股摘要，返回 code -> snapshot dict。"""
    batch = watchlist[: max(1, int(max_items))]
    codes = [str(item.get("代码") or "") for item in batch if item.get("代码")]
    cached = get_cached_snapshots(codes)
    if cached is not None:
        return cached

    out: dict[str, dict[str, Any]] = {}
    label = query_label or format_query_datetime(datetime.now())
    for item in batch:
        code = str(item.get("代码") or "")
        if not code:
            continue
        try:
            snap = analyze_watch_light(item, fetch_fn)
            snap.updated_at = label
            out[code] = snap.as_dict()
        except Exception as exc:
            fail = WatchSnapshot(
                code=code,
                name=str(item.get("名称") or code),
                pct=None,
                score=None,
                one_line=f"拉取失败：{exc}",
                updated_at=label,
            ).as_dict()
            fail["fetch_failed"] = True
            out[code] = fail
    set_cached_snapshots(codes, out)
    return out


def run_quick_analysis(
    item: dict[str, Any],
    fetch_fn: FetchFn,
    *,
    days: int = 100,
    query_label: str = "",
) -> QuickAnalysisResult:
    """一键分析：并行 K 线 / 新闻 / 财务对比，并生成路线与简报。"""
    kind = str(item.get("类型") or "A")
    code = str(item.get("代码") or "").strip()
    name = str(item.get("名称") or code)
    yh = str(item.get("Yahoo") or code)
    code6 = _code6(item)
    end = date.today()
    start = end - timedelta(days=int(days) + 10)
    q_label = query_label or format_query_datetime(datetime.now())

    def _kline() -> tuple[pd.DataFrame, str]:
        return fetch_fn(item, start=start, end=end, kline="日K")

    def _news() -> list[dict[str, Any]]:
        return fetch_aggregated_news(
            code6=code6,
            yahoo_ticker=yh,
            limit=15,
        )

    def _fin() -> dict[str, Any] | None:
        if not code6:
            return None
        from src.providers.eastmoney_f10 import fetch_industry_compare

        return fetch_industry_compare(code6)

    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_k = pool.submit(_kline)
        fut_n = pool.submit(_news)
        fut_f = pool.submit(_fin) if code6 else None
        df, ksrc = fut_k.result()
        news = fut_n.result()
        fin_data = fut_f.result() if fut_f else None

    if df is None or df.empty:
        raise ValueError("无行情数据，无法完成一键分析")

    stats = last_bar_stats(df)
    sc = score_stock(df)
    snapshot = build_watch_snapshot(
        item=item, stats=stats, score=sc, fin_data=fin_data, query_label=q_label
    )
    fin_summary = snapshot.fin_summary
    rep = build_action_route_report(
        name=name,
        code=code,
        kind=kind,
        df=df,
        kline_src=ksrc,
        query_label=q_label,
    )
    brief = build_stock_brief_markdown(
        name=name,
        code=code,
        kind=kind,
        market=str(item.get("市场") or ""),
        currency=str(item.get("货币") or "CNY"),
        stats=stats,
        score=sc,
        kline_src=ksrc,
        query_label=q_label,
        route_report=rep,
        news=news,
        fin_summary=fin_summary,
    )
    return QuickAnalysisResult(
        df=df,
        kline_src=ksrc,
        stats=stats,
        score=sc,
        snapshot=snapshot,
        route_report=rep,
        brief_md=brief,
        fin_data=fin_data,
        news=news,
    )


def batch_run_quick_analysis(
    watchlist: list[dict[str, Any]],
    fetch_fn: FetchFn,
    *,
    max_items: int = 3,
    query_label: str = "",
) -> dict[str, QuickAnalysisResult]:
    """对自选股前几只做完整一键分析（适合小白批量导出）。"""
    out: dict[str, QuickAnalysisResult] = {}
    label = query_label or format_query_datetime(datetime.now())
    for item in watchlist[: max(1, int(max_items))]:
        code = str(item.get("代码") or "")
        if not code:
            continue
        try:
            out[code] = run_quick_analysis(item, fetch_fn, query_label=label)
        except Exception:
            continue
    return out
