"""分析结果置顶（P55）：user_prefs.pinned_tickers，排序后仍置顶。"""

from __future__ import annotations

from typing import Any


def normalize_pinned_tickers(raw: Any) -> list[str]:
    """规范化 pinned_tickers 为去重代码列表（保留顺序）。"""
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        code = str(t or "").strip()
        if code and code not in seen:
            seen.add(code)
            out.append(code)
    return out


def is_pinned(pinned: list[str], ticker: str) -> bool:
    code = str(ticker or "").strip()
    return code in normalize_pinned_tickers(pinned)


def pin_ticker(pinned: list[str], ticker: str) -> list[str]:
    code = str(ticker or "").strip()
    norm = normalize_pinned_tickers(pinned)
    if not code or code in norm:
        return norm
    return norm + [code]


def unpin_ticker(pinned: list[str], ticker: str) -> list[str]:
    code = str(ticker or "").strip()
    return [c for c in normalize_pinned_tickers(pinned) if c != code]


def toggle_pin(pinned: list[str], ticker: str) -> list[str]:
    code = str(ticker or "").strip()
    if is_pinned(pinned, code):
        return unpin_ticker(pinned, code)
    return pin_ticker(pinned, code)


def apply_pinned_order(
    watchlist: list[dict[str, Any]],
    pinned: list[str],
) -> list[dict[str, Any]]:
    """置顶标的排在最前（按 pin 顺序），其余保持相对顺序。"""
    pin_list = normalize_pinned_tickers(pinned)
    if not pin_list:
        return list(watchlist)
    pin_index = {c: i for i, c in enumerate(pin_list)}
    pinned_items: list[tuple[int, dict[str, Any]]] = []
    rest: list[dict[str, Any]] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        if code in pin_index:
            pinned_items.append((pin_index[code], item))
        else:
            rest.append(item)
    pinned_items.sort(key=lambda x: x[0])
    return [item for _, item in pinned_items] + rest
