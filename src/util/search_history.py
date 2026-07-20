"""搜索历史（P34）：最近关键词持久化到 user_prefs。"""

from __future__ import annotations

from typing import Any

SEARCH_HISTORY_MAX = 20


def normalize_search_history(raw: Any) -> list[str]:
    """去重、去空、保序（最新在前）。"""
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        term = str(item or "").strip()
        if not term or term in seen:
            continue
        seen.add(term)
        out.append(term)
    return out[:SEARCH_HISTORY_MAX]


def push_search(history: list[str] | Any, keyword: str) -> list[str]:
    """将关键词插入队首，最多保留 SEARCH_HISTORY_MAX 条。"""
    term = str(keyword or "").strip()
    base = normalize_search_history(history)
    if not term:
        return base
    rest = [x for x in base if x != term]
    return ([term] + rest)[:SEARCH_HISTORY_MAX]


def remove_search_term(history: list[str] | Any, keyword: str) -> list[str]:
    term = str(keyword or "").strip()
    if not term:
        return normalize_search_history(history)
    return [x for x in normalize_search_history(history) if x != term]
