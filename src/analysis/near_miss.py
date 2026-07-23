"""近失榜（P130）：精准闸门拒掉后留下「差一点」的票，空仓也可解释。

主线：快照 → 精选 → K线 → 闸门 → **近失可追溯** → 校准
不把近失升为推荐，只作透明度与次日关注线索。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


NEAR_MISS_LIMIT = 8
# 分数略低于门槛时仍记入近失（便于解释「扫到了但未过线」）
LOW_SCORE_NEAR_BAND = 5.0


@dataclass(frozen=True)
class NearMiss:
    code: str
    name: str
    stage: str  # precision | quality | low_score
    reason: str
    score: float | None = None
    precision_score: float | None = None
    pattern: str = ""
    pct: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "stage": self.stage,
            "reason": self.reason,
            "score": self.score,
            "precision_score": self.precision_score,
            "pattern": self.pattern,
            "pct": self.pct,
        }

    @property
    def rank_key(self) -> float:
        """越接近过关越高。"""
        if self.precision_score is not None:
            return float(self.precision_score)
        if self.score is not None:
            return float(self.score) * 0.85
        return 0.0


def rank_near_misses(
    items: list[NearMiss] | list[dict[str, Any]],
    *,
    limit: int = NEAR_MISS_LIMIT,
) -> list[dict[str, Any]]:
    """按接近度排序，同代码去重保留最高分。"""
    best: dict[str, NearMiss] = {}
    for raw in items:
        m = raw if isinstance(raw, NearMiss) else _from_dict(raw)
        if not m or not m.code:
            continue
        prev = best.get(m.code)
        if prev is None or m.rank_key > prev.rank_key:
            best[m.code] = m
    ordered = sorted(best.values(), key=lambda x: -x.rank_key)
    return [m.as_dict() for m in ordered[:limit]]


def _from_dict(d: dict[str, Any]) -> NearMiss | None:
    code = str(d.get("code") or "").zfill(6)
    if len(code) != 6 or not code.isdigit():
        return None
    return NearMiss(
        code=code,
        name=str(d.get("name") or code),
        stage=str(d.get("stage") or "precision"),
        reason=str(d.get("reason") or "")[:80],
        score=_f(d.get("score")),
        precision_score=_f(d.get("precision_score")),
        pattern=str(d.get("pattern") or ""),
        pct=_f(d.get("pct")),
    )


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def summarize_near_misses(rows: list[dict[str, Any]] | None) -> str:
    """一句话：给佛祖简报 / 花园 caption。"""
    if not rows:
        return ""
    top = rows[0]
    name = top.get("name") or top.get("code")
    reason = str(top.get("reason") or "")[:28]
    n = len(rows)
    if n == 1:
        return f"近失 1 只：{name}（{reason}）"
    return f"近失 {n} 只，最近：{name}（{reason}）"


def stage_label(stage: str) -> str:
    return {
        "precision": "精准闸门",
        "quality": "质量过滤",
        "low_score": "分数略低",
    }.get(stage, stage or "—")
