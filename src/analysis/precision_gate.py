"""精准推荐闸门（P129）：宁可少荐，多信号确认才过。

确认维度：
1. 技术明日分达标
2. 质量过滤已过
3. 不对称分（回踩 > 追高）
4. 近绩弱模式（校准权重过低）直接剔除或降级
5. 禁止追高买入（日涨幅过大）
6. 流动性下限（成交额）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analysis.quantum_style import asymmetry_score


@dataclass(frozen=True)
class PrecisionVerdict:
    ok: bool
    allow_buy: bool
    precision_score: float
    reject_reason: str
    tags: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "allow_buy": self.allow_buy,
            "precision_score": self.precision_score,
            "reject_reason": self.reject_reason,
            "tags": list(self.tags),
        }


# 宁可少：买入需更高不对称；观察也要过底线
ASYM_WATCH_MIN = 56.0
ASYM_BUY_MIN = 64.0
CHASE_PCT_BLOCK_BUY = 6.5  # 日涨幅超过则不可「买入」
CHASE_PCT_SKIP = 9.5  # 过高直接不进池
MIN_AMOUNT_YUAN = 8e7  # 约 0.8 亿成交额，过滤过小流动性
WEAK_PATTERN_ADJ = -2.5  # 校准对该模式 ≤ 此值 → 剔除


def evaluate_precision(
    *,
    pattern: str,
    pct: float | None,
    adj_score: float,
    amount: float | None,
    pattern_adj: dict[str, float] | None,
    quality_delta: float,
    want_buy: bool,
) -> PrecisionVerdict:
    tags: list[str] = []
    padj = float((pattern_adj or {}).get(pattern) or 0)

    if pct is not None and pct >= CHASE_PCT_SKIP:
        return PrecisionVerdict(False, False, 0.0, "涨幅过大·追高剔除", ())

    if padj <= WEAK_PATTERN_ADJ:
        return PrecisionVerdict(
            False, False, 0.0, f"模式「{pattern}」近绩偏弱（校准 {padj:+.1f}）", ()
        )

    if amount is not None and amount > 0 and amount < MIN_AMOUNT_YUAN:
        return PrecisionVerdict(False, False, 0.0, "成交额偏低·流动性不足", ())

    asym = asymmetry_score(pattern=pattern, pct=pct, tech_score=adj_score)
    if asym < ASYM_WATCH_MIN:
        return PrecisionVerdict(
            False, False, asym, f"不对称分 {asym:.0f}<{ASYM_WATCH_MIN:.0f}", ()
        )

    # 综合精准分：技术 + 不对称 + 质量 + 校准
    precision = adj_score * 0.45 + asym * 0.40 + min(8.0, max(-4.0, quality_delta)) + padj
    tags.append(f"不对称{asym:.0f}")
    if padj > 0:
        tags.append(f"模式近优{padj:+.1f}")
    if quality_delta >= 2:
        tags.append("质量加分")

    allow_buy = want_buy and asym >= ASYM_BUY_MIN and precision >= 68
    if want_buy and pct is not None and pct >= CHASE_PCT_BLOCK_BUY:
        allow_buy = False
        tags.append("涨幅偏大·禁买")
    if want_buy and padj < 0:
        allow_buy = False
        tags.append("弱模式·禁买")

    if precision < 62:
        return PrecisionVerdict(False, False, precision, f"精准分 {precision:.0f}<62", tuple(tags))

    return PrecisionVerdict(True, allow_buy, round(precision, 1), "", tuple(tags))
