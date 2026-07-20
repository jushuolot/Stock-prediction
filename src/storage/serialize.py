"""Session 对象 ↔ JSON 可序列化结构。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.analysis.capital_attribution import CapitalMix, capital_mix_from_dict
from src.analysis.mover_insight import ActionRouteReport
from src.analysis.timeframe_impact import TimeframeSlice


def capital_mix_to_dict(cap: CapitalMix) -> dict[str, Any]:
    return {
        "fund_pct": cap.fund_pct,
        "institution_pct": cap.institution_pct,
        "large_account_pct": cap.large_account_pct,
        "hot_money_pct": cap.hot_money_pct,
        "retail_pct": cap.retail_pct,
        "foreign_pct": cap.foreign_pct,
        "method": cap.method,
        "notes": list(cap.notes),
    }


def timeframe_slice_to_dict(s: TimeframeSlice) -> dict[str, Any]:
    return {
        "label": s.label,
        "available": s.available,
        "price_chg_pct": s.price_chg_pct,
        "volume_chg_pct": s.volume_chg_pct,
        "impact": s.impact,
        "detail": s.detail,
    }


def timeframe_slice_from_dict(d: dict[str, Any]) -> TimeframeSlice:
    return TimeframeSlice(
        label=str(d.get("label") or ""),
        available=bool(d.get("available")),
        price_chg_pct=d.get("price_chg_pct"),
        volume_chg_pct=d.get("volume_chg_pct"),
        impact=str(d.get("impact") or ""),
        detail=str(d.get("detail") or ""),
    )


def panorama_detail_to_dict(d: dict[str, Any]) -> dict[str, Any]:
    cap = d.get("capital")
    if isinstance(cap, CapitalMix):
        cap_d = capital_mix_to_dict(cap)
    elif isinstance(cap, dict):
        cap_d = cap
    else:
        cap_d = {}
    tfs = d.get("timeframes") or []
    tf_out = []
    for t in tfs:
        if isinstance(t, TimeframeSlice):
            tf_out.append(timeframe_slice_to_dict(t))
        elif isinstance(t, dict):
            tf_out.append(t)
    return {
        "code": d.get("code"),
        "name": d.get("name"),
        "market": d.get("market"),
        "kind": d.get("kind"),
        "anomaly_score": d.get("anomaly_score"),
        "capital": cap_d,
        "timeframes": tf_out,
        "context": d.get("context") or {},
        "news": d.get("news") or [],
        "snapshot": d.get("snapshot") or {},
        "mode": d.get("mode", "fast"),
    }


def panorama_detail_from_dict(d: dict[str, Any]) -> dict[str, Any]:
    out = dict(d)
    cap = d.get("capital")
    if isinstance(cap, CapitalMix):
        out["capital"] = cap
    elif isinstance(cap, dict):
        out["capital"] = capital_mix_from_dict(cap)
    else:
        out["capital"] = capital_mix_from_dict(cap)
    tfs = []
    for t in d.get("timeframes") or []:
        if isinstance(t, dict):
            tfs.append(timeframe_slice_from_dict(t))
        else:
            tfs.append(t)
    out["timeframes"] = tfs
    return out


def df_to_records(df: pd.DataFrame | None) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def records_to_df(records: list[dict[str, Any]] | None) -> pd.DataFrame | None:
    if not records:
        return None
    return pd.DataFrame(records)


def route_report_to_dict(rep: ActionRouteReport | dict[str, Any]) -> dict[str, Any]:
    if isinstance(rep, dict):
        return rep
    return ActionRouteReport.to_dict(rep)


def route_report_from_session(val: Any) -> ActionRouteReport | None:
    if val is None:
        return None
    if isinstance(val, ActionRouteReport):
        return val
    if isinstance(val, dict):
        return ActionRouteReport.from_dict(val)
    return None
