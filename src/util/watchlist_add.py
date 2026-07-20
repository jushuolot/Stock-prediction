"""搜索命中 → 自选股条目（P58 快捷添加）。"""

from __future__ import annotations

from typing import Any

from src.providers import eastmoney
from src.util.currency import enrich_watchlist_item, infer_currency_for_hit


def effective_code(h: eastmoney.SearchHit) -> str:
    code = h.code
    if h.kind in ("US", "HK") and h.yahoo:
        return h.yahoo
    return code


def hit_to_watchlist_item(h: eastmoney.SearchHit) -> dict[str, Any]:
    code = effective_code(h)
    yahoo_code = h.yahoo
    kind = h.kind
    return enrich_watchlist_item(
        {
            "名称": h.name,
            "代码": code,
            "类型": kind,
            "市场": h.market,
            "Yahoo": yahoo_code,
            "货币": infer_currency_for_hit(
                kind=kind, market=h.market, code=code, yahoo=yahoo_code or ""
            ),
        }
    )


def is_in_watchlist(watchlist: list[dict[str, Any]], code: str) -> bool:
    c = str(code or "").strip()
    if not c:
        return False
    return any(str(x.get("代码") or "").strip() == c for x in watchlist)


def add_hit_to_watchlist(
    watchlist: list[dict[str, Any]],
    h: eastmoney.SearchHit,
) -> tuple[list[dict[str, Any]], bool]:
    """返回 (新列表, 是否新增)。已存在则原样返回 added=False。"""
    item = hit_to_watchlist_item(h)
    if is_in_watchlist(watchlist, item["代码"]):
        return list(watchlist), False
    return list(watchlist) + [item], True
