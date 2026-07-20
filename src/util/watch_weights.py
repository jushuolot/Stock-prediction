"""组合权重（P49）：ticker -> weight %，仅展示用，UI 内归一化为饼图。"""

from __future__ import annotations

from typing import Any


def _parse_weight(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def normalize_watch_weights(raw: Any) -> dict[str, float]:
    """ticker code -> 原始权重百分比（未归一化）。"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for ticker, weight in raw.items():
        code = str(ticker or "").strip()
        w = _parse_weight(weight)
        if code and w is not None:
            out[code] = w
    return out


def get_weight(weights: dict[str, float], ticker: str) -> float | None:
    return weights.get(str(ticker or "").strip())


def set_weight(
    weights: dict[str, float],
    ticker: str,
    weight_pct: float | None,
) -> dict[str, float]:
    code = str(ticker or "").strip()
    if not code:
        return dict(weights)
    out = dict(weights)
    w = _parse_weight(weight_pct)
    if w is None:
        out.pop(code, None)
    else:
        out[code] = w
    return out


def remove_ticker_weights(weights: dict[str, float], ticker: str) -> dict[str, float]:
    code = str(ticker or "").strip()
    if not code or code not in weights:
        return dict(weights)
    out = dict(weights)
    del out[code]
    return out


def pie_slices_for_watchlist(
    watchlist: list[dict[str, Any]],
    weights: dict[str, float],
) -> list[dict[str, Any]]:
    """返回 [{code, name, raw, pct}]，pct 之和为 100；无权重时等权。"""
    items: list[tuple[str, str, float | None]] = []
    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if not code:
            continue
        name = str(item.get("名称") or code)
        items.append((code, name, get_weight(weights, code)))

    if not items:
        return []

    raw_values = [w for _, _, w in items if w is not None]
    if not raw_values:
        eq = 100.0 / len(items)
        return [
            {"code": code, "name": name, "raw": None, "pct": eq}
            for code, name, _ in items
        ]

    total = sum(w for _, _, w in items if w is not None)
    if total <= 0:
        eq = 100.0 / len(items)
        return [
            {"code": code, "name": name, "raw": None, "pct": eq}
            for code, name, _ in items
        ]

    slices: list[dict[str, Any]] = []
    for code, name, raw in items:
        if raw is None:
            slices.append({"code": code, "name": name, "raw": None, "pct": 0.0})
        else:
            slices.append(
                {
                    "code": code,
                    "name": name,
                    "raw": raw,
                    "pct": raw / total * 100.0,
                }
            )
    return slices
