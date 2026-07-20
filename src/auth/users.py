"""多用户密码与数据隔离（P8）。"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import streamlit as st

_SAFE_USER = re.compile(r"[^a-zA-Z0-9_-]")


def safe_user_id(raw: str) -> str:
    s = _SAFE_USER.sub("", str(raw or "").strip())[:32]
    return s or "default"


def _single_password() -> str | None:
    try:
        v = st.secrets.get("STOCK_ASSISTANT_PASSWORD")
        if v is not None and str(v).strip():
            return str(v).strip()
    except Exception:
        pass
    env = os.environ.get("STOCK_ASSISTANT_PASSWORD", "").strip()
    return env or None


def _multi_passwords() -> dict[str, str]:
    """secrets [passwords] 或环境变量 STOCK_ASSISTANT_USERS JSON。"""
    out: dict[str, str] = {}
    try:
        table = st.secrets.get("passwords")
        if isinstance(table, dict):
            for k, v in table.items():
                uid = safe_user_id(str(k))
                pw = str(v or "").strip()
                if pw:
                    out[uid] = pw
    except Exception:
        pass
    raw = os.environ.get("STOCK_ASSISTANT_USERS", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                for k, v in data.items():
                    uid = safe_user_id(str(k))
                    pw = str(v or "").strip()
                    if pw:
                        out[uid] = pw
        except json.JSONDecodeError:
            pass
    return out


def list_auth_users() -> dict[str, str]:
    multi = _multi_passwords()
    if multi:
        return multi
    single = _single_password()
    if single:
        return {"default": single}
    return {}


def verify_password(password: str) -> str | None:
    pw = (password or "").strip()
    if not pw:
        return None
    users = list_auth_users()
    for uid, expected in users.items():
        if pw == expected:
            return uid
    return None


def current_user_id() -> str:
    return safe_user_id(str(st.session_state.get("_auth_user") or "default"))


def auth_mode_label() -> str:
    users = list_auth_users()
    if len(users) > 1:
        return f"多用户（{len(users)} 组密码，数据隔离）"
    return "单用户"
