"""东财机构持股：公募基金 / QFII 新进、增减持（datacenter RPT_MAIN_ORGHOLD）。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import requests

from src.providers.ticker_util import is_bj_code

_DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_DC_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}

ORG_INST = "00"
ORG_FUND = "01"
ORG_QFII = "02"


@dataclass(frozen=True)
class FundHoldingsSnapshot:
    code: str
    report_date: str
    fund_chg: str
    fund_chg_shares: int | None
    fund_hold_ratio: float | None
    fund_org_count: int | None
    fund_ratio_chg: float | None
    fund_count_chg: int | None
    qfii_chg: str
    qfii_hold_ratio: float | None
    inst_net_chg_shares: int | None
    inst_hold_ratio: float | None
    inst_org_count: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_date": self.report_date,
            "fund_chg": self.fund_chg,
            "fund_chg_shares": self.fund_chg_shares,
            "fund_hold_ratio": self.fund_hold_ratio,
            "fund_org_count": self.fund_org_count,
            "fund_ratio_chg": self.fund_ratio_chg,
            "fund_count_chg": self.fund_count_chg,
            "qfii_chg": self.qfii_chg,
            "qfii_hold_ratio": self.qfii_hold_ratio,
            "inst_net_chg_shares": self.inst_net_chg_shares,
            "inst_hold_ratio": self.inst_hold_ratio,
            "inst_org_count": self.inst_org_count,
        }


def _secucode(code6: str) -> str:
    c = str(code6).strip().zfill(6)
    if c[0] == "6":
        return f"{c}.SH"
    if is_bj_code(c):
        return f"{c}.BJ"
    return f"{c}.SZ"


def _f(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def _i(v: Any) -> int | None:
    f = _f(v)
    return int(f) if f is not None else None


def _norm_chg(raw: Any) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() == "none":
        return "—"
    if "新进" in s:
        return "新进"
    if "增" in s:
        return "增仓"
    if "减" in s:
        return "减仓"
    if "不变" in s:
        return "不变"
    return s


def _pick_org(rows: list[dict[str, Any]], org_type: str) -> dict[str, Any] | None:
    return next((r for r in rows if str(r.get("ORG_TYPE")) == org_type), None)


def _group_by_report(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        d = str(row.get("REPORT_DATE") or "")[:10]
        if d:
            by[d].append(row)
    return by


def fetch_fund_holdings_snapshot(code6: str) -> FundHoldingsSnapshot | None:
    """最新季报：公募基金 / QFII / 机构汇总持股变动。"""
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return None
    try:
        r = requests.get(
            _DC,
            params={
                "reportName": "RPT_MAIN_ORGHOLD",
                "columns": "ALL",
                "pageNumber": 1,
                "pageSize": 120,
                "filter": f'(SECUCODE="{_secucode(c)}")',
                "sortTypes": "-1",
                "sortColumns": "REPORT_DATE",
            },
            headers=_DC_HEADERS,
            timeout=18,
        )
        r.raise_for_status()
        payload = r.json()
        if not payload.get("success"):
            return None
        rows = (payload.get("result") or {}).get("data") or []
    except Exception:
        return None
    if not rows:
        return None

    by_date = _group_by_report(rows)
    dates = sorted(by_date.keys(), reverse=True)
    if not dates:
        return None

    cur_rows = by_date[dates[0]]
    prev_rows = by_date[dates[1]] if len(dates) > 1 else []

    fund = _pick_org(cur_rows, ORG_FUND) or {}
    qfii = _pick_org(cur_rows, ORG_QFII) or {}
    inst = _pick_org(cur_rows, ORG_INST) or {}

    prev_fund = _pick_org(prev_rows, ORG_FUND) or {}
    cur_ratio = _f(fund.get("TOTALSHARES_RATIO"))
    prev_ratio = _f(prev_fund.get("TOTALSHARES_RATIO"))
    ratio_chg = round(cur_ratio - prev_ratio, 3) if cur_ratio is not None and prev_ratio is not None else None

    cur_cnt = _i(fund.get("HOULD_NUM"))
    prev_cnt = _i(prev_fund.get("HOULD_NUM"))
    cnt_chg = (cur_cnt - prev_cnt) if cur_cnt is not None and prev_cnt is not None else None

    return FundHoldingsSnapshot(
        code=c,
        report_date=dates[0],
        fund_chg=_norm_chg(fund.get("HOLDCHA")),
        fund_chg_shares=_i(fund.get("HOLDCHA_NUM")),
        fund_hold_ratio=cur_ratio,
        fund_org_count=cur_cnt,
        fund_ratio_chg=ratio_chg,
        fund_count_chg=cnt_chg,
        qfii_chg=_norm_chg(qfii.get("HOLDCHA")),
        qfii_hold_ratio=_f(qfii.get("TOTALSHARES_RATIO")),
        inst_net_chg_shares=_i(inst.get("HOLDCHA_NUM")),
        inst_hold_ratio=_f(inst.get("TOTALSHARES_RATIO")),
        inst_org_count=_i(inst.get("HOULD_NUM")),
    )
