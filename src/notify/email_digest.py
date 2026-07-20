"""SMTP 邮件推送速览（P8，stdlib）。"""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore


def get_smtp_config() -> dict[str, Any] | None:
    cfg: dict[str, Any] = {}
    if st is not None:
        try:
            block = st.secrets.get("smtp")
            if isinstance(block, dict):
                cfg.update(block)
        except Exception:
            pass
    for key, env in (
        ("host", "STOCK_SMTP_HOST"),
        ("user", "STOCK_SMTP_USER"),
        ("password", "STOCK_SMTP_PASSWORD"),
        ("to", "STOCK_SMTP_TO"),
        ("from", "STOCK_SMTP_FROM"),
    ):
        if not cfg.get(key):
            val = os.environ.get(env, "").strip()
            if val:
                cfg[key] = val
    port = cfg.get("port") or os.environ.get("STOCK_SMTP_PORT", "587")
    try:
        cfg["port"] = int(port)
    except (TypeError, ValueError):
        cfg["port"] = 587
    host = str(cfg.get("host") or "").strip()
    to_addr = str(cfg.get("to") or "").strip()
    if not host or not to_addr:
        return None
    return cfg


def send_digest_email(
    *,
    subject: str,
    body: str,
    config: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    cfg = config or get_smtp_config()
    if not cfg:
        return False, "未配置 SMTP（host / to）"
    host = str(cfg["host"])
    port = int(cfg.get("port") or 587)
    user = str(cfg.get("user") or "")
    password = str(cfg.get("password") or "")
    to_addr = str(cfg["to"])
    from_addr = str(cfg.get("from") or user or to_addr)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if port == 587:
                server.starttls()
                server.ehlo()
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        return True, f"已发送至 {to_addr}"
    except Exception as exc:
        return False, str(exc)[:200]
