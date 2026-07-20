"""表格涨跌配色（A股习惯：红涨绿跌）。全站 st.dataframe 统一入口。"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
import streamlit as st

# A股：涨红跌绿
_UP = "color: #e74c3c; font-weight: 600;"
_DOWN = "color: #27ae60; font-weight: 600;"
_FLAT = "color: #888888;"


def _to_float(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace("＋", "+").replace(",", "")
    if not s or s in ("—", "-", "nan", "None", "null"):
        return None
    # 去掉前导+
    try:
        return float(s)
    except ValueError:
        m = re.search(r"([+-]?\d+(?:\.\d+)?)", s)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None
    return None


def is_pct_column(name: str) -> bool:
    n = str(name or "")
    if not n:
        return False
    # 排除非涨跌类百分比
    skip = ("命中", "概率", "换手", "占比", "权重", "仓位", "评分", "家数", "样本")
    if any(s in n for s in skip) and not any(k in n for k in ("涨跌", "涨幅", "跌幅")):
        return False
    keys = (
        "涨跌",
        "涨幅",
        "跌幅",
        "振幅",
        "回报",
        "收益",
        "delta",
        "pct",
        "最高%",
        "变化",
        "D+1",
        "D+2",
        "D+3",
        "5日%",
        "20日%",
    )
    return any(k.lower() in n.lower() if k.isascii() else k in n for k in keys)


def pct_columns(df: pd.DataFrame) -> list[str]:
    if df is None or df.empty:
        return []
    return [c for c in df.columns if is_pct_column(str(c))]


def _style_series(series: pd.Series) -> list[str]:
    out: list[str] = []
    for v in series:
        x = _to_float(v)
        if x is None:
            out.append("")
        elif x > 0:
            out.append(_UP)
        elif x < 0:
            out.append(_DOWN)
        else:
            out.append(_FLAT)
    return out


def style_pct_dataframe(
    df: pd.DataFrame,
    *,
    columns: list[str] | None = None,
) -> Any:
    """返回带涨跌色的 Styler，或原 DataFrame。"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    cols = columns if columns is not None else pct_columns(df)
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return df
    try:
        sty = df.style
        for c in cols:
            sty = sty.apply(lambda _s, col=c: _style_series(df[col]), subset=[c])
        return sty
    except Exception:
        return df


def show_df(
    data: Any,
    *,
    use_container_width: bool = True,
    hide_index: bool = True,
    pct_cols: list[str] | None = None,
    **kwargs: Any,
) -> None:
    """全站表格入口：自动给涨跌相关列上色。"""
    if data is None:
        return
    if isinstance(data, pd.DataFrame):
        styled = style_pct_dataframe(data, columns=pct_cols)
        st.dataframe(styled, use_container_width=use_container_width, hide_index=hide_index, **kwargs)
        return
    # 已是 Styler 或其他
    st.dataframe(data, use_container_width=use_container_width, hide_index=hide_index, **kwargs)


def html_pct_color(v: Any) -> str:
    """HTML 内联样式颜色值（用于 movers 自定义表）。"""
    x = _to_float(v)
    if x is None:
        return "#fafafa"
    if x > 0:
        return "#e74c3c"
    if x < 0:
        return "#27ae60"
    return "#888888"
