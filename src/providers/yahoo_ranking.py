"""Yahoo Finance 筛选器榜单（港股 / 美股）。"""

from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf
from yfinance import EquityQuery


def _region_query(region: str) -> EquityQuery:
    key = "hk" if region in ("HK", "港股") else "us"
    return EquityQuery("eq", ["region", key])


def _board_query(region_q: EquityQuery, board: str) -> tuple[EquityQuery, str, bool]:
    if board == "涨幅榜":
        return (
            EquityQuery("and", [region_q, EquityQuery("gt", ["percentchange", 0])]),
            "percentchange",
            False,
        )
    if board == "跌幅榜":
        return (
            EquityQuery("and", [region_q, EquityQuery("lt", ["percentchange", 0])]),
            "percentchange",
            True,
        )
    if board == "成交额榜":
        return EquityQuery("and", [region_q]), "dayvolume", False
    if board == "换手率榜":
        return EquityQuery("and", [region_q]), "percentchange", False
    return (
        EquityQuery("and", [region_q, EquityQuery("gt", ["percentchange", 0])]),
        "percentchange",
        False,
    )


def _market_label(region: str) -> str:
    return "港股" if region in ("HK", "港股") else "美股"


def _kind(region: str) -> str:
    return "HK" if region in ("HK", "港股") else "US"


def _parse_quote(item: dict[str, Any], *, region: str) -> dict[str, Any] | None:
    sym = str(item.get("symbol") or "").strip()
    if not sym:
        return None
    name = str(item.get("shortName") or item.get("longName") or sym).strip()

    def _f(*keys: str) -> float | None:
        for k in keys:
            v = item.get(k)
            if v is None:
                continue
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        return None

    price = _f("regularMarketPrice", "regularMarketPreviousClose")
    pct = _f("regularMarketChangePercent")
    chg = _f("regularMarketChange")
    vol = _f("regularMarketVolume", "volume", "dayvolume")
    mkt = _market_label(region)
    kind = _kind(region)
    return {
        "代码": sym,
        "名称": name,
        "市场": mkt,
        "类型": kind,
        "最新价": price,
        "涨跌幅%": pct,
        "涨跌额": chg,
        "成交量": vol,
        "成交额": None,
        "振幅%": None,
        "换手率%": None,
        "Yahoo代码": sym,
        "数据来源": "Yahoo Finance",
    }


def fetch_ranking(*, region: str, board: str = "涨幅榜", limit: int = 50) -> pd.DataFrame:
    """
    港股 / 美股榜单（Yahoo 筛选器）。
    region: HK / US 或 港股 / 美股
    """
    reg_key = "HK" if region in ("HK", "港股") else "US"
    region_q = _region_query(reg_key)
    query, sort_field, sort_asc = _board_query(region_q, board)
    size = max(10, min(int(limit), 100))
    try:
        payload = yf.screen(
            query,
            sortField=sort_field,
            sortAsc=sort_asc,
            size=size,
        )
    except Exception:
        return pd.DataFrame()

    quotes = payload.get("quotes") if isinstance(payload, dict) else None
    if not isinstance(quotes, list):
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in quotes:
        if not isinstance(item, dict):
            continue
        row = _parse_quote(item, region=reg_key)
        if row:
            rows.append(row)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)
