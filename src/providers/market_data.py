"""统一行情入口：多源拉取 + 新鲜度校验，降低对单一站点依赖。"""

from __future__ import annotations

from datetime import date

import pandas as pd

from src.providers import eastmoney, fresh_fetch, yahoo
from src.providers import yahoo_ranking
from src.providers.ticker_util import is_bj_code, yahoo_ticker_a


def fetch_global_ranking_multi(
    *,
    market: str = "A股",
    board: str = "涨幅榜",
    limit: int = 50,
) -> tuple[pd.DataFrame, str]:
    """全球榜单：A 股东财→新浪；港股/美股 Yahoo。"""
    m = (market or "A股").strip()
    if m in ("A股", "沪深京", "A"):
        return fetch_a_ranking_multi(board=board, limit=limit)
    if m in ("港股", "HK"):
        df = yahoo_ranking.fetch_ranking(region="HK", board=board, limit=limit)
        if not df.empty:
            return df, "Yahoo Finance（港股）"
        return df, "无可用数据源"
    if m in ("美股", "US"):
        df = yahoo_ranking.fetch_ranking(region="US", board=board, limit=limit)
        if not df.empty:
            return df, "Yahoo Finance（美股）"
        return df, "无可用数据源"
    return fetch_a_ranking_multi(board=board, limit=limit)


def fetch_a_ranking_multi(*, board: str = "涨幅榜", limit: int = 50) -> tuple[pd.DataFrame, str]:
    """A 股榜单：东财 → 新浪，须通过新鲜度校验。"""
    return fresh_fetch.fetch_a_ranking_fresh(board=board, limit=limit)


def _normalize_kline_period(kline: str) -> str:
    k = (kline or "").strip()
    if k.lower() in ("daily", "1d", "d"):
        return "日线"
    return k


def fetch_kline_multi(
    *,
    kind: str,
    code: str,
    kline: str,
    start: date,
    end: date,
) -> tuple[pd.DataFrame, str]:
    kline = _normalize_kline_period(kline)
    code = (code or "").strip()
    if kind == "A" and code.isdigit() and len(code) == 6:
        if eastmoney.is_intraday_kline(kline):
            try:
                df = eastmoney.fetch_a_kline(code, kline=kline, start=start, end=end)
                src = str(df.iloc[0].get("数据来源", "东方财富")) if not df.empty else "东方财富"
                return df, src
            except Exception as em_err:
                raise RuntimeError(
                    f"分钟级 K 线（{kline}）仅支持东方财富；{code} 拉取失败：{em_err}"
                ) from em_err
        if is_bj_code(code):
            try:
                return fresh_fetch.fetch_a_kline_fresh(code, kline=kline, start=start, end=end)
            except Exception as err:
                raise RuntimeError(
                    f"北交所 {code} 行情暂不可用（{err}）。请稍后重试。"
                ) from err
        return fresh_fetch.fetch_a_kline_fresh(code, kline=kline, start=start, end=end)

    iv_map = {
        "日线": "1d",
        "日K": "1d",
        "周线": "1wk",
        "周K": "1wk",
        "月线": "1mo",
        "月K": "1mo",
    }
    iv = iv_map.get(kline, "1d")
    df = yahoo.fetch_history(code, start=start, end=end, interval=iv)
    return df, "Yahoo Finance"
