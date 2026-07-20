"""多源新闻聚合（公开接口）。"""

from __future__ import annotations

import re
from typing import Any

import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.eastmoney.com/",
}


def _a_exchange_prefix(code6: str) -> str:
    from src.providers.ticker_util import is_bj_code

    c = str(code6).zfill(6)
    if c[0] == "6":
        return "SH"
    if is_bj_code(c):
        return "BJ"
    return "SZ"


def fetch_em_stock_news(code6: str, limit: int = 12) -> list[dict[str, Any]]:
    """东方财富个股新闻（PC 公告/资讯页接口）。"""
    ex = _a_exchange_prefix(code6)
    url = "https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/PageAjax"
    params = {"code": f"{ex}{str(code6).zfill(6)}", "page": 1, "pageSize": limit}
    try:
        r = requests.get(url, params=params, headers=_HEADERS, timeout=8)
        r.raise_for_status()
        j = r.json()
    except Exception:
        return []
    items = j.get("data") or j.get("list") or []
    if not isinstance(items, list):
        return []
    out: list[dict[str, Any]] = []
    for it in items[:limit]:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title") or it.get("Title") or "").strip()
        if not title:
            continue
        out.append(
            {
                "标题": title,
                "时间": str(it.get("date") or it.get("showTime") or ""),
                "来源": "东方财富",
                "链接": str(it.get("url") or it.get("art_url") or "").strip(),
                "摘要": str(it.get("digest") or it.get("summary") or "").strip(),
            }
        )
    return out


def fetch_aggregated_news(
    *,
    code6: str | None = None,
    yahoo_ticker: str | None = None,
    limit: int = 15,
) -> list[dict[str, Any]]:
    from src.providers import yahoo

    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    if code6 and code6.isdigit() and len(code6) == 6:
        for n in fetch_em_stock_news(code6, limit=limit):
            t = n.get("标题") or ""
            if t in seen:
                continue
            seen.add(t)
            out.append(n)

    if yahoo_ticker:
        for n in yahoo.fetch_news(yahoo_ticker, limit=limit):
            t = n.get("标题") or ""
            if t in seen:
                continue
            seen.add(t)
            out.append(n)

    return out[:limit]
