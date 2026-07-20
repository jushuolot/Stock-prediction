from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    trend: float
    momentum: float
    risk: float
    liquidity: float
    notes: list[str]


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        raise ValueError(f"缺少列：{name}")
    return pd.to_numeric(df[name], errors="coerce")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    close = _col(out, "收盘")
    vol = _col(out, "成交量") if "成交量" in out.columns else pd.Series([np.nan] * len(out))

    out["MA20"] = close.rolling(20).mean()
    out["MA60"] = close.rolling(60).mean()
    out["收益率"] = close.pct_change()
    out["波动率20"] = out["收益率"].rolling(20).std() * np.sqrt(252)
    out["动量20"] = close.pct_change(20)
    out["动量60"] = close.pct_change(60)
    out["成交量均值20"] = vol.rolling(20).mean()
    return out


def score_stock(df: pd.DataFrame) -> ScoreBreakdown:
    """
    规则型打分（便于理解、可量化、可复现）。
    仅依赖行情表的中文列：收盘/成交量（可选）。
    """
    dfi = add_indicators(df)
    last = dfi.tail(1).iloc[0]
    notes: list[str] = []

    close = float(last.get("收盘") or 0.0)
    ma20 = float(last.get("MA20") or np.nan)
    ma60 = float(last.get("MA60") or np.nan)
    mom20 = float(last.get("动量20") or np.nan)
    mom60 = float(last.get("动量60") or np.nan)
    vol20 = float(last.get("波动率20") or np.nan)
    vmean20 = float(last.get("成交量均值20") or np.nan)
    vlast = float(last.get("成交量") or np.nan)

    trend = 0.0
    if np.isfinite(ma20) and np.isfinite(ma60):
        if close > ma20 > ma60:
            trend = 35.0
            notes.append("趋势：收盘 > MA20 > MA60（偏强）")
        elif close > ma20 and close > ma60:
            trend = 25.0
            notes.append("趋势：收盘高于 MA20/MA60（偏强）")
        elif close < ma20 < ma60:
            trend = -25.0
            notes.append("趋势：收盘 < MA20 < MA60（偏弱）")
        else:
            trend = 5.0
            notes.append("趋势：均线缠绕（中性）")
    else:
        notes.append("趋势：数据不足（至少 60 根K线更好）")

    momentum = 0.0
    if np.isfinite(mom20):
        momentum += float(np.clip(mom20 * 100, -20, 20))
    if np.isfinite(mom60):
        momentum += float(np.clip(mom60 * 80, -20, 20))
    momentum = float(np.clip(momentum, -25, 25))
    if np.isfinite(mom20) or np.isfinite(mom60):
        notes.append("动量：近 20/60 日涨跌幅加权")

    risk = 0.0
    if np.isfinite(vol20):
        # 波动率越高扣分越多（上限 20）
        risk = -float(np.clip((vol20 - 0.25) * 40, 0, 20))
        notes.append(f"风险：20日年化波动率约 {vol20:.2f}")
    else:
        notes.append("风险：数据不足（至少 20 根K线更好）")

    liquidity = 0.0
    if np.isfinite(vmean20) and np.isfinite(vlast) and vmean20 > 0:
        ratio = vlast / vmean20
        liquidity = float(np.clip((ratio - 1.0) * 10, -5, 10))
        if ratio >= 1.5:
            notes.append("流动性：放量（成交量显著高于 20 日均值）")
        elif ratio <= 0.7:
            notes.append("流动性：缩量（成交量低于 20 日均值）")
        else:
            notes.append("流动性：正常")
    else:
        notes.append("流动性：无成交量或数据不足")

    total = float(np.clip(trend + momentum + risk + liquidity, -50, 80))
    return ScoreBreakdown(total=total, trend=trend, momentum=momentum, risk=risk, liquidity=liquidity, notes=notes)

