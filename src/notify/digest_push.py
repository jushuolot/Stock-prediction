"""推送自选股速览（Webhook / 邮件）。"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import streamlit as st

from src.analysis.daily_digest import build_watchlist_digest
from src.analysis.watch_alerts import compute_watch_alerts
from src.util.price_targets import normalize_price_targets
from src.auth.users import current_user_id
from src.notify.email_digest import get_smtp_config, send_digest_email
from src.notify.push_log import read_recent, record_push
from src.notify.retry import enqueue_retry, retry_with_backoff
from src.notify.webhook import build_webhook_payload, get_webhook_url, post_webhook


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


def format_digest_email_subject(
    *,
    alert_count: int = 0,
    watch_count: int = 0,
    when: datetime | None = None,
) -> str:
    """汇总邮件主题：日期 + 提醒条数（P59）。"""
    day = (when or datetime.now()).strftime("%Y-%m-%d")
    base = f"Stock Assistant · 自选股速览 · {day}"
    if alert_count > 0:
        return f"{base} · {alert_count} 条提醒"
    if watch_count > 0:
        return f"{base} · {watch_count} 只"
    return base


def alert_count_for_session(session_state: Any) -> int:
    wl = list(session_state.get("watchlist") or [])
    snaps = dict(session_state.get("watch_snapshots") or {})
    if not wl:
        return 0
    alerts = compute_watch_alerts(
        wl,
        snaps,
        pct_up=float(session_state.get("alert_pct_up") or 5.0),
        pct_down=float(session_state.get("alert_pct_down") or -5.0),
        score_low=float(session_state.get("alert_score_low") or 40.0),
        score_high=float(session_state.get("alert_score_high") or 65.0),
        price_targets=normalize_price_targets(session_state.get("price_targets") or {}),
    )
    return len(alerts)


def build_current_digest(session_state: Any | None = None) -> str:
    ss = session_state if session_state is not None else st.session_state
    wl = list(ss.get("watchlist") or [])
    snaps = dict(ss.get("watch_snapshots") or {})
    label = str(ss.get("query_label_watch") or ss.get("_auto_refresh_at") or "")
    notes = dict(ss.get("watch_notes") or {})
    return build_watchlist_digest(wl, snaps, query_label=label, watch_notes=notes)


def push_digest_webhook(*, digest: str, session_state: Any | None = None) -> tuple[bool, str]:
    url = get_webhook_url()
    if not url:
        return False, "未配置 STOCK_WEBHOOK_URL"
    ss = session_state if session_state is not None else st.session_state
    uid = _uid(session_state)
    payload = build_webhook_payload(
        digest_markdown=digest,
        watchlist=list(ss.get("watchlist") or []),
        snapshots=dict(ss.get("watch_snapshots") or {}),
        user_id=uid,
        app_url=_app_url(),
    )

    def _post() -> tuple[bool, str]:
        return post_webhook(url, payload)

    ok, msg = retry_with_backoff(_post, max_attempts=3)
    record_push(channel="webhook", ok=ok, detail=msg, user_id=uid)
    if not ok:
        enqueue_retry(
            {
                "channel": "webhook",
                "digest": digest,
                "session": {
                    "watchlist": list(ss.get("watchlist") or []),
                    "watch_snapshots": dict(ss.get("watch_snapshots") or {}),
                    "_auth_user": uid,
                },
            },
            user_id=uid,
        )
    return ok, msg


def push_digest_email(
    *,
    digest: str,
    session_state: Any | None = None,
    alert_count: int | None = None,
) -> tuple[bool, str]:
    uid = _uid(session_state)
    ss = session_state if session_state is not None else st.session_state
    wl = list(ss.get("watchlist") or [])
    n_alerts = alert_count if alert_count is not None else alert_count_for_session(ss)
    subject = format_digest_email_subject(alert_count=n_alerts, watch_count=len(wl))

    def _send() -> tuple[bool, str]:
        return send_digest_email(subject=subject, body=digest)

    ok, msg = retry_with_backoff(_send, max_attempts=3)
    record_push(channel="email", ok=ok, detail=msg, user_id=uid)
    if not ok:
        enqueue_retry({"channel": "email", "digest": digest, "session": {"_auth_user": uid}}, user_id=uid)
    return ok, msg


def push_digest_all(session_state: Any | None = None) -> list[str]:
    digest = build_current_digest(session_state)
    if not digest.strip():
        return ["无自选股数据"]
    lines: list[str] = []
    if get_webhook_url():
        ok, msg = push_digest_webhook(digest=digest, session_state=session_state)
        lines.append(f"Webhook: {'✓' if ok else '✗'} {msg}")
    if get_smtp_config():
        ok, msg = push_digest_email(digest=digest, session_state=session_state)
        lines.append(f"邮件: {'✓' if ok else '✗'} {msg}")
    if len(lines) == 0:
        lines.append("未配置 Webhook 或 SMTP，见 docs/PUSH.md")
    return lines


def maybe_push_after_refresh(session_state: Any | None = None) -> None:
    ss = session_state if session_state is not None else st.session_state
    if not ss.get("push_webhook_on_refresh") and not ss.get("push_email_on_refresh"):
        return
    digest = build_current_digest(ss)
    results: list[str] = []
    if ss.get("push_webhook_on_refresh") and get_webhook_url():
        ok, msg = push_digest_webhook(digest=digest, session_state=ss)
        results.append(f"Webhook: {'✓' if ok else '✗'} {msg}")
    if ss.get("push_email_on_refresh") and get_smtp_config():
        ok, msg = push_digest_email(digest=digest, session_state=ss)
        results.append(f"邮件: {'✓' if ok else '✗'} {msg}")
    ss["_last_push_results"] = results


def recent_push_lines(*, user_id: str | None = None, limit: int = 5) -> list[str]:
    uid = user_id or _uid(None)
    rows = read_recent(user_id=uid, limit=limit)
    out: list[str] = []
    for r in rows:
        icon = "✓" if r.get("ok") else "✗"
        out.append(f"{r.get('at')} {r.get('channel')} {icon} {r.get('detail')}")
    return out

