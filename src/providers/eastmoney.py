from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.providers.ticker_util import a_market_label, is_bj_code, yahoo_ticker_a


EM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json,text/plain,*/*",
}

EM_SUGGEST_URL = "https://searchadapter.eastmoney.com/api/suggest/get"
EM_SUGGEST_TOKEN = "D43BF722C8E33BDC906FB84D85E326E8"

EM_KLINE_URLS = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get",
    "https://80.push2his.eastmoney.com/api/qt/stock/kline/get",
    "https://push2.eastmoney.com/api/qt/stock/kline/get",
)

# 沪深京 A 股列表（东方财富 clist fs）——用于“全市场本地模糊匹配”的可选补充
EM_CLIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
EM_CLIST_FALLBACK = "https://82.push2.eastmoney.com/api/qt/clist/get"
EM_A_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"


_SESSION: Optional[requests.Session] = None


def _session() -> requests.Session:
    global _SESSION
    if _SESSION is not None:
        return _SESSION
    s = requests.Session()
    s.headers.update(EM_HEADERS)
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    ad = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=8)
    s.mount("https://", ad)
    s.mount("http://", ad)
    _SESSION = s
    return s


def _get(url: str, *, params: dict[str, Any], timeout: float = 25) -> requests.Response:
    return _session().get(url, params=params, timeout=timeout)


def _parse_jsonp_payload(text: str) -> Any:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("jQuery") or (t.startswith("(") and t.endswith(");")):
        m = re.search(r"\((\{.*\})\)\s*;?\s*$", t, re.S)
        if m:
            t = m.group(1)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


@dataclass(frozen=True)
class SearchHit:
    code: str
    name: str
    market: str  # 沪市A股 / 深市A股 / 北交所 / 港股 / 美股 / 其他
    kind: str  # A / HK / US / OTHER
    yahoo: str  # 可选


def _code6_market(code6: str) -> str:
    return a_market_label(code6)


def _to_yahoo(code: str) -> str:
    c = (code or "").strip()
    if c.isdigit() and len(c) == 6:
        return yahoo_ticker_a(c)
    if c.isdigit() and len(c) in (4, 5):
        return f"{int(c):04d}.HK"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.\-]*", c):
        return c.upper()
    return ""


def suggest(keyword: str, limit: int = 30) -> list[SearchHit]:
    kw = (keyword or "").strip()
    if not kw:
        return []
    params = {"input": kw, "type": "14", "token": EM_SUGGEST_TOKEN, "count": str(limit)}
    try:
        r = _get(EM_SUGGEST_URL, params=params, timeout=12)
        r.raise_for_status()
        payload = _parse_jsonp_payload(r.text)
    except Exception:
        return []

    raw_list = None
    if isinstance(payload, dict):
        if isinstance(payload.get("Data"), list):
            raw_list = payload["Data"]
        else:
            qct = payload.get("QuotationCodeTable")
            if isinstance(qct, dict) and isinstance(qct.get("Data"), list):
                raw_list = qct["Data"]
    if not raw_list:
        return []

    out: list[SearchHit] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        code = str(item.get("Code") or item.get("code") or "").strip()
        name = str(item.get("Name") or item.get("ShortName") or item.get("name") or "").strip()
        if not code or not name:
            continue
        # 统一 6 位代码
        if code.endswith((".SH", ".SZ", ".BJ", ".HK")):
            code = code.rsplit(".", 1)[0]
        if "." in code and code.replace(".", "").isdigit():
            code = code.split(".")[-1]
        if code.isdigit() and len(code) == 6:
            kind = "A"
            market = _code6_market(code)
        else:
            yh = _to_yahoo(code)
            if yh.endswith(".HK"):
                kind, market = "HK", "港股"
            elif yh and not code.isdigit():
                kind, market = "US", "美股"
            else:
                kind, market = "OTHER", "其他"

        yh = _to_yahoo(code)
        key = (code, name)
        if key in seen:
            continue
        seen.add(key)
        out.append(SearchHit(code=code, name=name, market=market, kind=kind, yahoo=yh))
    return out


# UI 周期名 → 东财 klt（101 日 / 102 周 / 103 月；5/15/30/60 为分钟）
_KLT_MAP: dict[str, int] = {
    "日线": 101,
    "日K": 101,
    "周线": 102,
    "周K": 102,
    "月线": 103,
    "月K": 103,
    "5分钟": 5,
    "5分": 5,
    "15分钟": 15,
    "15分": 15,
    "30分钟": 30,
    "30分": 30,
    "60分钟": 60,
    "60分": 60,
}

KLINE_PERIOD_UI = ("日K", "周K", "月K", "5分钟", "15分钟", "30分钟", "60分钟")


def _klt(kline: str) -> int:
    return _KLT_MAP.get(kline, 101)


def is_intraday_kline(kline: str) -> bool:
    return _klt(kline) in (5, 15, 30, 60)


def _candidate_secids(code6: str) -> list[str]:
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return []
    if c[0] == "6" or c.startswith("688") or c.startswith("689"):
        return [f"1.{c}"]
    if c[0] in ("0", "3"):
        return [f"0.{c}"]
    if is_bj_code(c):
        return [f"0.{c}", f"2.{c}"]
    return [f"0.{c}"]


_HTTP_TIMEOUT = 8.0


def _fetch_kline_lines(code6: str, *, kline: str, start: date, end: date) -> list[str]:
    """多域名 / 多 secid / 复权方式尝试拉 K 线（单次请求超时约 8 秒）。"""
    beg = start.strftime("%Y%m%d")
    ed = (end + timedelta(days=1)).strftime("%Y%m%d")
    last_sec = ""
    last_rc: Any = None

    secids = _candidate_secids(code6)
    bases = list(EM_KLINE_URLS)
    if is_bj_code(code6):
        bases = bases[:2]

    for fqt in ("1", "0"):
        params_base = {
            "ut": "fa5fd1943c7b386f172d6893fb581867",
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": str(_klt(kline)),
            "fqt": fqt,
            "beg": beg,
            "end": ed,
            "lmt": "1000000",
        }
        for secid in secids:
            last_sec = secid
            for base in bases:
                try:
                    r = _get(base, params={**params_base, "secid": secid}, timeout=_HTTP_TIMEOUT)
                    r.raise_for_status()
                    j = r.json()
                    last_rc = j.get("rc")
                    data = j.get("data") or {}
                    kl = data.get("klines")
                    if isinstance(kl, list) and kl:
                        return kl
                except Exception:
                    continue
    raise RuntimeError(
        f"东方财富未返回 K 线：{code6}（secid={last_sec}，rc={last_rc}）。"
        f"将尝试 Yahoo 备用源。"
    )


def fetch_a_kline(code6: str, *, kline: str, start: date, end: date) -> pd.DataFrame:
    """
    东方财富 K 线（优先前复权）；失败时由调用方或本函数兜底 Yahoo。
    列名中文：日期/开盘/收盘/最高/最低/成交量/成交额/振幅/涨跌幅/涨跌额/换手率
    """
    try:
        lines = _fetch_kline_lines(code6, kline=kline, start=start, end=end)
    except RuntimeError as err:
        if is_bj_code(code6):
            raise RuntimeError(
                f"北交所 {code6} 东财 K 线暂不可用（{err}）。"
                "可稍后重试，或在「全球股市」用榜单快照生成简版报告。"
            ) from err
        yh = _to_yahoo(code6)
        if not yh:
            raise
        from src.providers import yahoo

        iv_map = {
            "日线": "1d",
            "日K": "1d",
            "周线": "1wk",
            "周K": "1wk",
            "月线": "1mo",
            "月K": "1mo",
        }
        iv = iv_map.get(kline, "1d")
        df = yahoo.fetch_history(yh, start=start, end=end, interval=iv)
        df["数据来源"] = "Yahoo Finance（东财备用）"
        return df

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
    df["日期"] = pd.to_datetime(df["日期"])
    df["标的代码"] = str(code6).zfill(6)
    df["数据来源"] = "东方财富"
    return df


def _parse_clist_row(item: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    raw_c = item.get("f12")
    if raw_c is None:
        return None
    c = str(raw_c).strip()
    if c.replace(".", "").isdigit() and "." in c:
        c = c.split(".")[-1]
    c = re.sub(r"\.0$", "", c)
    if not c.isdigit():
        return None
    c = c.zfill(6)[:6]
    name = str(item.get("f14") or "").strip()
    if len(c) != 6 or not name:
        return None

    def _f(key: str) -> float | None:
        v = item.get(key)
        if v is None or v == "-":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return {
        "代码": c,
        "名称": name,
        "市场": _code6_market(c),
        "类型": "A",
        "最新价": _f("f2"),
        "涨跌幅%": _f("f3"),
        "涨跌额": _f("f5"),
        "成交量": _f("f6"),
        "成交额": _f("f62"),
        "振幅%": _f("f15"),
        "换手率%": _f("f8"),
        "Yahoo代码": _to_yahoo(c),
    }


def fetch_a_ranking(
    *,
    board: str = "涨幅榜",
    limit: int = 50,
) -> pd.DataFrame:
    """
    A 股实时榜单（东方财富 clist，盘中准实时）。
    board: 涨幅榜 / 跌幅榜 / 成交额榜 / 换手率榜
    """
    fid = "f3"
    ascending = False
    if board == "跌幅榜":
        fid, ascending = "f3", True
    elif board == "成交额榜":
        fid, ascending = "f62", False
    elif board == "换手率榜":
        fid, ascending = "f8", False
    elif board == "涨幅榜":
        fid, ascending = "f3", False

    params = {
        "pn": "1",
        "pz": str(limit),
        "po": "0" if ascending else "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": fid,
        "fs": EM_A_FS,
        "fields": "f12,f14,f2,f3,f5,f6,f8,f15,f62",
    }
    rows: list[dict[str, Any]] = []
    for url in (EM_CLIST_URL, EM_CLIST_FALLBACK):
        try:
            r = _get(url, params=params, timeout=25)
            r.raise_for_status()
            j = r.json()
            diff = (j.get("data") or {}).get("diff") or []
            for item in diff:
                row = _parse_clist_row(item)
                if row:
                    rows.append(row)
            if rows:
                break
        except Exception:
            continue
    if not rows:
        return pd.DataFrame(
            columns=["代码", "名称", "市场", "最新价", "涨跌幅%", "涨跌额", "成交量", "成交额", "振幅%", "换手率%", "Yahoo代码"]
        )
    return pd.DataFrame(rows)


def fetch_company_profile_stub(hit: SearchHit) -> dict[str, Any]:
    """
    公开信息的“基础介绍”占位实现：
    - 当前先返回代码/名称/市场等结构；后续可补：行业、概念、主营等（同样可从东财接口扩展）。
    """
    return {
        "名称": hit.name,
        "代码": hit.code,
        "市场": hit.market,
        "类型": hit.kind,
        "Yahoo代码": hit.yahoo,
    }

