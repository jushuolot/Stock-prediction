from __future__ import annotations

import hashlib
import io
import os
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import streamlit as st

from src.analysis.mover_insight import (
    ActionRouteReport,
    build_action_route_report,
    build_action_route_report_from_snapshot,
)
from src.analysis.capital_attribution import CapitalMix, capital_mix_from_dict
from src.analysis.global_anomaly import analyze_movers_batch
from src.analysis.signals import score_stock
from src.providers import eastmoney, market_data, symbol_search, yahoo
from src.providers.ticker_util import a_market_label, is_bj_code, yahoo_ticker_a
from src.auth.users import auth_mode_label, list_auth_users, verify_password
from src.storage.history_store import mark_dirty, persist_session
from src.storage.serialize import capital_mix_to_dict, route_report_from_session
from src.util.currency import normalize_watchlist
from src.util.watchlist_add import add_hit_to_watchlist
from src.util.query_time import format_data_range, format_query_date, format_query_datetime

def _get_password() -> str | None:
    users = list_auth_users()
    if not users:
        return None
    if len(users) == 1:
        return next(iter(users.values()))
    return None


def _login_gate() -> None:
    users = list_auth_users()
    if not users:
        st.title("访问验证")
        st.error(
            "尚未配置访问密码。请先设置后再启动：\n\n"
            "- 复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml` 并修改密码；或\n"
            "- 终端里执行：`export STOCK_ASSISTANT_PASSWORD='你的强密码'` 后再启动。"
        )
        st.stop()

    if "_auth_ok" not in st.session_state:
        st.session_state["_auth_ok"] = False

    if st.session_state["_auth_ok"]:
        return

    st.title("访问验证")
    if len(users) > 1:
        st.caption(auth_mode_label() + " — 不同密码对应不同自选股数据。")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            pw = st.text_input("访问密码", type="password")
            ok = st.form_submit_button("登录", type="primary", use_container_width=True)
        if ok:
            uid = verify_password(pw)
            if uid:
                st.session_state["_auth_ok"] = True
                st.session_state["_auth_user"] = uid
                st.rerun()
            else:
                st.error("密码错误。")
    st.stop()


def _init_state() -> None:
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []  # list[dict]
    if "last_hits" not in st.session_state:
        st.session_state.last_hits = []
    if "query_log" not in st.session_state:
        st.session_state.query_log = []
    if "history_snapshots" not in st.session_state:
        st.session_state.history_snapshots = []
    if "watch_snapshots" not in st.session_state:
        st.session_state.watch_snapshots = {}  # code -> snapshot dict
    if "auto_refresh_enabled" not in st.session_state:
        st.session_state.auto_refresh_enabled = False
    if "auto_refresh_minutes" not in st.session_state:
        st.session_state.auto_refresh_minutes = 5
    if "push_webhook_on_refresh" not in st.session_state:
        st.session_state.push_webhook_on_refresh = False
    if "push_email_on_refresh" not in st.session_state:
        st.session_state.push_email_on_refresh = False
    if "push_webhook_on_alerts" not in st.session_state:
        st.session_state.push_webhook_on_alerts = False
    if "alert_pct_up" not in st.session_state:
        st.session_state.alert_pct_up = 5.0
    if "alert_pct_down" not in st.session_state:
        st.session_state.alert_pct_down = -5.0
    if "alert_score_low" not in st.session_state:
        st.session_state.alert_score_low = 40.0
    if "alert_score_high" not in st.session_state:
        st.session_state.alert_score_high = 65.0
    if "watch_groups" not in st.session_state:
        st.session_state.watch_groups = {}
    if "watch_notes" not in st.session_state:
        st.session_state.watch_notes = {}
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "recent_viewed" not in st.session_state:
        st.session_state.recent_viewed = []
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True
    if "locale" not in st.session_state:
        st.session_state.locale = "zh"
    if "pick_log" not in st.session_state:
        st.session_state.pick_log = []
    if "today_picks" not in st.session_state:
        st.session_state.today_picks = []
    if "global_picks" not in st.session_state:
        st.session_state.global_picks = []
    if "market_outlook" not in st.session_state:
        st.session_state.market_outlook = None
    if "ui_mode" not in st.session_state:
        st.session_state.ui_mode = "garden"


def _save_history(
    *,
    log_kind: str | None = None,
    log_label: str = "",
    market: str = "",
    board: str = "",
    count: int = 0,
    conclusions_summary: str = "",
) -> None:
    persist_session(
        log_kind=log_kind,
        log_label=log_label,
        market=market,
        board=board,
        count=count,
        conclusions_summary=conclusions_summary,
    )


def _stamp_query(scope: str) -> str:
    """记录各模块查询时间并返回展示文案。"""
    ts = datetime.now()
    st.session_state[f"query_at_{scope}"] = ts
    st.session_state["query_at_latest"] = ts
    label = format_query_datetime(ts)
    st.session_state[f"query_label_{scope}"] = label
    return label


def _query_label(scope: str) -> str:
    return str(st.session_state.get(f"query_label_{scope}") or "")


def _show_query_banner(scope: str | None = None, *, extra: str = "") -> None:
    key = f"query_label_{scope}" if scope else None
    label = _query_label(scope) if key and st.session_state.get(f"query_at_{scope}") else ""
    if not label and st.session_state.get("query_at_latest"):
        label = format_query_datetime(st.session_state["query_at_latest"])
    if label:
        suffix = f"　{extra}" if extra else ""
        st.caption(f"📅 本次查询时间：{label}{suffix}")


def _pick_kind(pick: dict) -> str:
    k = str(pick.get("类型") or "").strip().upper()
    if k in ("A", "HK", "US"):
        return k
    m = str(pick.get("市场") or "")
    if "港" in m:
        return "HK"
    if "美" in m:
        return "US"
    return "A"


def _hit_label(h: eastmoney.SearchHit) -> str:
    code = h.code
    if h.kind in ("US", "HK") and h.yahoo:
        code = h.yahoo
    return f"{h.name}  ({code})  [{h.market}]"


def _add_to_watchlist(h: eastmoney.SearchHit) -> bool:
    new_wl, added = add_hit_to_watchlist(st.session_state.watchlist, h)
    if added:
        st.session_state.watchlist = new_wl
        mark_dirty()
        _save_history(log_kind="watchlist", log_label=f"加入自选股 {h.name}")
    return added


def _add_a_watchlist_by_code(code: str, name: str) -> None:
    c = str(code).strip().zfill(6)
    _add_to_watchlist(
        eastmoney.SearchHit(
            code=c,
            name=str(name or c),
            market=a_market_label(c),
            kind="A",
            yahoo=yahoo_ticker_a(c),
        )
    )


def _is_a_share_code6(code: str) -> bool:
    c = str(code or "").strip().split(".")[0]
    return c.isdigit() and len(c) <= 6


def _capital_mix_for_chart(cap: CapitalMix | dict[str, Any] | Any) -> tuple[dict[str, float], list[str]]:
    """Accept CapitalMix or persisted dict; return pie data and notes."""
    mix = capital_mix_from_dict(cap)
    return mix.as_dict(), list(mix.notes)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_kline(kind: str, code: str, kline: str, start_iso: str, end_iso: str) -> tuple[pd.DataFrame, str]:
    return market_data.fetch_kline_multi(
        kind=kind,
        code=code,
        kline=kline,
        start=date.fromisoformat(start_iso),
        end=date.fromisoformat(end_iso),
    )


@st.cache_data(ttl=300, show_spinner=False)
def _cached_panorama_batch(
    movers_csv: str,
    market: str,
    limit: int,
    query_label: str,
) -> tuple[list[dict], list[dict]]:
    """快速批量分析（无网络），结果可缓存 5 分钟。"""
    movers = pd.read_csv(io.StringIO(movers_csv))
    analyses = analyze_movers_batch(
        movers,
        market=market,
        limit=int(limit),
        query_label=query_label,
        mode="fast",
    )
    summaries = [a.to_summary_dict() for a in analyses]
    details = [
        {
            "code": a.code,
            "name": a.name,
            "market": a.market,
            "kind": a.kind,
            "anomaly_score": a.anomaly_score,
            "capital": capital_mix_to_dict(a.capital),
            "timeframes": a.timeframes,
            "context": a.context,
            "news": a.news,
            "snapshot": a.snapshot,
            "mode": a.mode,
        }
        for a in analyses
    ]
    return summaries, details


def _movers_csv_fingerprint(df: pd.DataFrame) -> str:
    return hashlib.md5(df.to_csv(index=False).encode("utf-8")).hexdigest()


def _fetch_one(item: dict, *, start: date, end: date, kline: str) -> tuple[pd.DataFrame, str]:
    kind = str(item.get("类型") or "")
    code = str(item.get("代码") or "").strip()
    return _cached_kline(kind, code, kline, start.isoformat(), end.isoformat())


def _run_insight_report(*, name: str, code: str, days: int, pick: dict) -> None:
    q_label = _stamp_query("insight")
    end = date.today()
    start = end - timedelta(days=int(days) + 10)
    kind = _pick_kind(pick)
    yahoo_code = str(pick.get("Yahoo代码") or code).strip()
    fetch_code = yahoo_code if kind in ("HK", "US") else code
    market = str(st.session_state.get("movers_market") or "")
    board = str(st.session_state.get("insight_board") or "")
    board_hint = f"{market} · {board}".strip(" · ") if market or board else board
    try:
        with st.spinner("① 拉取行情（多源，约 5–20 秒）…"):
            df, ksrc = _cached_kline(kind, fetch_code, "日线", start.isoformat(), end.isoformat())
        with st.spinner("② 聚合新闻并生成行动路线…"):
            rep = build_action_route_report(
                name=name,
                code=code,
                kind=kind,
                df=df,
                kline_src=ksrc,
                board_hint=board_hint,
                query_label=q_label,
            )
        st.session_state["route_report"] = rep
        st.session_state["insight_range"] = format_data_range(start, end)
        mark_dirty()
        _save_history(
            log_kind="insight",
            log_label=f"异动溯源 {name}（{code}）",
            conclusions_summary=f"溯源:{rep.result[:120]}",
        )
        st.success(f"报告已生成。（查询日 {format_query_date(end)}）")
    except Exception as e:
        snap_price = pick.get("最新价")
        if snap_price is not None or pick.get("涨跌幅%") is not None:
            with st.spinner("K 线不可用，正在用榜单快照生成简版报告…"):
                rep = build_action_route_report_from_snapshot(
                    name=name,
                    code=code,
                    snapshot=pick,
                    board_hint=board_hint,
                    query_label=q_label,
                )
            st.session_state["route_report"] = rep
            mark_dirty()
            _save_history(log_kind="insight", log_label=f"异动溯源简版 {name}（{code}）")
            st.warning(f"完整 K 线未拉到（{e}），已生成简版报告。")
        else:
            hint = "北交所（92 开头）可稍后重试，或先在「全球股市」刷新榜单再生成。" if is_bj_code(code) else ""
            st.error(str(e))
            if hint:
                st.caption(hint)


def _apply_pending_session_keys() -> None:
    pending = st.session_state.pop("_pending_movers_pick_code", None)
    if pending is not None:
        st.session_state["movers_pick_code"] = pending


def _render_route_report_block(rep: ActionRouteReport) -> None:
    st.markdown(f"### {rep.title}")
    st.markdown(f"**一、结果**　{rep.result}")
    st.markdown(f"**二、过程**　{rep.process}")
    st.markdown("**三、可能原因**")
    for c in rep.causes:
        st.markdown(f"- {c}")
    st.markdown("**四、参与者**")
    for p in rep.participants:
        st.markdown(f"- {p}")
    st.markdown("**五、行动路线**")
    for b in rep.playbooks:
        st.markdown(f"- {b}")
    st.markdown("**六、相关新闻**")
    if not rep.news:
        st.write("暂无聚合新闻。")
    else:
        for n in rep.news:
            t = n.get("标题") or ""
            link = n.get("链接") or ""
            src = n.get("来源") or ""
            if link:
                st.markdown(f"- [{t}]({link})（{src}）")
            else:
                st.write(f"- {t}（{src}）")
    st.caption(f"数据交叉：{'；'.join(rep.data_sources)}。{rep.disclaimer}")

