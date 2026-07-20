"""Webhook 推送自选股速览（P8）。"""

from __future__ import annotations

import json
import os
from typing import Any

import requests

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore


def get_webhook_url() -> str | None:
    url = ""
    if st is not None:
        try:
            v = st.secrets.get("STOCK_WEBHOOK_URL")
            if v:
                url = str(v).strip()
        except Exception:
            pass
    if not url:
        url = os.environ.get("STOCK_WEBHOOK_URL", "").strip()
    return url or None


def build_webhook_payload(
    *,
    digest_markdown: str,
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    user_id: str = "default",
    app_url: str = "",
) -> dict[str, Any]:
    return {
        "schema": "stock-assistant-webhook-v1",
        "user_id": user_id,
        "app_url": app_url,
        "watchlist_count": len(watchlist),
        "snapshot_count": len(snapshots),
        "digest_markdown": digest_markdown,
        "text": digest_markdown[:4000],
    }


def post_webhook(url: str, payload: dict[str, Any], *, timeout: int = 15) -> tuple[bool, str]:
    target = (url or "").strip()
    if not target:
        return False, "未配置 Webhook URL"
    try:
        r = requests.post(
            target,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=timeout,
        )
        if r.status_code >= 400:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        return True, f"HTTP {r.status_code}"
    except Exception as exc:
        return False, str(exc)[:200]
