"""Google 财经对照价（非主数据源，解析公开页面 ds:14 块）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests

from src.providers.eastmoney import EM_HEADERS, SearchHit

_GF = "https://www.google.com/finance/quote/"
_HEADERS = {
    **EM_HEADERS,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass(frozen=True)
class GoogleFinanceQuote:
    symbol: str
    price: float
    change: float | None
    change_pct: float | None
    url: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "change": self.change,
            "change_pct": self.change_pct,
            "url": self.url,
        }


def google_finance_symbol(hit: SearchHit) -> str | None:
    """东财 SearchHit → Google Finance 代码（如 600519:SHA）。"""
    code = str(hit.code or "").strip().upper()
    yh = str(hit.yahoo or "").strip().upper()
    kind = str(hit.kind or "").upper()
    if kind == "A" or (code.isdigit() and len(code) == 6):
        c = code.zfill(6)
        if c.startswith("6"):
            return f"{c}:SHA"
        return f"{c}:SHE"
    if kind == "HK" or (code.isdigit() and len(code) <= 5):
        num = code.split(".")[0]
        if num.isdigit():
            return f"{int(num):04d}:HKG"
    if kind == "US" or yh:
        t = yh or code
        if re.fullmatch(r"[A-Z][A-Z0-9.\-]*", t):
            ex = "NASDAQ"
            if ".HK" in t:
                return None
            return f"{t.split('.')[0]}:{ex}"
    return None


def _walk_price_node(obj: Any) -> tuple[float, float, float] | None:
    if isinstance(obj, list) and len(obj) >= 6 and isinstance(obj[5], list):
        row = obj[5]
        if len(row) >= 3 and isinstance(row[0], (int, float)) and row[0] > 0:
            try:
                return float(row[0]), float(row[1]), float(row[2])
            except (TypeError, ValueError):
                pass
    if isinstance(obj, list):
        for x in obj:
            got = _walk_price_node(x)
            if got:
                return got
    return None


def fetch_google_finance_quote(symbol: str) -> GoogleFinanceQuote | None:
    sym = (symbol or "").strip()
    if not sym:
        return None
    url = f"{_GF}{sym}?hl=zh-CN"
    try:
        r = requests.get(url, headers=_HEADERS, timeout=14)
        r.raise_for_status()
        text = r.text
    except Exception:
        return None
    for key in ("ds:14", "ds:2"):
        m = re.search(
            rf"AF_initDataCallback\(\{{key: '{key}'.*?data:(\[.*?\])\s*, sideChannel",
            text,
            re.S,
        )
        if not m:
            continue
        try:
            arr = json.loads(m.group(1))
            got = _walk_price_node(arr)
            if got:
                price, chg, chg_pct = got
                return GoogleFinanceQuote(
                    symbol=sym,
                    price=round(price, 4),
                    change=round(chg, 4),
                    change_pct=round(chg_pct, 4),
                    url=url,
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
    return None


def compare_prices(primary: float | None, google: float | None, *, tol_pct: float = 1.5) -> str:
    """主源 vs Google 对照文案。"""
    if primary is None or google is None or google <= 0:
        return ""
    diff_pct = abs(primary - google) / google * 100.0
    if diff_pct <= tol_pct:
        return f"Google 对照 {google:.2f}（一致）"
    return f"Google 对照 {google:.2f}（偏差 {diff_pct:.1f}%）"
