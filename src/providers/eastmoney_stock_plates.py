"""东方财富 · 个股所属板块与板块成份股。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.providers.eastmoney import EM_CLIST_FALLBACK, EM_CLIST_URL, _candidate_secids, _get
from src.providers.eastmoney_plates import _plate_link
from src.providers.ticker_util import a_market_label

EM_SLIST_URL = "https://push2.eastmoney.com/api/qt/slist/get"
EM_SLIST_FALLBACK = "https://80.push2.eastmoney.com/api/qt/slist/get"

EM_CONSTITUENT_URLS = (
    "https://80.push2.eastmoney.com/api/qt/clist/get",
    "https://push2delay.eastmoney.com/api/qt/clist/get",
    EM_CLIST_URL,
    EM_CLIST_FALLBACK,
)

_UT = "bd1d9ddb04089700cf9c27f6f7426281"


def _float(v: Any) -> float | None:
    if v is None or v == "-":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _norm_bk(code: str) -> str:
    c = str(code or "").strip().upper()
    if not c:
        return ""
    if not c.startswith("BK"):
        c = f"BK{c}" if c.isdigit() else c
    return c


def _parse_belong_row(item: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    bk = _norm_bk(str(item.get("f12") or ""))
    name = str(item.get("f14") or "").strip()
    if not bk or not name:
        return None
    lead = str(item.get("f128") or "").strip() or "—"
    lead_pct = _float(item.get("f136"))
    lead_suffix = f" {lead_pct:+.2f}%" if lead_pct is not None else ""
    return {
        "名称": name,
        "涨跌幅%": _float(item.get("f3")),
        "领涨股": f"{lead}{lead_suffix}",
        "板块代码": bk,
        "相关链接": _plate_link(bk),
    }


def fetch_stock_belong_plates(code: str, *, limit: int = 80) -> pd.DataFrame:
    """个股所属板块（行业/概念/地域等），东财 slist spt=3。"""
    code6 = str(code or "").strip()
    if code6.isdigit() and len(code6) <= 6:
        code6 = code6.zfill(6)
    secids = _candidate_secids(code6) if code6.isdigit() and len(code6) == 6 else []
    if not secids:
        return pd.DataFrame(columns=["名称", "涨跌幅%", "领涨股", "板块代码", "相关链接"])

    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f12,f14,f3,f128,f136,f140",
        "spt": "3",
        "np": "1",
        "ut": _UT,
        "pn": "1",
        "pz": str(max(10, min(limit, 100))),
    }
    rows: list[dict[str, Any]] = []
    for secid in secids:
        params["secid"] = secid
        for url in (EM_SLIST_URL, EM_SLIST_FALLBACK):
            try:
                r = _get(url, params=params, timeout=15)
                r.raise_for_status()
                diff = (r.json().get("data") or {}).get("diff") or []
                for item in diff:
                    row = _parse_belong_row(item)
                    if row:
                        rows.append(row)
                if rows:
                    break
            except Exception:
                continue
        if rows:
            break

    if not rows:
        return pd.DataFrame(columns=["名称", "涨跌幅%", "领涨股", "板块代码", "相关链接"])
    df = pd.DataFrame(rows)
    if "涨跌幅%" in df.columns:
        df = df.sort_values("涨跌幅%", ascending=False, na_position="last")
    return df.head(limit)


def fetch_plate_constituents(
    bk_code: str,
    *,
    sort: str = "pct",
    limit: int = 40,
) -> pd.DataFrame:
    """
    板块成份股。
    sort: pct（涨跌幅）/ amount（成交额）
    """
    bk = _norm_bk(bk_code)
    if not bk:
        return pd.DataFrame(columns=["名称", "最新价", "涨跌幅%", "代码", "市场"])

    fid = "f3" if sort != "amount" else "f6"
    params = {
        "pn": "1",
        "pz": str(max(5, min(limit, 100))),
        "po": "0",
        "np": "1",
        "ut": _UT,
        "fltt": "2",
        "invt": "2",
        "fid": fid,
        "fs": f"b:{bk}",
        "fields": "f12,f14,f2,f3",
    }
    rows: list[dict[str, Any]] = []
    for url in EM_CONSTITUENT_URLS:
        try:
            r = _get(url, params=params, timeout=15)
            r.raise_for_status()
            diff = (r.json().get("data") or {}).get("diff") or []
            for item in diff:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("f12") or "").strip()
                name = str(item.get("f14") or "").strip()
                if not code or not name:
                    continue
                if code.isdigit() and len(code) <= 6:
                    code = code.zfill(6)
                rows.append(
                    {
                        "名称": name,
                        "最新价": _float(item.get("f2")),
                        "涨跌幅%": _float(item.get("f3")),
                        "代码": code,
                        "市场": a_market_label(code) if code.isdigit() and len(code) == 6 else "",
                    }
                )
            if rows:
                break
        except Exception:
            continue

    if not rows:
        return pd.DataFrame(columns=["名称", "最新价", "涨跌幅%", "代码", "市场"])
    return pd.DataFrame(rows)
