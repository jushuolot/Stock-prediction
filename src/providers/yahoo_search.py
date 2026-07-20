"""Yahoo Finance 搜索（美股/港股等，补东财 suggest 缺口）。"""

from __future__ import annotations

import re
from typing import Any

import requests

from src.providers.eastmoney import SearchHit

_YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

# 公司英文名 / 旧名 → 代码
_NAME_ALIASES: dict[str, str] = {
    "synnex": "SNX",
    "td synnex": "SNX",
    "synnex corporation": "SNX",
    "apple": "AAPL",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "google": "GOOGL",
    "meta": "META",
}

_EXCHANGE_LABEL: dict[str, str] = {
    "NYQ": "NYSE",
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NCM": "NASDAQ",
    "PCX": "NYSE Arca",
    "BTS": "BATS",
    "HKG": "港股",
    "HKEX": "港股",
}


def _alias_ticker(keyword: str) -> str | None:
    k = (keyword or "").strip().lower()
    if k in _NAME_ALIASES:
        return _NAME_ALIASES[k]
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.\-]{0,9}", keyword.strip()):
        return keyword.strip().upper()
    return None


def _hit_from_quote(q: dict[str, Any]) -> SearchHit | None:
    sym = str(q.get("symbol") or "").strip().upper()
    if not sym:
        return None
    qtype = str(q.get("quoteType") or "").upper()
    if qtype and qtype not in ("EQUITY", "ETF"):
        return None
    name = str(q.get("longname") or q.get("shortname") or sym).strip()
    ex = str(q.get("exchange") or q.get("exchDisp") or "").strip()
    market = _EXCHANGE_LABEL.get(ex, ex or "海外")
    if sym.endswith(".HK") or ex in ("HKG", "HKEX"):
        kind, market = "HK", "港股"
    elif re.fullmatch(r"[A-Z][A-Z0-9.\-]*", sym) and not sym.endswith((".SS", ".SZ", ".BJ")):
        kind, market = "US", f"美股({market})" if market else "美股"
    else:
        kind, market = "OTHER", market or "其他"
    return SearchHit(code=sym, name=name, market=market, kind=kind, yahoo=sym)


def search_yahoo(keyword: str, *, limit: int = 15) -> list[SearchHit]:
    kw = (keyword or "").strip()
    if not kw:
        return []

    out: list[SearchHit] = []
    seen: set[str] = set()

    alias = _alias_ticker(kw)
    if alias and alias not in seen:
        try:
            import yfinance as yf

            info = yf.Ticker(alias).info or {}
            name = str(info.get("shortName") or info.get("longName") or alias)
            ex = str(info.get("exchange") or "")
            market = _EXCHANGE_LABEL.get(ex, ex or "美股")
            out.append(SearchHit(code=alias, name=name, market=f"美股({market})", kind="US", yahoo=alias))
            seen.add(alias)
        except Exception:
            out.append(
                SearchHit(code=alias, name=alias, market="美股", kind="US", yahoo=alias)
            )
            seen.add(alias)

    try:
        r = requests.get(
            _YAHOO_SEARCH,
            params={"q": kw, "quotesCount": str(limit), "newsCount": "0"},
            headers=_HEADERS,
            timeout=12,
        )
        r.raise_for_status()
        quotes = (r.json() or {}).get("quotes") or []
    except Exception:
        quotes = []

    for q in quotes:
        if not isinstance(q, dict):
            continue
        hit = _hit_from_quote(q)
        if not hit or hit.code in seen:
            continue
        seen.add(hit.code)
        out.append(hit)
        if len(out) >= limit:
            break
    return out[:limit]
