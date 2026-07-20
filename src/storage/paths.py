"""用户数据文件路径（P8）。"""

from __future__ import annotations

import re
from pathlib import Path

_SAFE_USER = re.compile(r"[^a-zA-Z0-9_-]")


def safe_user_id(raw: str) -> str:
    s = _SAFE_USER.sub("", str(raw or "").strip())[:32]
    return s or "default"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def history_file_path(*, user_id: str = "default") -> Path:
    """每用户独立 history；default 兼容旧版 data/user_history.json。"""
    root = project_root()
    uid = safe_user_id(user_id)
    user_path = root / "data" / "users" / uid / "user_history.json"
    if uid == "default":
        legacy = root / "data" / "user_history.json"
        if legacy.exists() and not user_path.exists():
            return legacy
    user_path.parent.mkdir(parents=True, exist_ok=True)
    return user_path
