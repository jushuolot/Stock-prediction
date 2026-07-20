"""东方财富 F10：个股 vs 行业财务对比（IndustryAnalysis + 财报摘要）。"""

from __future__ import annotations

from typing import Any, Optional

from src.providers.eastmoney import EM_HEADERS, _get
from src.providers.ticker_util import is_bj_code

_EMWEB = "https://emweb.securities.eastmoney.com/PC_HSF10"
_PAGE_AJAX = f"{_EMWEB}/IndustryAnalysis/PageAjax"
_SURVEY_AJAX = f"{_EMWEB}/CompanySurvey/PageAjax"
_ZCFZB_AJAX = f"{_EMWEB}/NewFinanceAnalysis/zcfzbAjaxNew"
_LRB_AJAX = f"{_EMWEB}/NewFinanceAnalysis/lrbAjaxNew"

_COLUMNS = (
    "总市值",
    "净资产",
    "净利润",
    "市盈率(动)",
    "市净率",
    "毛利率",
    "净利率",
    "ROE",
)


def _f10_code(code6: str) -> str:
    c = str(code6).strip().zfill(6)
    if c[0] == "6":
        return f"SH{c}"
    if is_bj_code(c):
        return f"BJ{c}"
    return f"SZ{c}"


def _industry_label(em2016: str, csrc: str) -> str:
    em = (em2016 or "").strip()
    if em:
        parts = [p for p in em.split("-") if p]
        if parts:
            return parts[-1]
    csrc = (csrc or "").strip()
    if csrc and "-" in csrc:
        return csrc.split("-")[-1]
    return csrc or "所属行业"


def _num(v: Any) -> Optional[float]:
    if v is None or v == "" or v == "-":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _fmt_money(v: Optional[float]) -> str:
    if v is None:
        return "—"
    av = abs(v)
    sign = "-" if v < 0 else ""
    if av >= 1e8:
        return f"{sign}{av / 1e8:.2f}亿"
    if av >= 1e4:
        return f"{sign}{av / 1e4:.2f}万"
    return f"{sign}{av:.2f}"


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}%"


def _fmt_ratio(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}"


def _find_peer(rows: list[dict], code6: str) -> Optional[dict]:
    c = str(code6).zfill(6)
    for row in rows:
        if str(row.get("CORRE_SECURITY_CODE") or "") == c:
            return row
    return None


def _find_label_row(rows: list[dict], label: str) -> Optional[dict]:
    for row in rows:
        if str(row.get("CORRE_SECURITY_CODE") or row.get("CORRE_SECURITY_NAME") or "") == label:
            return row
    return None


def _industry_total(payload: dict) -> int:
    totals: list[int] = []
    for key in ("gzbj", "dbfxbj", "czxbj"):
        for row in payload.get(key) or []:
            p = row.get("PAIMING")
            if p is not None:
                try:
                    totals.append(int(p))
                except (TypeError, ValueError):
                    pass
    gsgm = (payload.get("gsgm") or [{}])[0]
    for rk in ("TOTAL_CAP_RANK", "NETPROFIT_RANK", "TOTAL_OPERATEINCOME_RANK", "FREECAP_RANK"):
        v = gsgm.get(rk)
        if v is not None:
            try:
                totals.append(int(v))
            except (TypeError, ValueError):
                pass
    return max(totals) if totals else 0


def _quartile(rank: Optional[int], total: int) -> tuple[Optional[int], str]:
    """rank 1 = 行业内最佳 → 高。返回 (0–4 档位, 中文标签)；无排名时 label 为 —。"""
    labels = ("低", "较低", "中等", "较高", "高")
    if not rank or total < 2:
        return None, "—"
    pct = (int(rank) - 1) / (total - 1)
    if pct <= 0.2:
        return 4, labels[4]
    if pct <= 0.4:
        return 3, labels[3]
    if pct <= 0.6:
        return 2, labels[2]
    if pct <= 0.8:
        return 1, labels[1]
    return 0, labels[0]


def _rank_cell(rank: Optional[int], total: int) -> str:
    if not rank or not total:
        return "—"
    return f"{int(rank)}|{int(total)}"


def _gross_margin(code6: str) -> Optional[float]:
    """最近年报毛利率（%）。"""
    try:
        r = _get(
            _LRB_AJAX,
            params={
                "companyType": "4",
                "reportDateType": "0",
                "reportType": "1",
                "dates": "2025-12-31",
                "code": _f10_code(code6),
            },
            timeout=20,
        )
        r.raise_for_status()
        rows = r.json().get("data") or []
        if not rows:
            return None
        row = rows[0]
        oi = _num(row.get("OPERATE_INCOME"))
        oc = _num(row.get("OPERATE_COST"))
        if oi and oi > 0 and oc is not None:
            return (oi - oc) / oi * 100.0
    except Exception:
        pass
    return None


def _parent_equity(code6: str) -> Optional[float]:
    try:
        r = _get(
            _ZCFZB_AJAX,
            params={
                "companyType": "4",
                "reportDateType": "0",
                "reportType": "1",
                "dates": "2025-12-31",
                "code": _f10_code(code6),
            },
            timeout=20,
        )
        r.raise_for_status()
        rows = r.json().get("data") or []
        if not rows:
            return None
        return _num(rows[0].get("TOTAL_PARENT_EQUITY"))
    except Exception:
        return None


def _equity_industry_avg(total_cap: Optional[float], pb: Optional[float]) -> Optional[float]:
    if total_cap and pb and pb > 0:
        return total_cap / pb
    return None


def fetch_industry_compare(code6: str) -> dict[str, Any]:
    """
    拉取 A 股「财务对比」表数据（东财 F10 IndustryAnalysis/PageAjax 等）。
    非 A 股或接口失败时 ok=False。
    """
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return {"ok": False, "reason": "not_a_share"}

    headers = {**EM_HEADERS, "Referer": "https://emweb.securities.eastmoney.com/"}
    f10 = _f10_code(c)
    try:
        r = _get(_PAGE_AJAX, params={"code": f10, "type": "web"}, timeout=25)
        r.raise_for_status()
        payload = r.json()
    except Exception as exc:
        return {"ok": False, "reason": str(exc)}

    gsgm = (payload.get("gsgm") or [{}])[0]
    hypj = _find_label_row(payload.get("gsgm_hypj") or [], "行业平均") or {}
    gzbj_self = _find_peer(payload.get("gzbj") or [], c) or {}
    gzbj_ind = _find_label_row(payload.get("gzbj") or [], "行业平均") or {}
    dbfx_self = _find_peer(payload.get("dbfxbj") or [], c) or {}
    dbfx_ind = _find_label_row(payload.get("dbfxbj") or [], "行业平均") or {}

    name = str(gsgm.get("SECURITY_NAME_ABBR") or gzbj_self.get("CORRE_SECURITY_NAME") or c)
    report_type = str(gsgm.get("REPORT_TYPE") or "")

    try:
        sr = _get(_SURVEY_AJAX, params={"code": f10}, timeout=15)
        sr.raise_for_status()
        jb = (sr.json().get("jbzl") or [{}])[0]
    except Exception:
        jb = {}
    industry = _industry_label(str(jb.get("EM2016") or ""), str(jb.get("INDUSTRYCSRC1") or ""))

    total = _industry_total(payload)
    equity = _parent_equity(c)
    equity_ind = _equity_industry_avg(_num(hypj.get("TOTAL_CAP")), _num(gzbj_ind.get("PB_MRQ") or gzbj_ind.get("PB")))
    gross = _gross_margin(c)

    stock_vals = {
        "总市值": _num(gsgm.get("TOTAL_CAP")),
        "净资产": equity,
        "净利润": _num(gsgm.get("NETPROFIT")),
        "市盈率(动)": _num(gzbj_self.get("PE_TTM")),
        "市净率": _num(gzbj_self.get("PB_MRQ") or gzbj_self.get("PB")),
        "毛利率": gross,
        "净利率": _num(dbfx_self.get("XSJLL_AVG")),
        "ROE": _num(dbfx_self.get("ROE_AVG")),
    }
    ind_vals = {
        "总市值": _num(hypj.get("TOTAL_CAP")),
        "净资产": equity_ind,
        "净利润": _num(hypj.get("NETPROFIT")),
        "市盈率(动)": _num(gzbj_ind.get("PE_TTM")),
        "市净率": _num(gzbj_ind.get("PB_MRQ") or gzbj_ind.get("PB")),
        "毛利率": None,
        "净利率": _num(dbfx_ind.get("XSJLL_AVG")),
        "ROE": _num(dbfx_ind.get("ROE_AVG")),
    }
    ranks = {
        "总市值": gsgm.get("TOTAL_CAP_RANK"),
        "净资产": None,
        "净利润": gsgm.get("NETPROFIT_RANK"),
        "市盈率(动)": gzbj_self.get("PAIMING"),
        "市净率": gzbj_self.get("PAIMING"),
        "毛利率": None,
        "净利率": dbfx_self.get("PAIMING"),
        "ROE": dbfx_self.get("PAIMING"),
    }

    stock_cells: list[str] = []
    ind_cells: list[str] = []
    rank_cells: list[str] = []
    quartile_cells: list[dict[str, Any]] = []

    for col in _COLUMNS:
        sv, iv = stock_vals[col], ind_vals[col]
        rk = ranks[col]
        if col in ("市盈率(动)", "市净率", "毛利率", "净利率", "ROE"):
            stock_cells.append(_fmt_pct(sv) if col in ("毛利率", "净利率", "ROE") else _fmt_ratio(sv))
            ind_cells.append(_fmt_pct(iv) if col in ("毛利率", "净利率", "ROE") else _fmt_ratio(iv))
        else:
            stock_cells.append(_fmt_money(sv))
            ind_cells.append(_fmt_money(iv))
        rank_cells.append(_rank_cell(int(rk) if rk is not None else None, total))
        lvl, lbl = _quartile(int(rk) if rk is not None else None, total)
        quartile_cells.append({"level": lvl, "label": lbl})

    return {
        "ok": True,
        "code": c,
        "name": name,
        "industry": industry,
        "report_type": report_type,
        "columns": list(_COLUMNS),
        "industry_total": total,
        "rows": [
            {"kind": "stock", "label": name, "cells": stock_cells},
            {"kind": "industry_avg", "label": f"{industry} 行业平均", "cells": ind_cells},
            {"kind": "rank", "label": "行业排名", "cells": rank_cells},
            {"kind": "quartile", "label": "四分位属性", "cells": quartile_cells},
        ],
        "source": "东方财富 F10 · IndustryAnalysis/PageAjax",
        "note": "毛利率行业均值为 —（东财该接口未提供）；净资产行业均值按总市值/市净率估算。",
    }
