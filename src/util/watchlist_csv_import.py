"""自选 CSV 导入（P64）：解析代码列并合并进自选（去重）。"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

from src.providers.ticker_util import a_market_label, yahoo_ticker_a
from src.util.currency import enrich_watchlist_item
from src.util.watchlist_backup import merge_watchlist

_TICKER_HEADERS = frozenset(
    {
        "代码",
        "code",
        "ticker",
        "symbol",
        "股票代码",
        "证券代码",
        "标的",
    }
)


def _normalize_ticker(raw: str) -> str:
    t = str(raw or "").strip().strip('"').strip("'")
    if not t:
        return ""
    if t.upper().endswith(".HK"):
        base = t[:-3].strip()
        if base.isdigit():
            return f"{int(base):04d}.HK"
        return t.upper()
    if t.isdigit() and len(t) <= 6:
        return t.zfill(6)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.\-]*", t):
        return t.upper()
    return t


def _detect_ticker_column(fieldnames: list[str] | None) -> str | None:
    if not fieldnames:
        return None
    lower_map = {str(h).strip().lower(): str(h).strip() for h in fieldnames if h}
    for key in ("代码", "code", "ticker", "symbol", "股票代码", "证券代码", "标的"):
        if key.lower() in lower_map:
            return lower_map[key.lower()]
    return None


def parse_tickers_from_csv(raw: bytes | str) -> list[str]:
    """从 CSV 提取代码列；无表头时取首列。"""
    text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else str(raw)
    text = text.strip()
    if not text:
        return []
    buf = io.StringIO(text)
    try:
        sample = text[:2048]
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(buf, dialect)
    rows = list(reader)
    if not rows:
        return []
    first = [str(c).strip() for c in rows[0]]
    col_idx = 0
    start = 0
    header = _detect_ticker_column(first)
    if header and header in first:
        col_idx = first.index(header)
        start = 1
    elif _detect_ticker_column(first) is None and first and not _looks_like_ticker(first[0]):
        start = 1
    seen: set[str] = set()
    out: list[str] = []
    for row in rows[start:]:
        if not row or col_idx >= len(row):
            continue
        code = _normalize_ticker(row[col_idx])
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(code)
    return out


def _looks_like_ticker(val: str) -> bool:
    v = str(val or "").strip()
    if not v:
        return False
    if v.isdigit():
        return True
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9.\-]*", v))


def ticker_to_watchlist_item(ticker: str) -> dict[str, Any]:
    """由裸代码构造最小自选条目（名称暂用代码）。"""
    code = _normalize_ticker(ticker)
    if not code:
        raise ValueError("无效代码")
    kind = "A"
    market = "A股"
    yahoo = ""
    name = code
    if code.isdigit() and len(code) == 6:
        market = a_market_label(code)
        yahoo = yahoo_ticker_a(code)
        kind = "A"
    elif code.endswith(".HK"):
        kind = "HK"
        market = "港股"
        yahoo = code
    elif re.fullmatch(r"[A-Z][A-Z0-9.\-]*", code):
        kind = "US"
        market = "美股"
        yahoo = code
    return enrich_watchlist_item(
        {
            "名称": name,
            "代码": code,
            "类型": kind,
            "市场": market,
            "Yahoo": yahoo,
        }
    )


def merge_csv_tickers_into_watchlist(
    watchlist: list[dict[str, Any]],
    tickers: list[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """合并代码进自选，保留已有顺序并去重。"""
    incoming: list[dict[str, Any]] = []
    skipped_invalid = 0
    for raw in tickers:
        try:
            incoming.append(ticker_to_watchlist_item(raw))
        except ValueError:
            skipped_invalid += 1
    before = len(watchlist)
    merged = merge_watchlist(watchlist, incoming)
    added = max(0, len(merged) - before)
    dupes = max(0, len(incoming) - skipped_invalid - added)
    return merged, {
        "parsed": len(tickers),
        "added": added,
        "duplicates": dupes,
        "invalid": skipped_invalid,
    }


def apply_csv_import(
    watchlist: list[dict[str, Any]],
    raw: bytes | str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    tickers = parse_tickers_from_csv(raw)
    return merge_csv_tickers_into_watchlist(watchlist, tickers)
