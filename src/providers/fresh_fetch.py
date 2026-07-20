"""多源拉取 + 新鲜度校验：拒绝滞后 Yahoo/备用源数据。"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import pandas as pd

from src.providers import eastmoney, sina, yahoo
from src.providers.ticker_util import is_bj_code, yahoo_ticker_a
from src.util.data_date_label import parse_bar_date

_CN_TZ = timezone(timedelta(hours=8))

_IV_MAP = {
    "日线": "1d",
    "日K": "1d",
    "周线": "1wk",
    "周K": "1wk",
    "月线": "1mo",
    "月K": "1mo",
}


def china_now() -> datetime:
    return datetime.now(_CN_TZ)


def is_a_trading_weekday(d: date) -> bool:
    return d.weekday() < 5


def last_trading_day_on_or_before(d: date) -> date:
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def prev_trading_day(d: date) -> date:
    return last_trading_day_on_or_before(d - timedelta(days=1))


def expected_latest_bar_date(*, now: datetime | None = None) -> tuple[date, date]:
    """
    A 股日 K 可接受的最后交易日区间 (lo, hi)。
    交易日 15:00 前：今天或昨天；15:00 后：必须今天；周末：最近周五。
    """
    ref = now or china_now()
    today = ref.date()
    if not is_a_trading_weekday(today):
        last = last_trading_day_on_or_before(today)
        return last, last
    if ref.hour < 15:
        return prev_trading_day(today), today
    return today, today


def is_bar_fresh(
    bar_date: date | str | datetime | None,
    *,
    market: str = "A",
    now: datetime | None = None,
) -> bool:
    if market != "A":
        return bar_date is not None
    parsed = parse_bar_date(bar_date)
    if parsed is None:
        return False
    lo, hi = expected_latest_bar_date(now=now)
    return lo <= parsed <= hi


def last_bar_date(df: pd.DataFrame | None) -> date | None:
    if df is None or df.empty or "日期" not in df.columns:
        return None
    return parse_bar_date(df["日期"].iloc[-1])


def _kline_fresh(df: pd.DataFrame | None, *, now: datetime | None = None) -> bool:
    return is_bar_fresh(last_bar_date(df), market="A", now=now)


def _lines_to_df(lines: list[str], code6: str, source: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for line in lines:
        p = line.split(",")
        if len(p) < 7:
            continue
        try:
            rows.append(
                {
                    "日期": p[0],
                    "开盘": float(p[1]),
                    "收盘": float(p[2]),
                    "最高": float(p[3]),
                    "最低": float(p[4]),
                    "成交量": float(p[5]),
                    "成交额": float(p[6]),
                    "振幅": float(p[7]) if len(p) > 7 and p[7] else 0.0,
                    "涨跌幅": float(p[8]) if len(p) > 8 and p[8] else 0.0,
                    "涨跌额": float(p[9]) if len(p) > 9 and p[9] else 0.0,
                    "换手率": float(p[10]) if len(p) > 10 and p[10] else 0.0,
                }
            )
        except (ValueError, TypeError):
            continue
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"{source} K 线解析为空：{code6}")
    df["日期"] = pd.to_datetime(df["日期"])
    df["标的代码"] = str(code6).zfill(6)
    df["数据来源"] = source
    return df


def _try_em_kline(
    code6: str,
    *,
    kline: str,
    start: date,
    end: date,
    now: datetime | None,
) -> tuple[pd.DataFrame, str] | None:
    try:
        lines = eastmoney._fetch_kline_lines(code6, kline=kline, start=start, end=end)
        df = _lines_to_df(lines, code6, "东方财富")
        if _kline_fresh(df, now=now):
            return df, "东方财富"
    except Exception:
        return None
    return None


def _try_sina_kline(
    code6: str,
    *,
    kline: str,
    start: date,
    end: date,
    now: datetime | None,
) -> tuple[pd.DataFrame, str] | None:
    if kline not in ("日线", "日K"):
        return None
    try:
        df = sina.fetch_a_kline(code6, kline=kline, start=start, end=end)
        if _kline_fresh(df, now=now):
            return df, "新浪财经"
    except Exception:
        return None
    return None


def _try_tencent_kline(
    code6: str,
    *,
    kline: str,
    start: date,
    end: date,
    now: datetime | None,
) -> tuple[pd.DataFrame, str] | None:
    if kline not in _IV_MAP:
        return None
    try:
        from src.providers import tencent

        df = tencent.fetch_a_kline(code6, kline=kline, start=start, end=end)
        if _kline_fresh(df, now=now):
            return df, "腾讯财经"
    except Exception:
        return None
    return None


def _try_yahoo_kline(
    code6: str,
    *,
    kline: str,
    start: date,
    end: date,
    now: datetime | None,
) -> tuple[pd.DataFrame, str] | None:
    if is_bj_code(code6):
        return None
    yh = yahoo_ticker_a(code6)
    if not yh:
        return None
    iv = _IV_MAP.get(kline, "1d")
    try:
        df = yahoo.fetch_history(yh, start=start, end=end, interval=iv)
        if _kline_fresh(df, now=now):
            df = df.copy()
            df["数据来源"] = "Yahoo Finance"
            return df, "Yahoo Finance"
    except Exception:
        return None
    return None


def fetch_a_kline_fresh(
    code6: str,
    *,
    kline: str,
    start: date,
    end: date,
    now: datetime | None = None,
) -> tuple[pd.DataFrame, str]:
    """东财 → 腾讯 → Yahoo，返回首个最后 K 线日期新鲜的源。"""
    code = str(code6).strip().zfill(6)
    errors: list[str] = []

    for label, fn in (
        ("东方财富", lambda: _try_em_kline(code, kline=kline, start=start, end=end, now=now)),
        ("新浪财经", lambda: _try_sina_kline(code, kline=kline, start=start, end=end, now=now)),
        ("腾讯财经", lambda: _try_tencent_kline(code, kline=kline, start=start, end=end, now=now)),
        ("Yahoo Finance", lambda: _try_yahoo_kline(code, kline=kline, start=start, end=end, now=now)),
    ):
        hit = fn()
        if hit is not None:
            return hit
        errors.append(f"{label} 无新鲜数据")

    lo, hi = expected_latest_bar_date(now=now)
    raise RuntimeError(
        f"未获取到 {code} 的新鲜 {kline}（需 {lo}~{hi}）。"
        f"已尝试：{'；'.join(errors)}"
    )


def is_ranking_fresh(
    df: pd.DataFrame | None,
    *,
    probe_code: str = "600519",
    now: datetime | None = None,
) -> bool:
    """榜单样本行有效，且探针股行情日期新鲜。"""
    if df is None or df.empty:
        return False
    sample = df.head(5)
    if "最新价" not in sample.columns:
        return False
    prices = pd.to_numeric(sample["最新价"], errors="coerce").dropna()
    if len(prices) < 3:
        return False
    if "涨跌幅%" in sample.columns:
        pcts = pd.to_numeric(sample["涨跌幅%"], errors="coerce").dropna()
        if len(pcts) < 3:
            return False

    code = str(probe_code).strip().zfill(6)
    try:
        from src.providers import tencent

        qd = tencent.fetch_quote_date(code)
        if is_bar_fresh(qd, market="A", now=now):
            return True
    except Exception:
        pass

    # 探针 K 线兜底（不强制与榜单同源，仅校验市场有当日数据）
    try:
        end = (now or china_now()).date()
        start = end - timedelta(days=10)
        _, _ = fetch_a_kline_fresh(code, kline="日线", start=start, end=end, now=now)
        return True
    except Exception:
        return False


def fetch_a_ranking_fresh(
    *,
    board: str = "涨幅榜",
    limit: int = 50,
    now: datetime | None = None,
) -> tuple[pd.DataFrame, str]:
    """东财 → 新浪，返回首个通过新鲜度校验的榜单。"""
    errors: list[str] = []

    df = eastmoney.fetch_a_ranking(board=board, limit=limit)
    if not df.empty and is_ranking_fresh(df, now=now):
        if "数据来源" not in df.columns:
            df = df.copy()
            df["数据来源"] = "东方财富"
        if "类型" not in df.columns:
            df["类型"] = "A"
        return df, "东方财富"
    if not df.empty:
        errors.append("东方财富 榜单滞后")
    else:
        errors.append("东方财富 无数据")

    df = sina.fetch_a_ranking(board=board, limit=limit)
    if not df.empty and is_ranking_fresh(df, now=now):
        if "类型" not in df.columns:
            df["类型"] = "A"
        return df, "新浪财经（东财不可用时的备用）"
    if not df.empty:
        errors.append("新浪财经 榜单滞后")
    else:
        errors.append("新浪财经 无数据")

    lo, hi = expected_latest_bar_date(now=now)
    raise RuntimeError(
        f"A 股 {board} 无新鲜榜单（需行情日 {lo}~{hi}）。"
        f"已尝试：{'；'.join(errors)}"
    )
