"""报价货币推断与汇率换算。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

CURRENCY_META: dict[str, tuple[str, str]] = {
    "CNY": ("人民币", "¥"),
    "HKD": ("港元", "HK$"),
    "USD": ("美元", "$"),
    "JPY": ("日元", "¥"),
    "EUR": ("欧元", "€"),
}

# 离线兜底（相对 1 USD）
FALLBACK_USD_RATES: dict[str, float] = {
    "USD": 1.0,
    "CNY": 7.25,
    "HKD": 7.82,
    "JPY": 156.0,
    "EUR": 0.92,
}

FX_URL = "https://api.frankfurter.app/latest"


def infer_currency(*, kind: str = "", market: str = "", code: str = "", yahoo: str = "") -> str:
    k = str(kind or "").upper()
    m = str(market or "")
    c = str(code or yahoo or "").upper()
    if k == "HK" or ".HK" in c or "港" in m:
        return "HKD"
    if k == "US" or "美" in m:
        return "USD"
    if k == "A":
        return "CNY"
    if c.endswith((".SS", ".SZ", ".BJ")):
        return "CNY"
    if c.isdigit() and len(c.split(".")[0]) <= 6:
        return "CNY"
    if "." in c and not c.endswith((".SS", ".SZ", ".BJ", ".HK")):
        return "USD"
    return "CNY"


def currency_display(code: str) -> str:
    c = str(code or "CNY").upper()
    name, _ = CURRENCY_META.get(c, (c, c))
    return f"{name} ({c})"


def infer_currency_for_hit(**kwargs: Any) -> str:
    return infer_currency(**kwargs)


def enrich_watchlist_item(item: dict[str, Any]) -> dict[str, Any]:
    return ensure_watchlist_currency(item)


def normalize_watchlist(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ensure_watchlist_currency(x) for x in items]


def ensure_watchlist_currency(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    stored = str(out.get("货币") or "").strip().upper()
    if stored in CURRENCY_META:
        out["货币"] = stored
    else:
        out["货币"] = infer_currency(
            kind=str(out.get("类型") or ""),
            market=str(out.get("市场") or ""),
            code=str(out.get("代码") or ""),
            yahoo=str(out.get("Yahoo") or ""),
        )
    return out


def infer_currency_from_item(item: dict[str, Any] | None) -> str:
    if not item:
        return "CNY"
    return ensure_watchlist_currency(item)["货币"]


def infer_currency_for_hit(*, kind: str, market: str = "", code: str = "", yahoo: str = "") -> str:
    return infer_currency(kind=kind, market=market, code=code, yahoo=yahoo)


def enrich_watchlist_item(item: dict[str, Any]) -> dict[str, Any]:
    return ensure_watchlist_currency(item)


def normalize_watchlist(watchlist: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [ensure_watchlist_currency(x) for x in watchlist]


def fetch_fx_rates() -> tuple[dict[str, float], str, bool]:
    """
    返回 (各币种相对 USD 的汇率, 更新时间文案, 是否来自实时接口)。
    """
    try:
        r = requests.get(FX_URL, params={"from": "USD"}, timeout=8)
        r.raise_for_status()
        data = r.json()
        rates = {k.upper(): float(v) for k, v in (data.get("rates") or {}).items()}
        rates["USD"] = 1.0
        when = str(data.get("date") or "")
        ts = f"{when} (Frankfurter)" if when else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return rates, ts, True
    except Exception:
        return dict(FALLBACK_USD_RATES), "内置参考汇率（接口不可用）", False


def convert_amount(
    amount: float,
    from_ccy: str,
    to_ccy: str,
    rates_usd: dict[str, float],
) -> float | None:
    f = str(from_ccy or "").upper()
    t = str(to_ccy or "").upper()
    if f == t:
        return float(amount)
    rf = rates_usd.get(f)
    rt = rates_usd.get(t)
    if not rf or not rt:
        return None
    usd = float(amount) / rf
    return usd * rt
