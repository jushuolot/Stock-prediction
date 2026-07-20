"""数据源故障 Webhook 告警（P9）。"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

from src.notify.webhook import post_webhook
from src.storage.paths import project_root, safe_user_id


def get_health_alert_webhook_url() -> str | None:
    url = ""
    if st is not None:
        try:
            v = st.secrets.get("STOCK_HEALTH_ALERT_WEBHOOK_URL")
            if v:
                url = str(v).strip()
        except Exception:
            pass
    if not url:
        url = os.environ.get("STOCK_HEALTH_ALERT_WEBHOOK_URL", "").strip()
    return url or None


def _state_path(*, user_id: str = "default") -> Path:
    uid = safe_user_id(user_id)
    p = project_root() / "data" / "users" / uid / "health_alert_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_state(*, user_id: str = "default") -> dict[str, Any]:
    p = _state_path(user_id=user_id)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict[str, Any], *, user_id: str = "default") -> None:
    _state_path(user_id=user_id).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def maybe_send_health_alert(
    probes: list[dict[str, Any]],
    *,
    user_id: str = "default",
    app_url: str = "",
    debounce_seconds: int = 1800,
) -> tuple[bool, str]:
    url = get_health_alert_webhook_url()
    if not url:
        return False, "未配置 HEALTH_ALERT_WEBHOOK"
    failed = [p for p in probes if not p.get("ok")]
    state = _load_state(user_id=user_id)
    now = time.time()
    fingerprint = "|".join(f"{p.get('name')}:{p.get('detail')}" for p in failed)
    if not failed:
        if state.get("last_failed"):
            state["last_failed"] = False
            state["recovered_at"] = now
            _save_state(state, user_id=user_id)
        return False, "全部正常"
    last_fp = str(state.get("fingerprint") or "")
    last_at = float(state.get("alert_at") or 0)
    if fingerprint == last_fp and (now - last_at) < debounce_seconds:
        return False, "告警已发送（防抖）"
    payload = {
        "schema": "stock-assistant-health-alert-v1",
        "user_id": safe_user_id(user_id),
        "app_url": app_url,
        "failed": failed,
        "text": "数据源异常：" + "；".join(f"{p.get('name')} {p.get('detail')}" for p in failed),
    }
    ok, msg = post_webhook(url, payload)
    if ok:
        state.update({"fingerprint": fingerprint, "alert_at": now, "last_failed": True})
        _save_state(state, user_id=user_id)
    return ok, msg
