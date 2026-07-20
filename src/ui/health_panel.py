"""数据源连通性探测（P5）。"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Callable

import streamlit as st

from src.auth.users import current_user_id
from src.notify.health_alert import maybe_send_health_alert
from src.notify.push_log import read_recent
from src.util.fetch_cache import cache_stats


@dataclass(frozen=True)
class SourceHealth:
    name: str
    ok: bool
    detail: str


def _probe_eastmoney() -> SourceHealth:
    try:
        from src.providers import eastmoney

        hits = eastmoney.suggest("600519", limit=1)
        if hits:
            return SourceHealth("东财 A 股", True, "搜索正常")
        return SourceHealth("东财 A 股", False, "搜索无结果")
    except Exception as exc:
        return SourceHealth("东财 A 股", False, str(exc)[:60])


def _probe_yahoo() -> SourceHealth:
    try:
        from datetime import date, timedelta

        from src.providers import yahoo

        end = date.today()
        start = end - timedelta(days=10)
        df = yahoo.fetch_history("AAPL", start=start, end=end)
        if df is not None and not df.empty:
            return SourceHealth("Yahoo 港美", True, "AAPL 日线 ok")
        return SourceHealth("Yahoo 港美", False, "无数据")
    except Exception as exc:
        return SourceHealth("Yahoo 港美", False, str(exc)[:60])


def format_last_refresh_label(session_state: dict[str, Any]) -> str:
    """上次自选摘要刷新时间（P32）。"""
    label = session_state.get("query_label_watch") or session_state.get("_auto_refresh_at")
    return str(label).strip() if label else "—"


def format_cache_stats_line(stats: dict[str, Any]) -> str:
    count = int(stats.get("count") or 0)
    if count <= 0:
        return "摘要缓存：0 条（60s TTL）"
    entries = list(stats.get("entries") or [])
    tickers = sum(int(e.get("tickers") or 0) for e in entries)
    oldest = max((float(e.get("age_s") or 0) for e in entries), default=0.0)
    return f"摘要缓存：{count} 批 / {tickers} 只 · 最久 {oldest:.0f}s 前"


def format_push_log_tail(rows: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    """推送日志尾部格式化（P32）。"""
    out: list[str] = []
    for row in rows[: max(limit, 1)]:
        icon = "✓" if row.get("ok") else "✗"
        out.append(
            f"{row.get('at', '—')} {row.get('channel', '?')} {icon} {row.get('detail', '')}"
        )
    return out


@st.cache_data(ttl=120, show_spinner=False)
def probe_all_sources() -> tuple[dict[str, str], ...]:
    results = [_probe_eastmoney(), _probe_yahoo()]
    return tuple({"name": r.name, "ok": r.ok, "detail": r.detail} for r in results)


def render_health_panel(*, on_refresh: Callable[[], None] | None = None) -> None:
    with st.expander("🩺 数据源状态", expanded=False):
        if st.button("刷新检测", key="health_refresh", use_container_width=True):
            probe_all_sources.clear()
            if on_refresh:
                on_refresh()
            st.rerun()
        for row in probe_all_sources():
            icon = "🟢" if row["ok"] else "🔴"
            st.caption(f"{icon} **{row['name']}** — {row['detail']}")
        probes = list(probe_all_sources())
        app_url = os.environ.get("STOCK_APP_PUBLIC_URL", "").strip()
        try:
            import streamlit as _st

            v = _st.secrets.get("STOCK_APP_PUBLIC_URL")
            if v:
                app_url = str(v).strip()
        except Exception:
            pass
        ok, alert_msg = maybe_send_health_alert(probes, app_url=app_url)
        if ok:
            st.caption(f"⚠️ 已发送健康告警 Webhook：{alert_msg}")
        st.caption(format_cache_stats_line(cache_stats()))
        st.caption(f"上次摘要刷新：{format_last_refresh_label(dict(st.session_state))}")
        try:
            uid = current_user_id()
        except Exception:
            uid = str(st.session_state.get("_auth_user") or "default")
        tail = format_push_log_tail(read_recent(user_id=uid, limit=5))
        if tail:
            st.caption("最近推送：")
            for line in tail:
                st.caption(f"· {line}")
        st.caption("检测缓存 2 分钟；行情延迟以各数据源为准。")
