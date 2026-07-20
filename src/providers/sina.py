"""新浪财经公开接口（A 股榜单/行情/K 线），作为东方财富的备用源。"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import pandas as pd
import requests

from src.providers.tencent import tencent_symbol
from src.providers.ticker_util import a_market_label, yahoo_ticker_a

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn/",
}
_LIST_URL = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
_KLINE_URL = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"


def _to_code6(symbol: str) -> str:
    s = (symbol or "").strip().lower()
    m = re.search(r"(?:sh|sz|bj)(\d{6})", s)
    if m:
        return m.group(1)
    if s.isdigit():
        return s.zfill(6)[:6]
    return s


def _market_label(code6: str) -> str:
    return a_market_label(code6)


def fetch_a_kline(
    code6: str,
    *,
    kline: str = "日线",
    start: date | None = None,
    end: date | None = None,
    datalen: int = 320,
) -> pd.DataFrame:
    """日 K 线（新浪仅支持日线）。"""
    if kline not in ("日线", "日K"):
        raise RuntimeError(f"新浪财经不支持 {kline} K 线")
    sym = tencent_symbol(code6)
    try:
        r = requests.get(
            _KLINE_URL,
            params={"symbol": sym, "scale": 240, "ma": "no", "datalen": str(datalen)},
            headers=_HEADERS,
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        raise RuntimeError(f"新浪财经 K 线请求失败：{code6}") from exc

    if not isinstance(data, list) or not data:
        raise RuntimeError(f"新浪财经未返回 K 线：{code6}")

    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            rows.append(
                {
                    "日期": str(item.get("day") or ""),
                    "开盘": float(item.get("open") or 0),
                    "收盘": float(item.get("close") or 0),
                    "最高": float(item.get("high") or 0),
                    "最低": float(item.get("low") or 0),
                    "成交量": float(item.get("volume") or 0),
                }
            )
        except (TypeError, ValueError):
            continue

    if not rows:
        raise RuntimeError(f"新浪财经 K 线解析失败：{code6}")

    df = pd.DataFrame(rows)
    df["日期"] = pd.to_datetime(df["日期"])
    if start is not None:
        df = df[df["日期"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["日期"] <= pd.Timestamp(end)]
    if df.empty:
        raise RuntimeError(f"新浪财经 K 线区间为空：{code6}")
    df["标的代码"] = str(code6).zfill(6)
    df["数据来源"] = "新浪财经"
    return df


def fetch_a_ranking(*, board: str = "涨幅榜", limit: int = 50) -> pd.DataFrame:
    sort = "changepercent"
    asc = 0
    if board == "跌幅榜":
        asc = 1
    elif board == "成交额榜":
        sort, asc = "amount", 0
    elif board == "换手率榜":
        sort, asc = "turnoverratio", 0

    params = {"page": "1", "num": str(limit), "sort": sort, "asc": str(asc), "node": "hs_a"}
    try:
        r = requests.get(_LIST_URL, params=params, headers=_HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.DataFrame()

    if not isinstance(data, list):
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        code = _to_code6(str(item.get("symbol") or item.get("code") or ""))
        name = str(item.get("name") or "").strip()
        if len(code) != 6 or not name:
            continue
        def _f(k: str) -> float | None:
            try:
                return float(item.get(k))
            except (TypeError, ValueError):
                return None

        rows.append(
            {
                "代码": code,
                "名称": name,
                "市场": _market_label(code),
                "类型": "A",
                "最新价": _f("trade"),
                "涨跌幅%": _f("changepercent"),
                "涨跌额": _f("pricechange"),
                "成交量": _f("volume"),
                "成交额": _f("amount"),
                "振幅%": _f("swing"),
                "换手率%": _f("turnoverratio"),
                "Yahoo代码": yahoo_ticker_a(code),
                "数据来源": "新浪财经",
            }
        )
    return pd.DataFrame(rows)
