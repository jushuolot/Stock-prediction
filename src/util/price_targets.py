"""价格目标提醒（P46）：ticker -> {above, below} 可选浮点。"""

from __future__ import annotations

from typing import Any


def _parse_optional_float(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def normalize_price_targets(raw: Any) -> dict[str, dict[str, float | None]]:
    """ticker code -> {above?, below?}"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, float | None]] = {}
    for ticker, targets in raw.items():
        code = str(ticker or "").strip()
        if not code:
            continue
        if isinstance(targets, dict):
            above = _parse_optional_float(targets.get("above"))
            below = _parse_optional_float(targets.get("below"))
        else:
            above = below = None
        if above is not None or below is not None:
            out[code] = {"above": above, "below": below}
    return out


def get_targets(targets: dict[str, dict[str, float | None]], ticker: str) -> dict[str, float | None]:
    return dict(targets.get(str(ticker or "").strip(), {}))


def set_targets(
    targets: dict[str, dict[str, float | None]],
    ticker: str,
    *,
    above: float | None = None,
    below: float | None = None,
) -> dict[str, dict[str, float | None]]:
    code = str(ticker or "").strip()
    if not code:
        return dict(targets)
    out = dict(targets)
    a = _parse_optional_float(above)
    b = _parse_optional_float(below)
    if a is None and b is None:
        out.pop(code, None)
    else:
        out[code] = {"above": a, "below": b}
    return out


def remove_ticker_targets(
    targets: dict[str, dict[str, float | None]], ticker: str
) -> dict[str, dict[str, float | None]]:
    code = str(ticker or "").strip()
    if not code or code not in targets:
        return dict(targets)
    out = dict(targets)
    del out[code]
    return out
