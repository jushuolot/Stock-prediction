"""自选股排序偏好（P43）：持久化到 user_prefs。"""

from __future__ import annotations

from typing import Any

SORT_BY_UI = {"代码": "name", "涨跌幅": "pct", "评分": "score"}
SORT_BY_PREF_TO_UI = {"name": "代码", "pct": "涨跌幅", "score": "评分"}
SORT_UI_OPTIONS = list(SORT_BY_UI.keys())


def normalize_watch_sort(raw: Any) -> dict[str, Any]:
    """规范化 watch_sort：by ∈ {score,pct,name}，desc 布尔。"""
    if not isinstance(raw, dict):
        raw = {}
    by = str(raw.get("by") or "name").strip().lower()
    if by not in SORT_BY_PREF_TO_UI:
        by = "name"
    return {"by": by, "desc": bool(raw.get("desc", False))}


def ui_sort_by(pref_by: str) -> str:
    return SORT_BY_PREF_TO_UI.get(str(pref_by or "name"), "代码")


def pref_sort_by(ui_by: str) -> str:
    return SORT_BY_UI.get(str(ui_by or "代码"), "name")


def prefs_from_ui(ui_by: str, descending: bool) -> dict[str, Any]:
    return {"by": pref_sort_by(ui_by), "desc": bool(descending)}


def apply_watch_sort_to_session(prefs: dict[str, Any] | Any) -> dict[str, Any]:
    """将规范化偏好转为 UI 控件初值（by 中文、desc 布尔）。"""
    norm = normalize_watch_sort(prefs)
    return {"by_ui": ui_sort_by(norm["by"]), "desc": norm["desc"]}
