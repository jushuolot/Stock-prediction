"""最近查看标的（P68）：user_prefs.recent_viewed，最多 10 条。"""

from __future__ import annotations

from typing import Any

RECENT_VIEWED_MAX = 10
RECENT_CHIP_DISPLAY = 6
RECENT_CHIP_ROW = 3


def normalize_recent_viewed(raw: Any) -> list[dict[str, str]]:
    """去重、去空、保序（最新在前）。"""
    if not isinstance(raw, list):
        return []
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            code = str(item.get("code") or item.get("代码") or "").strip()
            name = str(item.get("name") or item.get("名称") or code).strip()
        else:
            code = str(item or "").strip()
            name = code
        if not code or code in seen:
            continue
        seen.add(code)
        out.append({"code": code, "name": name})
    return out[:RECENT_VIEWED_MAX]


def push_recent_viewed(
    history: list[dict[str, str]] | Any,
    *,
    code: str,
    name: str = "",
) -> list[dict[str, str]]:
    """将标的插入队首，最多保留 RECENT_VIEWED_MAX 条。"""
    ticker = str(code or "").strip()
    base = normalize_recent_viewed(history)
    if not ticker:
        return base
    label = str(name or ticker).strip() or ticker
    rest = [x for x in base if x.get("code") != ticker]
    return ([{"code": ticker, "name": label}] + rest)[:RECENT_VIEWED_MAX]


def push_recent_viewed_many(
    history: list[dict[str, str]] | Any,
    entries: list[tuple[str, str]],
) -> list[dict[str, str]]:
    """按时间顺序写入多条（后者更新、排在更前）。"""
    out = normalize_recent_viewed(history)
    for code, name in entries:
        out = push_recent_viewed(out, code=code, name=name)
    return out


def chip_label(entry: dict[str, str]) -> str:
    code = str(entry.get("code") or "")
    name = str(entry.get("name") or code)
    if name and name != code:
        return f"{name} ({code})"
    return code
