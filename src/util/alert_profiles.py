"""提醒规则模板（P35）：保守 / 均衡 / 激进 阈值预设。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AlertProfile:
    id: str
    label: str
    pct_up: float
    pct_down: float
    score_low: float
    score_high: float


ALERT_PROFILES: tuple[AlertProfile, ...] = (
    AlertProfile("conservative", "保守", 8.0, -8.0, 30.0, 75.0),
    AlertProfile("balanced", "均衡", 5.0, -5.0, 40.0, 65.0),
    AlertProfile("aggressive", "激进", 3.0, -3.0, 50.0, 55.0),
)


def get_alert_profile(profile_id: str) -> AlertProfile | None:
    pid = str(profile_id or "").strip()
    return next((p for p in ALERT_PROFILES if p.id == pid), None)


def alert_profile_thresholds(profile: AlertProfile) -> dict[str, float]:
    return {
        "alert_pct_up": profile.pct_up,
        "alert_pct_down": profile.pct_down,
        "alert_score_low": profile.score_low,
        "alert_score_high": profile.score_high,
    }


def apply_alert_profile(session: Any, profile_id: str) -> AlertProfile | None:
    """将模板阈值写入 session_state（Streamlit 或 dict-like）。"""
    prof = get_alert_profile(profile_id)
    if prof is None:
        return None
    for key, val in alert_profile_thresholds(prof).items():
        session[key] = val
    return prof


def profile_caption(profile: AlertProfile) -> str:
    return (
        f"涨≥{profile.pct_up:g}% · 跌≤{profile.pct_down:g}% · "
        f"低分≤{profile.score_low:g} · 高分≥{profile.score_high:g}"
    )
