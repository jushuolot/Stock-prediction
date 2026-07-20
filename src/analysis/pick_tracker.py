"""推荐命中率追踪（P104）：记录每日推荐，验证日后是否上涨。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

HOLD_DAYS_DEFAULT = 3


@dataclass(frozen=True)
class PickRecord:
    pick_date: str
    code: str
    name: str
    signal: str
    pick_score: float | None
    pick_pct: float | None
    hold_days: int
    verified: bool
    end_pct: float | None
    hit: bool | None
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "pick_date": self.pick_date,
            "code": self.code,
            "name": self.name,
            "signal": self.signal,
            "pick_score": self.pick_score,
            "pick_pct": self.pick_pct,
            "hold_days": self.hold_days,
            "verified": self.verified,
            "end_pct": self.end_pct,
            "hit": self.hit,
            "note": self.note,
        }


def _parse_hold_days(hold: str) -> int:
    s = (hold or "").strip()
    for part in s.replace("天", " ").replace("–", "-").replace("—", "-").split("-"):
        part = part.strip()
        if part.isdigit():
            return max(1, min(10, int(part)))
    return HOLD_DAYS_DEFAULT


def append_today_picks(
    log: list[dict[str, Any]],
    picks: list[Any],
    *,
    day: str | None = None,
) -> list[dict[str, Any]]:
    """将今日推荐写入 log（同 code 同 day 不重复）。"""
    d = day or date.today().isoformat()
    out = list(log or [])
    existing = {(str(x.get("pick_date")), str(x.get("code"))) for x in out}
    for p in picks:
        code = str(getattr(p, "code", "") or p.get("code", ""))
        if (d, code) in existing:
            continue
        hold = getattr(p, "hold_days", None) or p.get("hold_days", "3")
        reason = str(getattr(p, "reason", "") or p.get("reason", "") or "")
        pattern = str(getattr(p, "pattern", "") or p.get("pattern", "") or "")
        if not pattern and reason:
            m = re.search(r"\[([^\]]+)\]", reason)
            if m:
                pattern = m.group(1).strip()
        out.append(
            {
                "pick_date": d,
                "code": code,
                "name": str(getattr(p, "name", "") or p.get("name", "")),
                "signal": str(getattr(p, "signal", "") or p.get("signal", "")),
                "pick_score": getattr(p, "score", None) if hasattr(p, "score") else p.get("score"),
                "pick_pct": getattr(p, "pct", None) if hasattr(p, "pct") else p.get("pct"),
                "hold_days": _parse_hold_days(str(hold)),
                "pattern": pattern,
                "reason": reason[:200],
                "verified": False,
                "end_pct": None,
                "hit": None,
                "note": "",
            }
        )
    return out[-200:]


def _days_since(pick_date: str, today: date | None = None) -> int:
    ref = today or date.today()
    try:
        d0 = date.fromisoformat(pick_date[:10])
    except ValueError:
        return 0
    return (ref - d0).days


def verify_pick_record(
    rec: dict[str, Any],
    current_pct: float | None,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """到期后用当前涨跌幅验证是否「涨过」（相对推荐日榜单 pct 或绝对为正）。"""
    out = dict(rec)
    if out.get("verified"):
        return out
    hold = int(out.get("hold_days") or HOLD_DAYS_DEFAULT)
    elapsed = _days_since(str(out.get("pick_date") or ""), today=today)
    if elapsed < hold:
        return out
    pick_pct = out.get("pick_pct")
    hit: bool | None = None
    note = ""
    if current_pct is None:
        note = "暂无最新涨跌数据"
    elif pick_pct is not None:
        try:
            hit = float(current_pct) > float(pick_pct)
            note = f"推荐日 {float(pick_pct):+.2f}% → 今 {float(current_pct):+.2f}%"
        except (TypeError, ValueError):
            hit = float(current_pct) > 0
            note = f"今 {float(current_pct):+.2f}%"
    else:
        hit = float(current_pct) > 0
        note = f"今 {float(current_pct):+.2f}%"
    out["verified"] = True
    out["end_pct"] = current_pct
    out["hit"] = hit
    out["note"] = note
    return out


def verify_log(
    log: list[dict[str, Any]] | Any,
    pct_by_code: dict[str, float | None],
    *,
    today: date | None = None,
) -> list[dict[str, Any]]:
    return [
        verify_pick_record(r, pct_by_code.get(str(r.get("code") or "")), today=today)
        for r in normalize_pick_log(log)
    ]


def _coerce_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        if f != f:
            return None
        return f
    except (TypeError, ValueError):
        return None


def _coerce_hold_days(v: Any) -> int:
    if v is None:
        return HOLD_DAYS_DEFAULT
    if isinstance(v, bool):
        return HOLD_DAYS_DEFAULT
    if isinstance(v, int):
        return max(1, min(10, v))
    if isinstance(v, float):
        if v != v:
            return HOLD_DAYS_DEFAULT
        return max(1, min(10, int(v)))
    if isinstance(v, str):
        return _parse_hold_days(v)
    try:
        return max(1, min(10, int(v)))
    except (TypeError, ValueError):
        return HOLD_DAYS_DEFAULT


def normalize_pick_log(raw: Any) -> list[dict[str, Any]]:
    """Session/快照里的 pick_log 可能是脏数据，统一成 dict 列表。"""
    if raw is None:
        return []
    if isinstance(raw, dict):
        if raw.get("code") and raw.get("pick_date"):
            return [dict(raw)]
        return []
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(dict(item))
    return out


def has_due_verifications(log: list[dict[str, Any]] | Any, *, today: date | None = None) -> bool:
    """是否有已到持有期、尚未验证的推荐。"""
    ref = today or date.today()
    for r in normalize_pick_log(log):
        if r.get("verified"):
            continue
        hold = int(r.get("hold_days") or HOLD_DAYS_DEFAULT)
        if _days_since(str(r.get("pick_date") or ""), today=ref) >= hold:
            return True
    return False


def hit_rate_summary(log: list[dict[str, Any]] | Any, *, last_n: int = 20) -> dict[str, Any]:
    verified = [r for r in normalize_pick_log(log) if r.get("verified") and r.get("hit") is not None]
    recent = verified[-last_n:]
    hits = sum(1 for r in recent if r.get("hit"))
    total = len(recent)
    rate = (hits / total * 100.0) if total else None
    return {
        "total_verified": total,
        "hits": hits,
        "rate_pct": round(rate, 1) if rate is not None else None,
        "label": f"最近 {total} 次推荐，{hits} 次按持有期涨过" if total else "尚无到期验证记录",
    }


def records_for_display(log: list[dict[str, Any]] | Any, *, limit: int = 15) -> list[PickRecord]:
    rows: list[PickRecord] = []
    items = normalize_pick_log(log)
    for r in items[-limit:][::-1]:
        hit_raw = r.get("hit")
        hit: bool | None
        if hit_raw is None:
            hit = None
        elif isinstance(hit_raw, bool):
            hit = hit_raw
        else:
            hit = bool(hit_raw)
        rows.append(
            PickRecord(
                pick_date=str(r.get("pick_date") or ""),
                code=str(r.get("code") or ""),
                name=str(r.get("name") or ""),
                signal=str(r.get("signal") or ""),
                pick_score=_coerce_float(r.get("pick_score")),
                pick_pct=_coerce_float(r.get("pick_pct")),
                hold_days=_coerce_hold_days(r.get("hold_days")),
                verified=bool(r.get("verified")),
                end_pct=_coerce_float(r.get("end_pct")),
                hit=hit,
                note=str(r.get("note") or ""),
            )
        )
    return rows
