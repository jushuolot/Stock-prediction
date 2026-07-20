"""
多周期价格/量能变化及对股价影响的文字化归纳。

秒级：公开免费源一般不提供全市场逐秒资金流，标记为不可用。
分/时：优先 Yahoo 分钟/小时线（近几日）；日/月/年：日 K 汇总。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from src.providers.ticker_util import yahoo_ticker_a


@dataclass
class TimeframeSlice:
    label: str
    available: bool
    price_chg_pct: float | None
    volume_chg_pct: float | None
    impact: str
    detail: str


def _chg_pct(series: pd.Series) -> float | None:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2:
        return None
    a, b = float(s.iloc[0]), float(s.iloc[-1])
    if not np.isfinite(a) or a == 0:
        return None
    return (b / a - 1) * 100


def _impact_text(pct: float | None, vol_pct: float | None, horizon: str) -> str:
    if pct is None:
        return f"{horizon}：数据不足。"
    direction = "推升股价" if pct > 0.5 else ("压制股价" if pct < -0.5 else "对股价影响中性")
    vol = ""
    if vol_pct is not None:
        if vol_pct > 30:
            vol = "，成交显著放大，资金参与度提高"
        elif vol_pct < -20:
            vol = "，成交萎缩，观望情绪浓"
    return f"{horizon}涨跌约 {pct:.2f}%，{direction}{vol}。"


def _from_daily(df: pd.DataFrame) -> list[TimeframeSlice]:
    d = df.sort_values("日期").copy()
    close = pd.to_numeric(d["收盘"], errors="coerce")
    vol = pd.to_numeric(d.get("成交量", pd.Series([np.nan] * len(d))), errors="coerce")
    out: list[TimeframeSlice] = []

    def slice_n(n: int, label: str) -> None:
        if len(close) < n + 1:
            out.append(TimeframeSlice(label, False, None, None, "数据不足", f"日K不足 {n} 根"))
            return
        pc = _chg_pct(close.tail(n + 1))
        vc = _chg_pct(vol.tail(n + 1))
        out.append(
            TimeframeSlice(label, True, pc, vc, _impact_text(pc, vc, label), f"基于最近 {n} 个交易日收盘")
        )

    slice_n(1, "日")
    slice_n(5, "周(约5日)")
    slice_n(20, "月(约20日)")
    if len(close) >= 250:
        pc = _chg_pct(close.tail(250))
        vc = _chg_pct(vol.tail(250))
        out.append(TimeframeSlice("年(约250日)", True, pc, vc, _impact_text(pc, vc, "年"), "基于约一年日K"))
    else:
        pc = _chg_pct(close)
        out.append(
            TimeframeSlice(
                "年(样本不足)",
                len(close) >= 60,
                pc,
                _chg_pct(vol),
                _impact_text(pc, _chg_pct(vol), "年内样本"),
                f"仅 {len(close)} 根日K，年维度为近似",
            )
        )
    return out


def _from_intraday(ticker: str) -> list[TimeframeSlice]:
    out: list[TimeframeSlice] = []
    out.append(
        TimeframeSlice(
            "秒",
            False,
            None,
            None,
            "公开源不提供全市场逐秒资金拆分",
            "需 Level-2/付费行情；本工具不展示伪秒级数据",
        )
    )
    import yfinance as yf

    for interval, label, period in (("1m", "分(1分钟)", "1d"), ("5m", "分(5分钟)", "5d"), ("1h", "小时", "1mo")):
        try:
            hist = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        except Exception as e:
            out.append(TimeframeSlice(label, False, None, None, "拉取失败", str(e)[:80]))
            continue
        if hist is None or hist.empty:
            out.append(TimeframeSlice(label, False, None, None, "无日内数据", "非交易时段或源站限制"))
            continue
        pc = _chg_pct(hist["Close"])
        vc = _chg_pct(hist["Volume"]) if "Volume" in hist.columns else None
        out.append(
            TimeframeSlice(
                label,
                True,
                pc,
                vc,
                _impact_text(pc, vc, label),
                f"Yahoo {interval} 线，{period} 窗口，{len(hist)} 根",
            )
        )
    return out


def analyze_timeframes(
    *,
    daily_df: pd.DataFrame | None,
    yahoo_ticker: str,
    kind: str = "A",
    code: str = "",
    include_intraday: bool = True,
) -> list[TimeframeSlice]:
    slices: list[TimeframeSlice] = []
    yh = (yahoo_ticker or "").strip()
    if not yh and code.isdigit() and len(code) == 6:
        yh = yahoo_ticker_a(code)
    if not yh:
        yh = code

    if include_intraday and yh:
        try:
            slices.extend(_from_intraday(yh))
        except Exception:
            slices.append(
                TimeframeSlice("分", False, None, None, "日内线不可用", "非交易时段或网络限制")
            )

    if daily_df is not None and not daily_df.empty:
        slices.extend(_from_daily(daily_df))
    elif not slices:
        slices.append(TimeframeSlice("日", False, None, None, "无K线", "请先拉取日K或检查代码"))
    return slices


def snapshot_timeframe_slices(
    pct_change: float | None,
    turnover_pct: float | None,
) -> list[TimeframeSlice]:
    """快速模式：仅用榜单当日字段，不发起行情请求。"""
    pct = float(pct_change) if pct_change is not None else None
    turn = float(turnover_pct) if turnover_pct is not None else None
    return [
        TimeframeSlice(
            "秒",
            False,
            None,
            None,
            "需 Level-2/付费源",
            "快速模式不请求逐秒数据",
        ),
        TimeframeSlice(
            "分/时",
            False,
            None,
            None,
            "快速模式未拉日内线",
            "点「深度分析选中1只」可获取",
        ),
        TimeframeSlice(
            "日(榜单)",
            pct is not None,
            pct,
            None,
            _impact_text(pct, None, "当日(榜单涨跌幅)"),
            "来自榜单快照，非历史 K 线回测",
        ),
        TimeframeSlice(
            "周/月/年",
            False,
            None,
            None,
            "快速模式无历史 K 线",
            "深度分析可计算日/周/月/年维度",
        ),
    ]


def slices_to_rows(slices: list[TimeframeSlice]) -> list[dict[str, Any]]:
    rows = []
    for s in slices:
        rows.append(
            {
                "周期": s.label,
                "可用": "是" if s.available else "否",
                "涨跌%": s.price_chg_pct,
                "量能变化%": s.volume_chg_pct,
                "对股价影响": s.impact,
                "说明": s.detail,
            }
        )
    return rows
