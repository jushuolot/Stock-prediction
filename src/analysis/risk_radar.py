"""风险雷达（P79）：从快照评分分解或默认值输出 3 条风险旗标。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.analysis.sector_relative import SectorRelativeRow
from src.analysis.signals import ScoreBreakdown
from src.util.freshness_badge import is_stale

_VOL_RISK_THRESHOLD = -8.0
_SCORE_LOW = 40.0
_PCT_VOL_THRESHOLD = 5.0
_PRIORITY = ("波动", "评分偏低", "stale", "跑输板块")


@dataclass(frozen=True)
class RiskFlag:
    kind: str
    message: str
    triggered: bool


def _breakdown_fields(
    score_breakdown: ScoreBreakdown | dict[str, Any] | None,
) -> dict[str, float | None]:
    if score_breakdown is None:
        return {"risk": None, "total": None}
    if isinstance(score_breakdown, ScoreBreakdown):
        return {"risk": score_breakdown.risk, "total": score_breakdown.total}
    out: dict[str, float | None] = {"risk": None, "total": None}
    for key in ("risk", "total"):
        val = score_breakdown.get(key)
        if val is None:
            continue
        try:
            out[key] = float(val)
        except (TypeError, ValueError):
            pass
    return out


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _volatility_flag(
    snap: dict[str, Any],
    breakdown: dict[str, float | None],
) -> RiskFlag:
    risk = breakdown.get("risk")
    if risk is not None and risk <= _VOL_RISK_THRESHOLD:
        return RiskFlag(
            "波动",
            f"波动偏高（风险项扣分 {abs(risk):.0f}，20 日年化波动率较大）",
            True,
        )
    pct = _float_or_none(snap.get("pct"))
    if pct is not None and abs(pct) >= _PCT_VOL_THRESHOLD:
        return RiskFlag(
            "波动",
            f"当日波动较大（{pct:+.2f}%），短线振幅需留意",
            True,
        )
    return RiskFlag("波动", "波动正常，暂无异常放大。", False)


def _score_low_flag(
    snap: dict[str, Any],
    breakdown: dict[str, float | None],
) -> RiskFlag:
    score = _float_or_none(snap.get("score"))
    if score is None:
        score = breakdown.get("total")
    if score is not None and score <= _SCORE_LOW:
        return RiskFlag(
            "评分偏低",
            f"综合评分 {score:.1f} 分偏低（≤{_SCORE_LOW:.0f}），趋势/动量信号偏弱",
            True,
        )
    if score is None:
        return RiskFlag("评分偏低", "暂无评分，请先刷新摘要或一键分析。", False)
    return RiskFlag("评分偏低", f"综合评分 {score:.1f} 分，暂无偏低警示。", False)


def _stale_flag(
    snap: dict[str, Any],
    *,
    stale_hours: float,
    now: datetime | None,
) -> RiskFlag:
    updated = snap.get("updated_at")
    if is_stale(updated, stale_hours=stale_hours, now=now):
        label = str(updated or "未知").strip() or "未知"
        return RiskFlag(
            "stale",
            f"摘要数据过期（上次更新 {label}，超过 {stale_hours:.0f} 小时）",
            True,
        )
    label = str(updated or "—").strip()
    return RiskFlag("stale", f"摘要较新（更新于 {label}）。", False)


def _sector_flag(sector_relative: SectorRelativeRow | None) -> RiskFlag:
    if sector_relative is None:
        return RiskFlag("跑输板块", "暂无板块相对数据，无法判断强弱。", False)
    if sector_relative.label == "跑输板块":
        return RiskFlag(
            "跑输板块",
            sector_relative.fool_conclusion,
            True,
        )
    if sector_relative.label == "跑赢板块":
        return RiskFlag(
            "跑输板块",
            f"相对同板块自选偏强（{sector_relative.fool_conclusion}）",
            False,
        )
    return RiskFlag("跑输板块", sector_relative.fool_conclusion, False)


def compute_risk_radar(
    snap: dict[str, Any] | None,
    *,
    score_breakdown: ScoreBreakdown | dict[str, Any] | None = None,
    sector_relative: SectorRelativeRow | None = None,
    stale_hours: float = 24.0,
    now: datetime | None = None,
) -> list[RiskFlag]:
    """输出 3 条风险旗标（波动/评分偏低/stale/跑输板块），优先展示已触发项。"""
    snap = snap or {}
    breakdown = _breakdown_fields(score_breakdown)
    flags = [
        _volatility_flag(snap, breakdown),
        _score_low_flag(snap, breakdown),
        _stale_flag(snap, stale_hours=stale_hours, now=now),
        _sector_flag(sector_relative),
    ]
    by_kind = {f.kind: f for f in flags}
    ordered = [by_kind[k] for k in _PRIORITY if k in by_kind]
    triggered = [f for f in ordered if f.triggered]
    calm = [f for f in ordered if not f.triggered]
    return (triggered + calm)[:3]


def risk_radar_markdown(flags: list[RiskFlag], *, name: str = "", code: str = "") -> str:
    """Markdown 段落，供 expander 或下载使用。"""
    head = f"**{name}（{code}）**" if name and code else ""
    lines: list[str] = []
    if head:
        lines.extend([head, ""])
    for f in flags:
        icon = "⚠️" if f.triggered else "✅"
        lines.append(f"- {icon} **{f.kind}**：{f.message}")
    return "\n".join(lines)
