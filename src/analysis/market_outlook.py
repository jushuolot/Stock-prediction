"""大盘与个股长线展望（P111）：1~2 周大跌概率 + 2~8 周趋势判断。

基于指数 K 线、波动率、市场广度（涨跌家数比）的规则模型。
输出为「概率估计」，非精确预测；供花园页与云端 cron 共用。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.analysis.signals import add_indicators
from src.providers import yahoo

FetchKlineFn = Callable[..., tuple[pd.DataFrame, str]]

# 指数代理（Yahoo）
INDEX_PROXIES: list[tuple[str, str, str]] = [
    ("000001.SS", "上证指数", "A股"),
    ("399006.SZ", "创业板指", "A股"),
    ("^HSI", "恒生指数", "港股"),
    ("^GSPC", "标普500", "美股"),
]

# 大跌定义：未来 1~2 周内指数从当前水平再跌 ≥5%（规则代理，用当下结构估算概率）
CRASH_THRESHOLD_PCT = 5.0


@dataclass(frozen=True)
class IndexSnapshot:
    ticker: str
    name: str
    region: str
    close: float | None
    pct_5d: float | None
    pct_20d: float | None
    drawdown_20d_pct: float | None
    above_ma20: bool | None
    trend: str  # 多头/空头/震荡
    vol_ratio: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketOutlook:
    """全市场长线风向标。"""

    as_of: str
    crash_prob_1_2w_pct: float
    crash_label: str
    outlook_2w: str
    outlook_4_8w: str
    breadth_adv_pct: float | None
    indices: list[IndexSnapshot]
    drivers: list[str]
    advice: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "as_of": self.as_of,
            "crash_prob_1_2w_pct": self.crash_prob_1_2w_pct,
            "crash_label": self.crash_label,
            "outlook_2w": self.outlook_2w,
            "outlook_4_8w": self.outlook_4_8w,
            "breadth_adv_pct": self.breadth_adv_pct,
            "indices": [i.as_dict() for i in self.indices],
            "drivers": list(self.drivers),
            "advice": self.advice,
        }


@dataclass(frozen=True)
class StockLongOutlook:
    code: str
    name: str
    outlook_2w: str
    outlook_4_8w: str
    risk_note: str
    trend_score: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def _fetch_index_df(ticker: str, *, days: int = 160) -> pd.DataFrame | None:
    end = date.today()
    start = end - timedelta(days=days)
    if ticker.endswith((".SS", ".SZ")):
        code = ticker.split(".")[0].zfill(6)
        try:
            from src.providers import fresh_fetch

            df, _ = fresh_fetch.fetch_a_kline_fresh(code, kline="日线", start=start, end=end)
            return df
        except Exception:
            pass
    try:
        return yahoo.fetch_history(ticker, start=start, end=end, interval="1d")
    except Exception:
        return None


def _index_snapshot(ticker: str, name: str, region: str, df: pd.DataFrame | None) -> IndexSnapshot:
    if df is None or len(df) < 25:
        return IndexSnapshot(
            ticker=ticker,
            name=name,
            region=region,
            close=None,
            pct_5d=None,
            pct_20d=None,
            drawdown_20d_pct=None,
            above_ma20=None,
            trend="数据不足",
            vol_ratio=None,
        )

    work = add_indicators(df.sort_values("日期"))
    close = pd.to_numeric(work["收盘"], errors="coerce")
    last = float(close.iloc[-1])
    ma20 = _f(work["MA20"].iloc[-1])
    ma60 = _f(work["MA60"].iloc[-1])

    pct_5d = _f(close.pct_change(5).iloc[-1])
    if pct_5d is not None:
        pct_5d *= 100.0
    pct_20d = _f(close.pct_change(20).iloc[-1])
    if pct_20d is not None:
        pct_20d *= 100.0

    hi20 = float(close.tail(20).max())
    dd = ((last / hi20) - 1) * 100.0 if hi20 > 0 else None

    above = ma20 is not None and last > ma20
    if ma20 is not None and ma60 is not None:
        if last > ma20 > ma60:
            trend = "多头"
        elif last < ma20 < ma60:
            trend = "空头"
        else:
            trend = "震荡"
    else:
        trend = "震荡"

    vol_r = None
    if "成交量" in work.columns:
        vol = pd.to_numeric(work["成交量"], errors="coerce")
        if len(vol) >= 21:
            v_last = float(vol.iloc[-1])
            v_avg = float(vol.tail(21).iloc[:-1].mean())
            if v_avg > 0:
                vol_r = v_last / v_avg

    return IndexSnapshot(
        ticker=ticker,
        name=name,
        region=region,
        close=round(last, 2),
        pct_5d=round(pct_5d, 2) if pct_5d is not None else None,
        pct_20d=round(pct_20d, 2) if pct_20d is not None else None,
        drawdown_20d_pct=round(dd, 2) if dd is not None else None,
        above_ma20=above,
        trend=trend,
        vol_ratio=round(vol_r, 2) if vol_r is not None else None,
    )


def compute_market_breadth(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]] | None = None,
) -> tuple[float | None, str]:
    """A 股样本广度：上涨家数占比。"""
    if fetch_ranking is None:
        from src.providers import market_data

        def fetch_ranking():
            return market_data.fetch_a_ranking_multi(board="涨幅榜", limit=100)

    try:
        df, _ = fetch_ranking()
    except Exception:
        return None, ""
    if df is None or df.empty or "涨跌幅%" not in df.columns:
        return None, ""

    pcts = pd.to_numeric(df["涨跌幅%"], errors="coerce").dropna()
    if pcts.empty:
        return None, ""
    adv = float((pcts > 0).sum()) / len(pcts) * 100.0
    return round(adv, 1), f"样本 {len(pcts)} 只"


def _crash_prob_from_signals(
    indices: list[IndexSnapshot],
    breadth_adv: float | None,
) -> tuple[float, list[str]]:
    """合成 1~2 周大跌概率（0~100）。"""
    score = 28.0
    drivers: list[str] = []

    a_indices = [i for i in indices if i.region == "A股" and i.close is not None]
    global_indices = [i for i in indices if i.region != "A股" and i.close is not None]

    for idx in a_indices:
        if idx.trend == "空头":
            score += 14
            drivers.append(f"{idx.name}均线空头")
        elif idx.trend == "多头":
            score -= 8
            drivers.append(f"{idx.name}趋势偏多")

        if idx.drawdown_20d_pct is not None and idx.drawdown_20d_pct <= -8:
            score += 12
            drivers.append(f"{idx.name}距20日高点已回撤{abs(idx.drawdown_20d_pct):.1f}%")
        elif idx.drawdown_20d_pct is not None and idx.drawdown_20d_pct >= -2:
            score -= 4

        if idx.pct_5d is not None and idx.pct_5d <= -4:
            score += 10
            drivers.append(f"{idx.name}近5日跌{idx.pct_5d:.1f}%")
        elif idx.pct_5d is not None and idx.pct_5d >= 3:
            score -= 5

        if idx.vol_ratio is not None and idx.vol_ratio >= 1.4 and (idx.pct_5d or 0) < 0:
            score += 8
            drivers.append(f"{idx.name}下跌放量")

    weak_global = sum(1 for i in global_indices if i.trend == "空头" or (i.pct_5d or 0) < -2)
    if weak_global >= 2:
        score += 10
        drivers.append("港股/美股同步偏弱")
    elif weak_global == 0 and global_indices:
        score -= 5
        drivers.append("外围市场相对稳定")

    if breadth_adv is not None:
        if breadth_adv < 38:
            score += 14
            drivers.append(f"市场广度弱（仅{breadth_adv:.0f}%上涨）")
        elif breadth_adv > 62:
            score -= 12
            drivers.append(f"市场广度高（{breadth_adv:.0f}%上涨）")
        else:
            drivers.append(f"涨跌家数比中性（{breadth_adv:.0f}%上涨）")

    prob = float(np.clip(score, 8, 82))
    return round(prob, 1), drivers[:6]


def _outlook_labels(
    prob: float,
    indices: list[IndexSnapshot],
) -> tuple[str, str, str]:
    a_main = next((i for i in indices if i.name == "上证指数"), None)
    trend = a_main.trend if a_main else "震荡"

    if prob >= 55:
        o2 = "偏空 · 宜控仓防回撤"
        o48 = "谨慎 · 优先防守与现金"
        label = "偏高"
    elif prob >= 40:
        o2 = "震荡偏弱 · 少追多等"
        o48 = "结构性分化 · 精选个股"
        label = "中等"
    elif prob >= 25:
        o2 = "中性 · 可正常选股"
        o48 = "震荡偏多 · 关注主线"
        label = "偏低"
    else:
        o2 = "偏多 · 可积极布局"
        o48 = "趋势友好 · 持有为主"
        label = "低"

    if trend == "多头" and prob < 45:
        o48 = "中期趋势仍多 · 回调视为机会"
    if trend == "空头" and prob >= 45:
        o48 = "中期趋势承压 · 反弹宜减"

    return o2, o48, label


def _advice_text(prob: float, outlook_2w: str) -> str:
    if prob >= 55:
        return (
            f"系统估计未来 1~2 周出现指数级大跌（≥{CRASH_THRESHOLD_PCT:.0f}%）的概率 **{prob:.0f}%**（{outlook_2w}）。"
            "建议：降低仓位、避免追高、保留现金。"
        )
    if prob >= 40:
        return (
            f"未来 1~2 周大跌概率 **{prob:.0f}%**，不算极端但需留神。"
            "建议：分散持仓、止损纪律、不重仓单票。"
        )
    return (
        f"未来 1~2 周大跌概率 **{prob:.0f}%**（相对可控）。"
        "建议：可按计划选股，仍须设好止损。"
    )


def compute_market_outlook(
    *,
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]] | None = None,
    as_of: date | None = None,
) -> MarketOutlook:
    """计算全市场 1~2 周大跌概率与 2~8 周展望。"""
    day = as_of or date.today()
    indices: list[IndexSnapshot] = []
    for ticker, name, region in INDEX_PROXIES:
        df = _fetch_index_df(ticker)
        indices.append(_index_snapshot(ticker, name, region, df))

    breadth, _ = compute_market_breadth(fetch_ranking)
    prob, drivers = _crash_prob_from_signals(indices, breadth)
    o2, o48, crash_label = _outlook_labels(prob, indices)

    return MarketOutlook(
        as_of=day.isoformat(),
        crash_prob_1_2w_pct=prob,
        crash_label=crash_label,
        outlook_2w=o2,
        outlook_4_8w=o48,
        breadth_adv_pct=breadth,
        indices=indices,
        drivers=drivers,
        advice=_advice_text(prob, o2),
    )


def analyze_stock_long_term(
    df: pd.DataFrame,
    *,
    code: str,
    name: str,
) -> StockLongOutlook | None:
    """个股 2~8 周长线结构（基于日 K）。"""
    if df is None or len(df) < 60:
        return None

    work = add_indicators(df.sort_values("日期"))
    close = pd.to_numeric(work["收盘"], errors="coerce")
    last = float(close.iloc[-1])
    ma20 = _f(work["MA20"].iloc[-1])
    ma60 = _f(work["MA60"].iloc[-1])
    mom20 = _f(work["动量20"].iloc[-1])
    mom60 = _f(work["动量60"].iloc[-1])
    vol20 = _f(work["波动率20"].iloc[-1])

    trend_score = 50.0
    if ma20 is not None and ma60 is not None:
        if last > ma20 > ma60:
            trend_score += 22
        elif last < ma20 < ma60:
            trend_score -= 22
        elif last > ma20:
            trend_score += 8
        else:
            trend_score -= 8

    if mom20 is not None:
        trend_score += float(np.clip(mom20 * 80, -15, 15))
    if mom60 is not None:
        trend_score += float(np.clip(mom60 * 50, -10, 10))

    trend_score = float(np.clip(trend_score, 0, 100))

    if trend_score >= 68:
        o2, o48 = "2周偏多", "4~8周趋势友好"
        risk = "长线结构偏强，注意短线过热"
    elif trend_score >= 52:
        o2, o48 = "2周中性", "4~8周震荡待方向"
        risk = "均线附近震荡，宜等放量突破"
    elif trend_score >= 38:
        o2, o48 = "2周偏弱", "4~8周谨慎"
        risk = "趋势承压，不宜重仓抄底"
    else:
        o2, o48 = "2周偏空", "4~8周弱势"
        risk = "空头结构，仅适合极小仓博弈"

    if vol20 is not None and vol20 > 0.35:
        risk += "；波动率偏高"

    return StockLongOutlook(
        code=code,
        name=name,
        outlook_2w=o2,
        outlook_4_8w=o48,
        risk_note=risk,
        trend_score=round(trend_score, 1),
    )


def outlook_to_markdown(outlook: MarketOutlook) -> str:
    lines = [
        f"# 大盘长线风向标 · {outlook.as_of}",
        "",
        f"## 未来 1~2 周大跌概率：**{outlook.crash_prob_1_2w_pct:.0f}%**（{outlook.crash_label}）",
        "",
        f"- **2 周看法：** {outlook.outlook_2w}",
        f"- **4~8 周看法：** {outlook.outlook_4_8w}",
        "",
        outlook.advice,
        "",
        "### 主要依据",
    ]
    for d in outlook.drivers:
        lines.append(f"- {d}")
    if outlook.breadth_adv_pct is not None:
        lines.append(f"- A股样本上涨占比：**{outlook.breadth_adv_pct:.0f}%**")
    lines.extend(["", "### 指数快照", ""])
    lines.append("| 指数 | 趋势 | 5日% | 20日% | 距20日高% |")
    lines.append("|------|------|------|-------|-----------|")
    for i in outlook.indices:
        if i.close is None:
            continue
        lines.append(
            f"| {i.name} | {i.trend} | "
            f"{i.pct_5d if i.pct_5d is not None else '—'} | "
            f"{i.pct_20d if i.pct_20d is not None else '—'} | "
            f"{i.drawdown_20d_pct if i.drawdown_20d_pct is not None else '—'} |"
        )
    lines.extend(["", "*规则模型估计，非投资建议。*"])
    return "\n".join(lines)


def enrich_picks_with_long_term(
    picks: list[dict[str, Any]],
    fetch_fn: FetchKlineFn,
) -> list[dict[str, Any]]:
    """为推荐列表附加个股长线字段。"""
    end = date.today()
    start = end - timedelta(days=200)
    out: list[dict[str, Any]] = []
    for p in picks:
        row = dict(p)
        code = str(p.get("code") or "")
        name = str(p.get("name") or code)
        item = {"代码": code, "名称": name, "类型": "A", "市场": p.get("market") or "A股"}
        try:
            df, _ = fetch_fn(item, start=start, end=end, kline="日线")
            lo = analyze_stock_long_term(df, code=code, name=name)
            if lo:
                row["long_2w"] = lo.outlook_2w
                row["long_4_8w"] = lo.outlook_4_8w
                row["long_trend_score"] = lo.trend_score
                row["long_risk"] = lo.risk_note
        except Exception:
            pass
        out.append(row)
    return out
