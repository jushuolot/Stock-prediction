"""推荐 3 日内复盘：对比推荐日表现，反哺选股策略（P119）。"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable

import pandas as pd

from src.analysis.pick_tracker import normalize_pick_log

FetchFn = Callable[..., tuple[pd.DataFrame, str]]

_PATTERN_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class Pick3dReview:
    pick_date: str
    code: str
    name: str
    pattern: str
    pick_close: float | None
    ret_d1_pct: float | None
    ret_d2_pct: float | None
    ret_d3_pct: float | None
    max_ret_3d_pct: float | None
    hit_3d: bool | None
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "pick_date": self.pick_date,
            "code": self.code,
            "name": self.name,
            "pattern": self.pattern,
            "pick_close": self.pick_close,
            "ret_d1_pct": self.ret_d1_pct,
            "ret_d2_pct": self.ret_d2_pct,
            "ret_d3_pct": self.ret_d3_pct,
            "max_ret_3d_pct": self.max_ret_3d_pct,
            "hit_3d": self.hit_3d,
            "note": self.note,
        }


def extract_pattern(reason: str, signal: str = "") -> str:
    m = _PATTERN_RE.search(reason or "")
    if m:
        return m.group(1).strip()
    if "延续" in (reason or ""):
        return "趋势延续"
    if "突破" in (reason or ""):
        return "突破在即"
    if "回踩" in (reason or "") or "反弹" in (reason or ""):
        return "强势回踩"
    return (signal or "未知")[:12]


def _parse_pick_date(s: str) -> date | None:
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _forward_returns_from_kline(df: pd.DataFrame, pick_day: date, *, horizon: int = 3) -> dict[str, float | None]:
    if df is None or df.empty or "收盘" not in df.columns or "日期" not in df.columns:
        return {"d1": None, "d2": None, "d3": None, "max": None, "pick_close": None}
    work = df.copy()
    work["日期"] = pd.to_datetime(work["日期"], errors="coerce")
    work = work.dropna(subset=["日期"]).sort_values("日期")
    if work.empty:
        return {"d1": None, "d2": None, "d3": None, "max": None, "pick_close": None}

    pick_ts = pd.Timestamp(pick_day)
    on_or_before = work[work["日期"].dt.date <= pick_day]
    if on_or_before.empty:
        return {"d1": None, "d2": None, "d3": None, "max": None, "pick_close": None}
    base_idx = on_or_before.index[-1]
    try:
        base_close = float(work.loc[base_idx, "收盘"])
    except (TypeError, ValueError):
        return {"d1": None, "d2": None, "d3": None, "max": None, "pick_close": None}
    if base_close <= 0:
        return {"d1": None, "d2": None, "d3": None, "max": None, "pick_close": None}

    after = work[work.index > base_idx].head(horizon)
    rets: list[float] = []
    out: dict[str, float | None] = {"pick_close": base_close, "d1": None, "d2": None, "d3": None, "max": None}
    for i, (_, row) in enumerate(after.iterrows(), start=1):
        try:
            c = float(row["收盘"])
            r = (c / base_close - 1.0) * 100.0
        except (TypeError, ValueError):
            r = None
        if r is not None:
            rets.append(r)
            out[f"d{i}"] = round(r, 2)
    if rets:
        out["max"] = round(max(rets), 2)
    return out


def review_pick_3d(
    rec: dict[str, Any],
    fetch_fn: FetchFn,
    *,
    today: date | None = None,
    horizon: int = 3,
) -> Pick3dReview | None:
    code = str(rec.get("code") or "").zfill(6)
    pick_date_s = str(rec.get("pick_date") or "")
    pick_day = _parse_pick_date(pick_date_s)
    ref = today or date.today()
    if not code.isdigit() or pick_day is None:
        return None
    elapsed = (ref - pick_day).days
    if elapsed < 1:
        return None

    end = ref + timedelta(days=2)
    start = pick_day - timedelta(days=10)
    item = {"代码": code, "名称": str(rec.get("name") or code), "市场": "A股"}
    try:
        df, _ = fetch_fn(item, start=start, end=end, kline="日线")
    except Exception:
        df = pd.DataFrame()

    fwd = _forward_returns_from_kline(df, pick_day, horizon=horizon)
    max_r = fwd.get("max")
    hit: bool | None = None
    if max_r is not None:
        hit = max_r > 0

    note_parts: list[str] = []
    for k, label in (("d1", "D+1"), ("d2", "D+2"), ("d3", "D+3")):
        v = fwd.get(k)
        if v is not None:
            note_parts.append(f"{label}{v:+.1f}%")
    if not note_parts:
        note_parts.append("K线不足")

    reason = str(rec.get("reason") or rec.get("note") or "")
    pattern = str(rec.get("pattern") or "") or extract_pattern(reason, str(rec.get("signal") or ""))

    return Pick3dReview(
        pick_date=pick_date_s[:10],
        code=code,
        name=str(rec.get("name") or ""),
        pattern=pattern,
        pick_close=fwd.get("pick_close"),
        ret_d1_pct=fwd.get("d1"),
        ret_d2_pct=fwd.get("d2"),
        ret_d3_pct=fwd.get("d3"),
        max_ret_3d_pct=max_r,
        hit_3d=hit,
        note=" · ".join(note_parts),
    )


def review_recent_picks(
    log: list[dict[str, Any]] | Any,
    fetch_fn: FetchFn,
    *,
    today: date | None = None,
    within_days: int = 6,
    limit: int = 20,
) -> list[Pick3dReview]:
    ref = today or date.today()
    items = normalize_pick_log(log)
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in items:
        pd_s = str(r.get("pick_date") or "")[:10]
        d = _parse_pick_date(pd_s)
        if d is None:
            continue
        if (ref - d).days > within_days or (ref - d).days < 1:
            continue
        by_day[pd_s].append(r)

    days_sorted = sorted(by_day.keys(), reverse=True)
    out: list[Pick3dReview] = []
    for day_s in days_sorted:
        for rec in by_day[day_s]:
            rev = review_pick_3d(rec, fetch_fn, today=ref)
            if rev:
                out.append(rev)
            if len(out) >= limit:
                return out
    return out


def strategy_hints_from_reviews(reviews: list[Pick3dReview]) -> list[str]:
    """根据 3 日复盘统计，给出策略优化提示。"""
    if not reviews:
        return ["尚无足够复盘样本（推荐满 1 个交易日后自动对比）。"]

    by_pat: dict[str, list[bool]] = defaultdict(list)
    for r in reviews:
        if r.hit_3d is not None:
            by_pat[r.pattern or "未知"].append(r.hit_3d)

    hints: list[str] = []
    total = sum(len(v) for v in by_pat.values())
    hits = sum(sum(1 for x in v if x) for v in by_pat.values())
    if total:
        hints.append(f"近批推荐 3 日内跑赢率 {hits}/{total}（{hits / total * 100:.0f}%）")

    for pat, arr in sorted(by_pat.items(), key=lambda x: -len(x[1])):
        if len(arr) < 2:
            continue
        rate = sum(1 for x in arr if x) / len(arr)
        hints.append(f"「{pat}」{len(arr)}只 · 3日跑赢 {rate * 100:.0f}%")
        if pat == "趋势延续" and rate < 0.45:
            hints.append("→ 已放宽趋势延续涨幅带（0~8%），减少对微涨的过度偏好")
        if rate < 0.35:
            hints.append(f"→ 「{pat}」近期偏弱，明日扫盘将略降该模式权重")

    return hints[:6]


def pattern_score_adjustments_from_log(log: list[dict[str, Any]] | Any) -> dict[str, float]:
    """用已到期验证记录微调模式权重（扫盘时无额外网络请求）。"""
    by_pat: dict[str, list[bool]] = defaultdict(list)
    for r in normalize_pick_log(log):
        if not r.get("verified") or r.get("hit") is None:
            continue
        pat = str(r.get("pattern") or "") or extract_pattern(
            str(r.get("reason") or ""), str(r.get("signal") or "")
        )
        if pat:
            by_pat[pat].append(bool(r.get("hit")))
    adj: dict[str, float] = {}
    for pat, arr in by_pat.items():
        if len(arr) < 3:
            continue
        rate = sum(1 for x in arr if x) / len(arr)
        if rate >= 0.6:
            adj[pat] = 2.0
        elif rate <= 0.35:
            adj[pat] = -3.0
        elif rate <= 0.45:
            adj[pat] = -1.5
    return adj


def pattern_score_adjustments(reviews: list[Pick3dReview]) -> dict[str, float]:
    """按模式近绩微调技术面加分（供明日扫盘）。"""
    by_pat: dict[str, list[bool]] = defaultdict(list)
    for r in reviews:
        if r.hit_3d is not None and r.pattern:
            by_pat[r.pattern].append(r.hit_3d)
    adj: dict[str, float] = {}
    for pat, arr in by_pat.items():
        if len(arr) < 3:
            continue
        rate = sum(1 for x in arr if x) / len(arr)
        if rate >= 0.6:
            adj[pat] = 2.0
        elif rate <= 0.35:
            adj[pat] = -3.0
        elif rate <= 0.45:
            adj[pat] = -1.5
    return adj
