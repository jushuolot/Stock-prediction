"""腾讯财经公开接口（A 股 K 线 / 实时报价），作为东财失败时的备用源。"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import pandas as pd
import requests

from src.providers.ticker_util import is_bj_code

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://gu.qq.com/",
}
_KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
_QUOTE_URL = "https://qt.gtimg.cn/q="

_KLINE_MAP = {
    "日线": "day",
    "日K": "day",
    "周线": "week",
    "周K": "week",
    "月线": "month",
    "月K": "month",
}


def tencent_symbol(code6: str) -> str:
    c = str(code6).strip().zfill(6)
    if c[0] == "6":
        return f"sh{c}"
    if is_bj_code(c):
        return f"bj{c}"
    return f"sz{c}"


def _parse_quote_fields(text: str) -> list[str] | None:
    m = re.search(r'="([^"]+)"', text or "")
    if not m:
        return None
    return m.group(1).split("~")


def fetch_quote_date(code6: str) -> date | None:
    """实时报价中的行情日期（YYYYMMDD）。"""
    sym = tencent_symbol(code6)
    try:
        r = requests.get(f"{_QUOTE_URL}{sym}", headers=_HEADERS, timeout=12)
        r.raise_for_status()
        fields = _parse_quote_fields(r.text)
        if not fields or len(fields) <= 30:
            return None
        raw = str(fields[30]).strip()
        if len(raw) >= 8 and raw[:8].isdigit():
            return datetime.strptime(raw[:8], "%Y%m%d").date()
    except Exception:
        return None
    return None


def fetch_a_kline(
    code6: str,
    *,
    kline: str = "日线",
    start: date,
    end: date,
) -> pd.DataFrame:
    """日/周/月 K 线（前复权）。"""
    period = _KLINE_MAP.get(kline)
    if not period:
        raise RuntimeError(f"腾讯财经不支持 {kline} K 线")

    sym = tencent_symbol(code6)
    param = f"{sym},{period},{start.isoformat()},{end.isoformat()},640,qfq"
    r = requests.get(_KLINE_URL, params={"param": param}, headers=_HEADERS, timeout=20)
    r.raise_for_status()
    j = r.json()
    data = (j.get("data") or {}).get(sym) or {}
    rows_raw: list[Any] = data.get(period) or data.get(f"qfq{period}") or []
    if not rows_raw:
        raise RuntimeError(f"腾讯财经未返回 K 线：{code6}")

    rows: list[dict[str, Any]] = []
    for item in rows_raw:
        if not isinstance(item, (list, tuple)) or len(item) < 6:
            continue
        try:
            rows.append(
                {
                    "日期": str(item[0]),
                    "开盘": float(item[1]),
                    "收盘": float(item[2]),
                    "最高": float(item[3]),
                    "最低": float(item[4]),
                    "成交量": float(item[5]),
                }
            )
        except (TypeError, ValueError):
            continue

    if not rows:
        raise RuntimeError(f"腾讯财经 K 线解析失败：{code6}")

    df = pd.DataFrame(rows)
    df["日期"] = pd.to_datetime(df["日期"])
    df["标的代码"] = str(code6).zfill(6)
    df["数据来源"] = "腾讯财经"
    return df
