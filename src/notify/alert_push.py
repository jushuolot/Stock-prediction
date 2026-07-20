"""自选股提醒 Webhook 推送（P17）。"""

from __future__ import annotations

import hashlib
import os
from typing import Any

import streamlit as st

from src.analysis.watch_alerts import WatchAlert, alerts_to_markdown
from src.auth.users import current_user_id
from src.notify.push_log import record_push
from src.notify.retry import enqueue_retry, retry_with_backoff
from src.notify.webhook import get_webhook_url, post_webhook
from src.util.quiet_hours import is_in_quiet_hours, normalize_quiet_hours


def _app_url() -> str:
    try:
        v = st.secrets.get("STOCK_APP_PUBLIC_URL")
        if v:
            return str(v).strip()
    except Exception:
        pass
    return os.environ.get("STOCK_APP_PUBLIC_URL", "").strip()


def _uid(session_state: Any | None) -> str:
    if session_state is None:
        try:
            return current_user_id()
        except Exception:
            return "default"
    return str(session_state.get("_auth_user") or "default")


def alerts_fingerprint(alerts: list[WatchAlert]) -> str:
    parts = sorted(f"{a.code}:{a.kind}:{a.message}" for a in alerts)
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_alert_webhook_payload(
    alerts: list[WatchAlert],
    *,
    user_id: str = "default",
    app_url: str = "",
) -> dict[str, Any]:
    md = alerts_to_markdown(alerts, title="自选股提醒推送")
    return {
        "schema": "stock-assistant-webhook-v1",
        "kind": "watch_alerts",
        "user_id": user_id,
        "app_url": app_url,
        "alert_count": len(alerts),
        "digest_markdown": md,
        "text": md[:4000],
    }


def push_alerts_webhook(
    alerts: list[WatchAlert],
    *,
    session_state: Any | None = None,
) -> tuple[bool, str]:
    if not alerts:
        return False, "无提醒可推送"
    url = get_webhook_url()
    if not url:
        return False, "未配置 STOCK_WEBHOOK_URL"
    ss = session_state if session_state is not None else st.session_state
    uid = _uid(session_state)
    payload = build_alert_webhook_payload(alerts, user_id=uid, app_url=_app_url())

    def _post() -> tuple[bool, str]:
        return post_webhook(url, payload)

    ok, msg = retry_with_backoff(_post, max_attempts=3)
    record_push(channel="alert_webhook", ok=ok, detail=msg, user_id=uid, extra={"alert_count": len(alerts)})
    if not ok:
        enqueue_retry(
            {
                "channel": "alert_webhook",
                "alerts": [
                    {"code": a.code, "name": a.name, "kind": a.kind, "message": a.message, "level": a.level}
                    for a in alerts
                ],
                "session": {"_auth_user": uid},
            },
            user_id=uid,
        )
    ss["_last_alert_push_result"] = f"{'✓' if ok else '✗'} {msg}"
    return ok, msg


def _quiet_hours_from_session(ss: Any) -> dict[str, int | None]:
    if hasattr(ss, "get"):
        raw = ss.get("quiet_hours")
    else:
        raw = (ss or {}).get("quiet_hours")
    return normalize_quiet_hours(raw)


def maybe_push_alerts_if_configured(
    alerts: list[WatchAlert],
    *,
    session_state: Any | None = None,
    now: Any | None = None,
) -> tuple[bool, str] | None:
    """开启 push_webhook_on_alerts 且提醒集合变化时自动推送。"""
    ss = session_state if session_state is not None else st.session_state
    if not alerts or not ss.get("push_webhook_on_alerts"):
        return None
    if not get_webhook_url():
        return None
    if is_in_quiet_hours(_quiet_hours_from_session(ss), now=now):
        return None
    fp = alerts_fingerprint(alerts)
    if ss.get("_last_alert_push_fp") == fp:
        return None
    ok, msg = push_alerts_webhook(alerts, session_state=ss)
    if ok:
        ss["_last_alert_push_fp"] = fp
    return ok, msg
