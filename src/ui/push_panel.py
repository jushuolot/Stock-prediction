"""Webhook / 邮件推送 UI（P8）。"""

from __future__ import annotations

import streamlit as st

from src.auth.users import auth_mode_label
from src.notify.digest_push import push_digest_all, recent_push_lines
from src.notify.email_digest import get_smtp_config
from src.notify.webhook import get_webhook_url


def render_push_panel() -> None:
    with st.expander("📣 推送速览", expanded=False):
        st.caption(f"身份：{auth_mode_label()}")
        wh = get_webhook_url()
        smtp = get_smtp_config()
        st.caption(
            "Webhook: "
            + ("已配置" if wh else "未配置")
            + " · 邮件: "
            + ("已配置" if smtp else "未配置")
            + " · 详见 docs/PUSH.md"
        )
        st.session_state.setdefault("push_webhook_on_refresh", False)
        st.session_state.setdefault("push_email_on_refresh", False)
        if wh:
            st.checkbox("自动刷新后推送 Webhook", key="push_webhook_on_refresh")
        if smtp:
            st.checkbox("自动刷新后发送邮件", key="push_email_on_refresh")
        if st.button("立即推送当前速览", key="push_now", use_container_width=True):
            with st.spinner("推送中…"):
                for line in push_digest_all():
                    if line.startswith("Webhook: ✓") or line.startswith("邮件: ✓"):
                        st.success(line)
                    elif "未配置" in line:
                        st.info(line)
                    else:
                        st.warning(line)
        for line in recent_push_lines(limit=5):
            st.caption(line)
