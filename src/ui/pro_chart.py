"""专业风格 K 线图（蜡烛图 + 均线 + 成交量 + 副图指标，接近常见看盘软件）。"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.signals import add_indicators

CHART_INDICATORS = (
    "RSI",
    "KDJ",
    "MACD",
    "W%R",
    "DMI",
    "BIAS",
    "OBV",
    "CCI",
    "ROC",
)

DEFAULT_VISIBLE_BARS = 120
MIN_VISIBLE_BARS = 30
MAX_VISIBLE_BARS = 500


def _prep_df(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values("日期").copy()
    d["日期"] = pd.to_datetime(d["日期"])
    for c in ("开盘", "最高", "最低", "收盘", "成交量"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["开盘", "最高", "最低", "收盘"])
    if d.empty:
        return d
    return add_indicators(d)


def _ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def add_chart_indicators(d: pd.DataFrame) -> pd.DataFrame:
    """副图指标（RSI/KDJ/MACD 等），供 multipane 使用。"""
    out = d.copy()
    close = out["收盘"]
    high = out["最高"]
    low = out["最低"]
    vol = out["成交量"].fillna(0) if "成交量" in out.columns else pd.Series(0.0, index=out.index)

    for p in (5, 10, 20, 60):
        out[f"MA{p}"] = close.rolling(p).mean()
    out["VOL_MA5"] = vol.rolling(5).mean()
    out["VOL_MA10"] = vol.rolling(10).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))

    low9 = low.rolling(9).min()
    high9 = high.rolling(9).max()
    rsv = (close - low9) / (high9 - low9).replace(0, np.nan) * 100
    out["KDJ_K"] = rsv.ewm(com=2, adjust=False).mean()
    out["KDJ_D"] = out["KDJ_K"].ewm(com=2, adjust=False).mean()
    out["KDJ_J"] = 3 * out["KDJ_K"] - 2 * out["KDJ_D"]

    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    out["MACD_DIF"] = ema12 - ema26
    out["MACD_DEA"] = _ema(out["MACD_DIF"], 9)
    out["MACD_HIST"] = (out["MACD_DIF"] - out["MACD_DEA"]) * 2

    hh14 = high.rolling(14).max()
    ll14 = low.rolling(14).min()
    out["W%R"] = (hh14 - close) / (hh14 - ll14).replace(0, np.nan) * -100

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr14 = tr.rolling(14).sum()
    plus_di = 100 * pd.Series(plus_dm, index=out.index).rolling(14).sum() / tr14.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=out.index).rolling(14).sum() / tr14.replace(0, np.nan)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    out["DMI_PDI"] = plus_di
    out["DMI_MDI"] = minus_di
    out["DMI_ADX"] = dx.rolling(14).mean()

    for n, col in ((6, "BIAS6"), (12, "BIAS12"), (24, "BIAS24")):
        ma = close.rolling(n).mean()
        out[col] = (close - ma) / ma.replace(0, np.nan) * 100

    direction = np.sign(close.diff()).fillna(0)
    out["OBV"] = (direction * vol).cumsum()

    tp = (high + low + close) / 3
    ma_tp = tp.rolling(14).mean()
    md = (tp - ma_tp).abs().rolling(14).mean()
    out["CCI"] = (tp - ma_tp) / (0.015 * md.replace(0, np.nan))

    out["ROC"] = close.pct_change(12) * 100
    return out


def _visible_slice(d: pd.DataFrame, visible_bars: int | None) -> tuple[pd.DataFrame, pd.Timestamp | None, pd.Timestamp | None]:
    if not visible_bars or visible_bars <= 0 or len(d) <= visible_bars:
        return d, None, None
    view = d.iloc[-visible_bars:]
    return view, view["日期"].iloc[0], view["日期"].iloc[-1]


def _fmt_val(v: float | None, *, digits: int = 2) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{float(v):.{digits}f}"


def _legend_annotations(
    fig: go.Figure,
    *,
    row: int,
    items: list[tuple[str, str, str]],
    y: float = 0.96,
) -> None:
    xref = "x domain" if row == 1 else f"x{row} domain"
    yref = "y domain" if row == 1 else f"y{row} domain"
    x = 0.01
    for label, val, color in items:
        fig.add_annotation(
            text=f"<span style='color:{color}'>{label}</span> {val}",
            xref=xref,
            yref=yref,
            x=x,
            y=y,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            font=dict(size=11, color="#e0e0e0"),
            bgcolor="rgba(14,17,23,0.55)",
            borderpad=2,
        )
        x += min(0.14, 0.85 / max(len(items), 1))


def last_bar_stats(d: pd.DataFrame) -> dict[str, float | str | None]:
    if d.empty:
        return {}
    last = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else last
    close = float(last["收盘"])
    prev_c = float(prev["收盘"])
    chg = close - prev_c
    chg_pct = (chg / prev_c * 100) if prev_c else 0.0
    return {
        "收盘": close,
        "涨跌额": chg,
        "涨跌幅%": chg_pct,
        "开盘": float(last["开盘"]),
        "最高": float(last["最高"]),
        "最低": float(last["最低"]),
        "成交量": float(last["成交量"]) if "成交量" in last and pd.notna(last["成交量"]) else None,
        "日期": str(last["日期"].date()) if hasattr(last["日期"], "date") else str(last["日期"]),
    }


def build_pro_chart(
    df: pd.DataFrame,
    title: str,
    *,
    show_ma: Sequence[int] = (5, 10, 20),
    show_volume: bool = True,
    show_rangeslider: bool = True,
    height: int = 720,
) -> go.Figure:
    d = _prep_df(df)
    if d.empty:
        fig = go.Figure()
        fig.update_layout(title=title, template="plotly_dark", height=400)
        fig.add_annotation(text="暂无有效 K 线数据", showarrow=False, font=dict(size=16))
        return fig

    rows = 2 if show_volume else 1
    row_heights = [0.72, 0.28] if show_volume else [1.0]
    subplot_titles = (title, "成交量") if show_volume else (title,)

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    inc = "#ef5350"
    dec = "#26a69a"

    fig.add_trace(
        go.Candlestick(
            x=d["日期"],
            open=d["开盘"],
            high=d["最高"],
            low=d["最低"],
            close=d["收盘"],
            name="K线",
            increasing_line_color=inc,
            increasing_fillcolor=inc,
            decreasing_line_color=dec,
            decreasing_fillcolor=dec,
        ),
        row=1,
        col=1,
    )

    ma_styles = {
        5: ("#ffca28", "MA5"),
        10: ("#42a5f5", "MA10"),
        20: ("#ab47bc", "MA20"),
        60: ("#78909c", "MA60"),
    }
    close = d["收盘"]
    for period in show_ma:
        if period <= 0:
            continue
        col = f"MA{period}"
        if col not in d.columns:
            d[col] = close.rolling(period).mean()
        color, label = ma_styles.get(period, ("#b0bec5", f"MA{period}"))
        fig.add_trace(
            go.Scatter(
                x=d["日期"],
                y=d[col],
                mode="lines",
                name=label,
                line=dict(width=1.2, color=color),
                opacity=0.9,
            ),
            row=1,
            col=1,
        )

    if show_volume and "成交量" in d.columns:
        vol = d["成交量"].fillna(0)
        vol_colors = [
            inc if float(c) >= float(o) else dec
            for c, o in zip(d["收盘"], d["开盘"])
        ]
        fig.add_trace(
            go.Bar(
                x=d["日期"],
                y=vol,
                name="成交量",
                marker_color=vol_colors,
                opacity=0.85,
            ),
            row=2,
            col=1,
        )

    y_min = float(d["最低"].min())
    y_max = float(d["最高"].max())
    pad = max((y_max - y_min) * 0.06, y_max * 0.01, 0.5)
    fig.update_yaxes(
        title_text="价格",
        range=[y_min - pad, y_max + pad],
        fixedrange=False,
        row=1,
        col=1,
    )
    if show_volume:
        fig.update_yaxes(title_text="成交量", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=48, r=24, t=48, b=36),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161a22",
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        font=dict(color="#e0e0e0", size=12),
    )

    fig.update_xaxes(
        rangeslider_visible=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="dot",
        spikecolor="#888",
        row=1,
        col=1,
    )
    bottom_row = 2 if show_volume else 1
    fig.update_xaxes(
        title_text="日期",
        rangeslider_visible=show_rangeslider,
        rangeslider_thickness=0.08,
        type="date",
        tickformat="%Y-%m-%d",
        showspikes=True,
        row=bottom_row,
        col=1,
    )

    # 快捷缩放（Plotly rangeselector）
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                filter(
                    None,
                    [
                        dict(count=1, label="1月", step="month", stepmode="backward"),
                        dict(count=3, label="3月", step="month", stepmode="backward"),
                        dict(count=6, label="6月", step="month", stepmode="backward"),
                        dict(count=1, label="1年", step="year", stepmode="backward"),
                        dict(step="all", label="全部"),
                    ],
                )
            ),
            bgcolor="#1e222d",
            activecolor="#3949ab",
        ),
        row=1,
        col=1,
    )

    return fig


def _add_indicator_traces(fig: go.Figure, d: pd.DataFrame, indicator: str, row: int) -> None:
    x = d["日期"]
    ind = indicator.strip().upper()

    if ind == "RSI":
        fig.add_trace(
            go.Scatter(x=x, y=d["RSI"], name="RSI", line=dict(color="#ffca28", width=1.2)),
            row=row,
            col=1,
        )
        fig.add_hline(y=70, line_dash="dot", line_color="#666", row=row, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#666", row=row, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=row, col=1)
        last = d["RSI"].iloc[-1]
        _legend_annotations(fig, row=row, items=[("RSI", _fmt_val(last), "#ffca28")])
        return

    if ind == "KDJ":
        for col, name, color in (
            ("KDJ_K", "K", "#ffca28"),
            ("KDJ_D", "D", "#42a5f5"),
            ("KDJ_J", "J", "#ab47bc"),
        ):
            fig.add_trace(
                go.Scatter(x=x, y=d[col], name=name, line=dict(color=color, width=1.1)),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="KDJ", row=row, col=1)
        _legend_annotations(
            fig,
            row=row,
            items=[
                ("K", _fmt_val(d["KDJ_K"].iloc[-1]), "#ffca28"),
                ("D", _fmt_val(d["KDJ_D"].iloc[-1]), "#42a5f5"),
                ("J", _fmt_val(d["KDJ_J"].iloc[-1]), "#ab47bc"),
            ],
        )
        return

    if ind == "MACD":
        colors = ["#ef5350" if v >= 0 else "#26a69a" for v in d["MACD_HIST"].fillna(0)]
        fig.add_trace(
            go.Bar(x=x, y=d["MACD_HIST"], name="MACD", marker_color=colors, opacity=0.75),
            row=row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=x, y=d["MACD_DIF"], name="DIF", line=dict(color="#ffca28", width=1.1)),
            row=row,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=x, y=d["MACD_DEA"], name="DEA", line=dict(color="#42a5f5", width=1.1)),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="MACD", row=row, col=1)
        _legend_annotations(
            fig,
            row=row,
            items=[
                ("DIF", _fmt_val(d["MACD_DIF"].iloc[-1]), "#ffca28"),
                ("DEA", _fmt_val(d["MACD_DEA"].iloc[-1]), "#42a5f5"),
                ("MACD", _fmt_val(d["MACD_HIST"].iloc[-1]), "#e0e0e0"),
            ],
        )
        return

    if ind == "W%R":
        fig.add_trace(
            go.Scatter(x=x, y=d["W%R"], name="W%R", line=dict(color="#ffca28", width=1.2)),
            row=row,
            col=1,
        )
        fig.add_hline(y=-20, line_dash="dot", line_color="#666", row=row, col=1)
        fig.add_hline(y=-80, line_dash="dot", line_color="#666", row=row, col=1)
        fig.update_yaxes(title_text="W%R", range=[-100, 0], row=row, col=1)
        _legend_annotations(fig, row=row, items=[("W%R", _fmt_val(d["W%R"].iloc[-1]), "#ffca28")])
        return

    if ind == "DMI":
        for col, name, color in (
            ("DMI_PDI", "+DI", "#ef5350"),
            ("DMI_MDI", "-DI", "#26a69a"),
            ("DMI_ADX", "ADX", "#ffca28"),
        ):
            fig.add_trace(
                go.Scatter(x=x, y=d[col], name=name, line=dict(color=color, width=1.1)),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="DMI", row=row, col=1)
        _legend_annotations(
            fig,
            row=row,
            items=[
                ("+DI", _fmt_val(d["DMI_PDI"].iloc[-1]), "#ef5350"),
                ("-DI", _fmt_val(d["DMI_MDI"].iloc[-1]), "#26a69a"),
                ("ADX", _fmt_val(d["DMI_ADX"].iloc[-1]), "#ffca28"),
            ],
        )
        return

    if ind == "BIAS":
        for col, name, color in (
            ("BIAS6", "BIAS6", "#ffca28"),
            ("BIAS12", "BIAS12", "#42a5f5"),
            ("BIAS24", "BIAS24", "#ab47bc"),
        ):
            fig.add_trace(
                go.Scatter(x=x, y=d[col], name=name, line=dict(color=color, width=1.1)),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="BIAS", row=row, col=1)
        _legend_annotations(
            fig,
            row=row,
            items=[
                ("BIAS6", _fmt_val(d["BIAS6"].iloc[-1]) + "%", "#ffca28"),
                ("BIAS12", _fmt_val(d["BIAS12"].iloc[-1]) + "%", "#42a5f5"),
                ("BIAS24", _fmt_val(d["BIAS24"].iloc[-1]) + "%", "#ab47bc"),
            ],
        )
        return

    if ind == "OBV":
        fig.add_trace(
            go.Scatter(x=x, y=d["OBV"], name="OBV", line=dict(color="#42a5f5", width=1.2)),
            row=row,
            col=1,
        )
        fig.update_yaxes(title_text="OBV", row=row, col=1)
        _legend_annotations(fig, row=row, items=[("OBV", _fmt_val(d["OBV"].iloc[-1], digits=0), "#42a5f5")])
        return

    if ind == "CCI":
        fig.add_trace(
            go.Scatter(x=x, y=d["CCI"], name="CCI", line=dict(color="#ffca28", width=1.2)),
            row=row,
            col=1,
        )
        fig.add_hline(y=100, line_dash="dot", line_color="#666", row=row, col=1)
        fig.add_hline(y=-100, line_dash="dot", line_color="#666", row=row, col=1)
        fig.update_yaxes(title_text="CCI", row=row, col=1)
        _legend_annotations(fig, row=row, items=[("CCI", _fmt_val(d["CCI"].iloc[-1]), "#ffca28")])
        return

    if ind == "ROC":
        fig.add_trace(
            go.Scatter(x=x, y=d["ROC"], name="ROC", line=dict(color="#ab47bc", width=1.2)),
            row=row,
            col=1,
        )
        fig.add_hline(y=0, line_dash="dot", line_color="#666", row=row, col=1)
        fig.update_yaxes(title_text="ROC", row=row, col=1)
        _legend_annotations(fig, row=row, items=[("ROC", _fmt_val(d["ROC"].iloc[-1]) + "%", "#ab47bc")])
        return

    fig.add_trace(
        go.Scatter(x=x, y=d["RSI"], name="RSI", line=dict(color="#ffca28", width=1.2)),
        row=row,
        col=1,
    )
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=row, col=1)


def build_pro_chart_multipane(
    df: pd.DataFrame,
    title: str,
    *,
    indicator: str = "RSI",
    show_ma: Sequence[int] = (5, 10, 20, 60),
    visible_bars: int | None = DEFAULT_VISIBLE_BARS,
    height: int = 900,
) -> go.Figure:
    """三栏专业图：K线+均线 / 成交量 / 副图指标。"""
    d = _prep_df(df)
    if d.empty:
        fig = go.Figure()
        fig.update_layout(title=title, template="plotly_dark", height=400)
        fig.add_annotation(text="暂无有效 K 线数据", showarrow=False, font=dict(size=16))
        return fig

    d = add_chart_indicators(d)
    view, x0, x1 = _visible_slice(d, visible_bars)

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.52, 0.22, 0.26],
        subplot_titles=(title, "成交量", indicator),
    )

    inc = "#ef5350"
    dec = "#26a69a"

    fig.add_trace(
        go.Candlestick(
            x=view["日期"],
            open=view["开盘"],
            high=view["最高"],
            low=view["最低"],
            close=view["收盘"],
            name="K线",
            increasing_line_color=inc,
            increasing_fillcolor=inc,
            decreasing_line_color=dec,
            decreasing_fillcolor=dec,
        ),
        row=1,
        col=1,
    )

    ma_styles = {
        5: ("#ffca28", "MA5"),
        10: ("#42a5f5", "MA10"),
        20: ("#ab47bc", "MA20"),
        60: ("#78909c", "MA60"),
    }
    ma_ann: list[tuple[str, str, str]] = []
    for period in show_ma:
        col = f"MA{period}"
        if col not in view.columns:
            continue
        color, label = ma_styles.get(period, ("#b0bec5", f"MA{period}"))
        fig.add_trace(
            go.Scatter(
                x=view["日期"],
                y=view[col],
                mode="lines",
                name=label,
                line=dict(width=1.2, color=color),
                opacity=0.9,
            ),
            row=1,
            col=1,
        )
        ma_ann.append((label, _fmt_val(float(view[col].iloc[-1])), color))

    if ma_ann:
        _legend_annotations(fig, row=1, items=ma_ann, y=0.99)

    if "成交量" in view.columns:
        vol = view["成交量"].fillna(0)
        vol_colors = [
            inc if float(c) >= float(o) else dec for c, o in zip(view["收盘"], view["开盘"])
        ]
        fig.add_trace(
            go.Bar(x=view["日期"], y=vol, name="成交量", marker_color=vol_colors, opacity=0.85),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=view["日期"],
                y=view["VOL_MA5"],
                name="VOL MA5",
                line=dict(color="#ffca28", width=1),
                opacity=0.9,
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=view["日期"],
                y=view["VOL_MA10"],
                name="VOL MA10",
                line=dict(color="#42a5f5", width=1),
                opacity=0.9,
            ),
            row=2,
            col=1,
        )
        _legend_annotations(
            fig,
            row=2,
            items=[
                ("VOL MA5", _fmt_val(float(view["VOL_MA5"].iloc[-1]), digits=0), "#ffca28"),
                ("VOL MA10", _fmt_val(float(view["VOL_MA10"].iloc[-1]), digits=0), "#42a5f5"),
            ],
        )

    _add_indicator_traces(fig, view, indicator, row=3)

    y_min = float(view["最低"].min())
    y_max = float(view["最高"].max())
    pad = max((y_max - y_min) * 0.06, y_max * 0.01, 0.5)
    fig.update_yaxes(title_text="价格", range=[y_min - pad, y_max + pad], fixedrange=False, row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=48, r=24, t=48, b=28),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, font=dict(size=10)),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161a22",
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        font=dict(color="#e0e0e0", size=12),
    )

    for r in (1, 2, 3):
        fig.update_xaxes(
            rangeslider_visible=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikedash="dot",
            spikecolor="#888",
            row=r,
            col=1,
        )

    if x0 is not None and x1 is not None:
        fig.update_xaxes(range=[x0, x1], row=1, col=1)
        fig.update_xaxes(range=[x0, x1], row=2, col=1)
        fig.update_xaxes(range=[x0, x1], row=3, col=1)

    fig.update_xaxes(type="date", tickformat="%m-%d %H:%M", row=3, col=1)
    return fig


PLOTLY_CHART_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "displaylogo": False,
    "responsive": True,
}
