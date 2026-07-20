"""自选股分组/标签（P19）。"""

from __future__ import annotations

from typing import Any


def normalize_watch_groups(raw: Any) -> dict[str, list[str]]:
    """group_name -> [ticker codes]"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for name, tickers in raw.items():
        g = str(name or "").strip()
        if not g:
            continue
        if not isinstance(tickers, list):
            continue
        codes = [str(t).strip() for t in tickers if str(t).strip()]
        if codes:
            out[g] = list(dict.fromkeys(codes))
    return out


def group_names(groups: dict[str, list[str]]) -> list[str]:
    return sorted(groups.keys())


def tickers_in_group(groups: dict[str, list[str]], group_name: str) -> set[str]:
    if not group_name or group_name == "全部":
        return set()
    return set(groups.get(group_name) or [])


def filter_watchlist_by_group(
    watchlist: list[dict[str, Any]],
    groups: dict[str, list[str]],
    group_name: str,
) -> list[dict[str, Any]]:
    if not group_name or group_name == "全部":
        return list(watchlist)
    allowed = tickers_in_group(groups, group_name)
    if not allowed:
        return []
    return [x for x in watchlist if str(x.get("代码") or "") in allowed]


def assign_ticker_to_group(
    groups: dict[str, list[str]],
    *,
    ticker: str,
    group_name: str,
) -> dict[str, list[str]]:
    code = str(ticker or "").strip()
    g = str(group_name or "").strip()
    if not code or not g:
        return dict(groups)
    out = {k: [c for c in v if c != code] for k, v in groups.items()}
    out.setdefault(g, [])
    if code not in out[g]:
        out[g].append(code)
    out = {k: v for k, v in out.items() if v}
    return out


def remove_ticker_from_all_groups(
    groups: dict[str, list[str]],
    ticker: str,
) -> dict[str, list[str]]:
    code = str(ticker or "").strip()
    if not code:
        return dict(groups)
    out = {k: [c for c in v if c != code] for k, v in groups.items()}
    return {k: v for k, v in out.items() if v}


def groups_for_ticker(groups: dict[str, list[str]], ticker: str) -> list[str]:
    code = str(ticker or "").strip()
    return sorted(g for g, codes in groups.items() if code in codes)
