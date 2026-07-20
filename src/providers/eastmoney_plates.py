"""东方财富 · 行业/概念/地区板块与资金流向（clist）。"""

from __future__ import annotations

import re
import time
from typing import Any

import pandas as pd

from src.providers.eastmoney import EM_CLIST_FALLBACK, EM_CLIST_URL, _get

# 板块类型 → 东财 fs 参数（与 quote.eastmoney.com 板块页一致）
PLATE_FS: dict[str, str] = {
    "行业板块": "m:90+t:2",
    "概念板块": "m:90+t:3",
    "地区板块": "m:90+t:1",
}

PLATE_CLIST_URLS: tuple[str, ...] = (
    EM_CLIST_URL,
    EM_CLIST_FALLBACK,
    "https://80.push2.eastmoney.com/api/qt/clist/get",
    "https://43.push2.eastmoney.com/api/qt/clist/get",
    "https://29.push2.eastmoney.com/api/qt/clist/get",
    "https://push2delay.eastmoney.com/api/qt/clist/get",
)

# f62=主力净流入；f128/f104=领涨股名；f136=领涨股代码；f140=领涨股涨跌幅
PLATE_FIELDS = "f12,f14,f2,f3,f5,f62,f104,f128,f136,f140"


def _float(v: Any) -> float | None:
    if v is None or v == "-":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _iter_clist_diff(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data:
        return []
    diff = data.get("diff")
    if not diff:
        return []
    if isinstance(diff, list):
        return [x for x in diff if isinstance(x, dict)]
    if isinstance(diff, dict):
        return [x for x in diff.values() if isinstance(x, dict)]
    return []


def _plate_link(code: str) -> str:
    c = str(code or "").strip().upper()
    if not c:
        return ""
    if not c.startswith("BK"):
        c = f"BK{c}" if c.isdigit() else c
    return f"https://quote.eastmoney.com/bk/90.{c}.html"


def _lead_stock_code(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s or s == "-":
        return ""
    if "." in s:
        s = s.split(".")[-1]
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 6:
        return digits.zfill(6)[-6:]
    return digits


def _main_inflow_wan(v: Any) -> float | None:
    """东财 fltt=2 下 f62 为元，展示为万元便于阅读。"""
    yuan = _float(v)
    if yuan is None:
        return None
    return round(yuan / 10000.0, 2)


def _parse_plate_row(item: dict[str, Any], *, category: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    code = str(item.get("f12") or "").strip()
    name = str(item.get("f14") or "").strip()
    if not code or not name:
        return None
    lead_name = str(item.get("f128") or item.get("f104") or "").strip()
    lead_code = _lead_stock_code(item.get("f136"))
    lead_pct = _float(item.get("f140"))
    pct = _float(item.get("f3"))
    return {
        "板块代码": code,
        "板块名称": name,
        "板块类型": category,
        "最新价": _float(item.get("f2")),
        "涨跌幅": pct,
        "涨跌额": _float(item.get("f5")),
        "主力净流入": _main_inflow_wan(item.get("f62")),
        "领涨股": lead_name or "—",
        "领涨股代码": lead_code,
        "领涨股涨跌幅": lead_pct,
        "相关链接": _plate_link(code),
    }


def _fetch_plate_rows(
    *,
    fs: str,
    fid: str,
    ascending: bool,
    limit: int,
    category: str,
) -> list[dict[str, Any]]:
    params = {
        "pn": "1",
        "pz": str(max(10, min(limit, 100))),
        "po": "0" if ascending else "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": fid,
        "fs": fs,
        "fields": PLATE_FIELDS,
    }
    rows: list[dict[str, Any]] = []
    for url in PLATE_CLIST_URLS:
        for attempt in range(2):
            try:
                r = _get(url, params=params, timeout=20)
                r.raise_for_status()
                diff = _iter_clist_diff(r.json().get("data") or {})
                for item in diff:
                    row = _parse_plate_row(item, category=category)
                    if row:
                        rows.append(row)
                if rows:
                    return rows
            except Exception:
                if attempt == 0:
                    time.sleep(0.4)
                continue
    return rows


def fetch_plate_board(
    *,
    category: str = "行业板块",
    board: str = "涨幅榜",
    limit: int = 50,
) -> pd.DataFrame:
    """
    拉取板块列表。
    category: 行业板块 / 概念板块 / 地区板块
    board: 涨幅榜 / 跌幅榜 / 资金流向（按主力净流入降序）
    """
    fs = PLATE_FS.get(category, PLATE_FS["行业板块"])
    fid = "f3"
    ascending = False
    if board == "跌幅榜":
        fid, ascending = "f3", True
    elif board == "资金流向":
        fid, ascending = "f62", False
    elif board == "涨幅榜":
        fid, ascending = "f3", False

    rows = _fetch_plate_rows(
        fs=fs, fid=fid, ascending=ascending, limit=limit, category=category
    )
    empty_cols = [
        "板块名称",
        "板块代码",
        "相关链接",
        "最新价",
        "涨跌额",
        "涨跌幅",
        "主力净流入",
        "领涨股",
        "领涨股涨跌幅",
    ]
    if not rows:
        return pd.DataFrame(columns=empty_cols)
    return pd.DataFrame(rows)


def fetch_flow_board(*, limit: int = 50) -> pd.DataFrame:
    """资金流向：三板块合并，按主力净流入（万元）降序。"""
    frames: list[pd.DataFrame] = []
    for cat in ("行业板块", "概念板块", "地区板块"):
        df = fetch_plate_board(category=cat, board="资金流向", limit=limit)
        if not df.empty:
            frames.append(df)
    if not frames:
        return fetch_plate_board(category="行业板块", board="资金流向", limit=limit)
    out = pd.concat(frames, ignore_index=True)
    if "主力净流入" in out.columns:
        out = out.sort_values("主力净流入", ascending=False, na_position="last")
    return out.head(limit)
