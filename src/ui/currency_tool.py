"""自选股页 · 货币换算。"""

from __future__ import annotations

import streamlit as st

from src.util.currency import (
    CURRENCY_META,
    convert_amount,
    currency_display,
    fetch_fx_rates,
)

CCY_OPTIONS = ["CNY", "HKD", "USD", "JPY", "EUR"]
_FX_LAST_WATCH = "fx_last_watch_code"


def render_floating_currency_tool(
    *, default_from: str = "CNY", watch_code: str = ""
) -> None:
    """货币换算（expander）；默认「从」货币仅在切换标的时更新。"""
    if "fx_rates_usd" not in st.session_state:
        rates, ts, live = fetch_fx_rates()
        st.session_state.fx_rates_usd = rates
        st.session_state.fx_rates_ts = ts
        st.session_state.fx_rates_live = live

    with st.expander("💱 货币计算", expanded=False):
        rates = st.session_state.fx_rates_usd
        ts = st.session_state.get("fx_rates_ts", "")
        live = st.session_state.get("fx_rates_live", False)
        if st.button("刷新汇率", key="fx_refresh", use_container_width=True):
            r2, t2, l2 = fetch_fx_rates()
            st.session_state.fx_rates_usd = r2
            st.session_state.fx_rates_ts = t2
            st.session_state.fx_rates_live = l2
            rates = r2
            ts = t2
            live = l2
        st.caption(f"汇率更新：{ts}" + (" · 实时" if live else " · 参考"))

        df = str(default_from or "CNY").upper()
        if df not in CCY_OPTIONS:
            df = "CNY"
        wk = str(watch_code or "")
        if st.session_state.get(_FX_LAST_WATCH) != wk:
            st.session_state.fx_from = df
            st.session_state.fx_to = "CNY" if df != "CNY" else "USD"
            st.session_state[_FX_LAST_WATCH] = wk
        if "fx_from" not in st.session_state:
            st.session_state.fx_from = df
        if "fx_to" not in st.session_state:
            f0 = st.session_state.fx_from
            st.session_state.fx_to = "CNY" if f0 != "CNY" else "USD"
        if "fx_amount" not in st.session_state:
            st.session_state.fx_amount = 10000.0

        c1, c2, c3 = st.columns([1, 0.35, 1])
        with c1:
            from_ccy = st.selectbox(
                "从",
                CCY_OPTIONS,
                format_func=lambda x: currency_display(x),
                key="fx_from",
            )
        with c2:
            st.markdown(
                "<div style='text-align:center;padding-top:1.6rem'>→</div>",
                unsafe_allow_html=True,
            )
        with c3:
            to_ccy = st.selectbox(
                "到",
                CCY_OPTIONS,
                format_func=lambda x: currency_display(x),
                key="fx_to",
            )
        amount = st.number_input(
            "金额",
            min_value=0.0,
            step=100.0,
            key="fx_amount",
        )

        out = convert_amount(float(amount), str(from_ccy), str(to_ccy), rates)
        if out is None:
            st.warning("暂无法换算该货币对。")
        else:
            _, sym_t = CURRENCY_META.get(str(to_ccy), ("", to_ccy))
            st.metric("换算结果", f"{sym_t}{out:,.2f}")
            st.caption(f"{float(amount):,.2f} {from_ccy} = {out:,.2f} {to_ccy}")
            if from_ccy != "USD" and to_ccy != "USD":
                mid = convert_amount(1.0, str(from_ccy), str(to_ccy), rates)
                if mid is not None:
                    st.caption(f"参考：1 {from_ccy} ≈ {mid:.4f} {to_ccy}")
