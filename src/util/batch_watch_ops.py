"""自选股批量操作（P26）。"""

from __future__ import annotations

from typing import Any

from src.util.watch_groups import assign_ticker_to_group, remove_ticker_from_all_groups


def normalize_ticker_codes(codes: list[str] | set[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in codes:
        code = str(raw or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


def batch_remove_from_watchlist(
    watchlist: list[dict[str, Any]],
    codes: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """从自选列表移除指定代码，返回 (新列表, 实际移除的代码)。"""
    remove_set = set(normalize_ticker_codes(codes))
    if not remove_set:
        return list(watchlist), []
    kept: list[dict[str, Any]] = []
    removed: list[str] = []
    for item in watchlist:
        code = str(item.get("代码") or "").strip()
        if code and code in remove_set:
            removed.append(code)
        else:
            kept.append(item)
    return kept, removed


def batch_remove_from_groups(
    groups: dict[str, list[str]],
    codes: list[str],
) -> dict[str, list[str]]:
    out = dict(groups)
    for code in normalize_ticker_codes(codes):
        out = remove_ticker_from_all_groups(out, code)
    return out


def batch_add_to_group(
    groups: dict[str, list[str]],
    codes: list[str],
    group_name: str,
) -> dict[str, list[str]]:
    """批量将标的加入同一分组（单分组内去重）。"""
    g = str(group_name or "").strip()
    if not g:
        return dict(groups)
    out = dict(groups)
    for code in normalize_ticker_codes(codes):
        out = assign_ticker_to_group(out, ticker=code, group_name=g)
    return out


def codes_in_watchlist(watchlist: list[dict[str, Any]], codes: list[str]) -> list[str]:
    """仅保留当前自选列表中存在的代码。"""
    existing = {str(x.get("代码") or "").strip() for x in watchlist if x.get("代码")}
    return [c for c in normalize_ticker_codes(codes) if c in existing]
