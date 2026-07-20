"""i18n lite（P40）：zh/en 切换，覆盖 Tab 名与工作台指标。"""

from __future__ import annotations

import streamlit as st

LOCALE_KEY = "locale"
DEFAULT_LOCALE = "zh"
SUPPORTED_LOCALES = frozenset({"zh", "en"})

TAB_IDS: list[str] = [
    "watch",
    "search",
    "markets",
    "history",
]

_STRINGS: dict[str, dict[str, str]] = {
    "tab_watch": {"zh": "① 自选分析", "en": "① Watchlist"},
    "tab_search": {"zh": "② 发现标的", "en": "② Discover"},
    "tab_markets": {"zh": "③ 市场一览", "en": "③ Markets"},
    "tab_history": {"zh": "④ 历史记录", "en": "④ History"},
    "dash_title": {"zh": "📊 工作台概览", "en": "📊 Watchlist Overview"},
    "dash_watch": {"zh": "自选", "en": "Watchlist"},
    "dash_avg_score": {"zh": "均分", "en": "Avg Score"},
    "dash_up": {"zh": "上涨", "en": "Up"},
    "dash_down": {"zh": "下跌", "en": "Down"},
    "dash_alerts": {"zh": "今日提醒", "en": "Alerts Today"},
    "dash_health": {"zh": "健康分", "en": "Health"},
    "dash_help_health": {
        "zh": "均分+提醒+新鲜度+板块分散加权 0–100",
        "en": "Weighted 0–100: score, alerts, freshness, sectors",
    },
    "dash_help_watch": {"zh": "当前自选股数量", "en": "Number of watchlist items"},
    "dash_help_avg": {"zh": "有评分 {n} 只", "en": "{n} scored"},
    "dash_help_up": {"zh": "涨跌幅 > 0", "en": "Change > 0"},
    "dash_help_down": {"zh": "涨跌幅 < 0", "en": "Change < 0"},
    "dash_help_alerts": {"zh": "按当前阈值计算的触发项", "en": "Triggers at current thresholds"},
    "dash_missing_snap": {
        "zh": "摘要覆盖 {have}/{total} 只；{missing} 只尚无快照。",
        "en": "Snapshots {have}/{total}; {missing} without snapshot.",
    },
    "dash_flat": {"zh": "平盘/无涨跌 {n} 只。", "en": "Flat / no change: {n}."},
    "locale_label": {"zh": "界面语言", "en": "Language"},
    "locale_zh": {"zh": "中文", "en": "中文"},
    "locale_en": {"zh": "English", "en": "English"},
}

_TAB_KEY_BY_ID = {
    "watch": "tab_watch",
    "search": "tab_search",
    "markets": "tab_markets",
    "history": "tab_history",
}


def normalize_locale(raw: str | None) -> str:
    loc = (raw or DEFAULT_LOCALE).strip().lower()
    return loc if loc in SUPPORTED_LOCALES else DEFAULT_LOCALE


def get_locale(session_state: dict | None = None) -> str:
    state = session_state if session_state is not None else st.session_state
    return normalize_locale(state.get(LOCALE_KEY, DEFAULT_LOCALE))


def t(key: str, *, locale: str | None = None, **fmt: object) -> str:
    loc = normalize_locale(locale or get_locale())
    text = _STRINGS.get(key, {}).get(loc) or _STRINGS.get(key, {}).get(DEFAULT_LOCALE) or key
    if fmt:
        return text.format(**fmt)
    return text


def tab_label(tab_id: str, *, locale: str | None = None) -> str:
    key = _TAB_KEY_BY_ID.get(tab_id, tab_id)
    return t(key, locale=locale)


def tab_order(*, locale: str | None = None) -> list[tuple[str, str]]:
    loc = normalize_locale(locale or get_locale())
    return [(tid, tab_label(tid, locale=loc)) for tid in TAB_IDS]


def render_locale_toggle() -> None:
    """侧边栏语言切换（偏好写入 user_prefs）。"""
    from src.storage.history_store import mark_dirty

    loc = get_locale()
    options = ["zh", "en"]
    labels = [t("locale_zh", locale=loc), t("locale_en", locale=loc)]
    idx = options.index(loc) if loc in options else 0
    choice = st.selectbox(
        t("locale_label", locale=loc),
        options=options,
        format_func=lambda x: labels[options.index(x)],
        index=idx,
        help="Tab names & dashboard metrics (P40 i18n lite)",
    )
    if choice != loc:
        st.session_state[LOCALE_KEY] = choice
        mark_dirty()
