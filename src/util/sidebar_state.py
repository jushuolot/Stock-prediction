"""侧边栏折叠状态（P71）：user_prefs.sidebar_collapsed 各区块记忆。"""

from __future__ import annotations

from typing import Any

KNOWN_SECTIONS = frozenset({"workflow_phase", "capability_map", "playbook_preview"})


def normalize_sidebar_collapsed(raw: Any) -> dict[str, bool]:
    """section -> True 表示默认折叠。"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, bool] = {}
    for key, val in raw.items():
        section = str(key or "").strip()
        if section and section in KNOWN_SECTIONS:
            out[section] = bool(val)
    return out


def is_section_collapsed(
    collapsed: dict[str, bool],
    section: str,
    *,
    default: bool = False,
) -> bool:
    name = str(section or "").strip()
    if not name:
        return default
    return bool(collapsed.get(name, default))


def set_section_collapsed(
    collapsed: dict[str, bool],
    section: str,
    is_collapsed: bool,
) -> dict[str, bool]:
    name = str(section or "").strip()
    if not name or name not in KNOWN_SECTIONS:
        return dict(collapsed)
    out = dict(collapsed)
    if is_collapsed:
        out[name] = True
    else:
        out.pop(name, None)
    return out
