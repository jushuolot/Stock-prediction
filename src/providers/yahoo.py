from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class YahooProfile:
    ticker: str
    name: str
    exchange: str
    currency: str
    market_cap: Optional[float]
    sector: str
    industry: str
    website: str
    long_business_summary: str


def fetch_history(ticker: str, *, start: date, end: date, interval: str = "1d") -> pd.DataFrame:
    t = yf.Ticker(ticker)
    df = t.history(start=start.isoformat(), end=end.isoformat(), interval=interval, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(f"未获取到行情：{ticker}")
    df = df.rename_axis("日期").reset_index()
    df = df.rename(
        columns={
            "Open": "开盘",
            "High": "最高",
            "Low": "最低",
            "Close": "收盘",
            "Adj Close": "复权收盘",
            "Volume": "成交量",
            "Dividends": "分红",
            "Stock Splits": "拆并股",
        }
    )
    df["标的代码"] = ticker.upper()
    df["数据来源"] = "Yahoo Finance"
    return df


def _ticker_info(t: yf.Ticker) -> dict[str, Any]:
    try:
        if hasattr(t, "get_info"):
            raw = t.get_info()
            if isinstance(raw, dict):
                return raw
    except Exception:
        pass
    try:
        raw = t.info
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def fetch_profile(ticker: str) -> YahooProfile:
    t = yf.Ticker(ticker)
    info = _ticker_info(t)
    name = str(info.get("shortName") or info.get("longName") or ticker).strip()
    return YahooProfile(
        ticker=ticker.upper(),
        name=name,
        exchange=str(info.get("exchange") or ""),
        currency=str(info.get("currency") or ""),
        market_cap=info.get("marketCap"),
        sector=str(info.get("sector") or ""),
        industry=str(info.get("industry") or ""),
        website=str(info.get("website") or ""),
        long_business_summary=str(info.get("longBusinessSummary") or ""),
    )


def fetch_news(ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    t = yf.Ticker(ticker)
    try:
        news = t.news or []
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for item in news[:limit]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "标题": str(item.get("title") or "").strip(),
                "来源": str(item.get("publisher") or "").strip(),
                "链接": str(item.get("link") or "").strip(),
                "时间": item.get("providerPublishTime"),
                "摘要": str(item.get("summary") or "").strip(),
            }
        )
    return out

