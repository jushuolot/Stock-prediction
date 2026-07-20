"""工作台 expander 深链接（P94）：?tab=watch&expand= 与会话一次性展开。"""

from __future__ import annotations

from typing import Any

CAPABILITY_EXPAND_KEYS: frozenset[str] = frozenset(
    {
        "sector_relative",
        "institutional_onepager",
        "battle_plan",
        "priority_queue",
    }
)

_SESSION_PREFIX = "watch_expand_"


def capability_watch_href(module: str) -> str:
    """能力地图条目跳转链接。"""
    key = (module or "").strip()
    if key not in CAPABILITY_EXPAND_KEYS:
        return "?tab=watch"
    return f"?tab=watch&expand={key}"


def apply_watch_expand_from_query(session_state: Any, query_params: Any) -> str | None:
    """读取 ?expand= 写入一次性展开 session key，并切到工作台 Tab。"""
    raw = query_params.get("expand", "")
    if not raw:
        return None
    key = str(raw).strip()
    if key not in CAPABILITY_EXPAND_KEYS:
        return None
    session_state[f"{_SESSION_PREFIX}{key}"] = True
    session_state["active_tab"] = "watch"
    return key


def watch_section_expanded(
    session_state: Any,
    section: str,
    *,
    default: bool = False,
) -> bool:
    """若深链接请求展开该区块，返回 True 并清除一次性标记。"""
    flag = f"{_SESSION_PREFIX}{section}"
    if session_state.get(flag):
        session_state.pop(flag, None)
        return True
    return default
