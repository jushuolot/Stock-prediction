"""量子基金风格启发层（P128）：宏观先行 · 可证伪论点 · 风险不对称 · 仓位档位。

不是量子基金本身，只借鉴其可落地的决策骨架：
1. 先定大盘体制（进攻/防守/中性），再选股
2. 每只票写清「论点」与「证伪条件」
3. 用涨跌空间不对称过滤（宁可少荐）
4. 用风险预算给仓位档位（非实盘下单）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analysis.daily_picks import DailyPick, SIGNAL_BUY, SIGNAL_WATCH


REGIME_OFFENSE = "进攻"
REGIME_DEFENSE = "防守"
REGIME_NEUTRAL = "中性"


@dataclass(frozen=True)
class MacroRegime:
    label: str
    risk_budget: float  # 0.25–1.0，建议仓位预算
    max_a_picks: int
    max_buy_signals: int
    score_floor_extra: float
    buy_threshold_extra: float
    summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "risk_budget": self.risk_budget,
            "max_a_picks": self.max_a_picks,
            "max_buy_signals": self.max_buy_signals,
            "score_floor_extra": self.score_floor_extra,
            "buy_threshold_extra": self.buy_threshold_extra,
            "summary": self.summary,
        }


def regime_from_outlook(outlook: dict[str, Any] | None) -> MacroRegime:
    """大盘体制：大跌概率 + 2 周看法 → 进攻/防守/中性。"""
    o = outlook or {}
    prob = float(o.get("crash_prob_1_2w_pct") or 0)
    o2w = str(o.get("outlook_2w") or "")
    breadth = o.get("breadth_adv_pct")

    if prob >= 55 or "空" in o2w or "弱" in o2w:
        return MacroRegime(
            label=REGIME_DEFENSE,
            risk_budget=0.30,
            max_a_picks=3,
            max_buy_signals=0,
            score_floor_extra=3.0,
            buy_threshold_extra=4.0,
            summary=f"防守体制：大跌概率 {prob:.0f}% · 少荐、偏观望、轻仓。",
        )
    if prob <= 35 and ("多" in o2w or "强" in o2w or "震荡偏多" in o2w):
        budget = 0.85
        if breadth is not None and float(breadth) >= 55:
            budget = 1.0
        return MacroRegime(
            label=REGIME_OFFENSE,
            risk_budget=budget,
            max_a_picks=5,
            max_buy_signals=3,
            score_floor_extra=0.0,
            buy_threshold_extra=0.0,
            summary=f"进攻体制：大跌概率 {prob:.0f}% · 可集中关注偏多标的。",
        )
    return MacroRegime(
        label=REGIME_NEUTRAL,
        risk_budget=0.55,
        max_a_picks=4,
        max_buy_signals=1,
        score_floor_extra=1.5,
        buy_threshold_extra=2.0,
        summary=f"中性体制：大跌概率 {prob:.0f}% · 精选、严门槛。",
    )


def merge_regime_into_calibration(
    cal: dict[str, Any] | None,
    regime: MacroRegime,
) -> dict[str, Any]:
    """把宏观体制叠进扫盘校准参数。"""
    out = dict(cal or {})
    out["score_floor_delta"] = float(out.get("score_floor_delta") or 0) + regime.score_floor_extra
    out["buy_threshold_delta"] = float(out.get("buy_threshold_delta") or 0) + regime.buy_threshold_extra
    out["pattern"] = dict(out.get("pattern") or {})
    out["macro_regime"] = regime.as_dict()
    return out


def asymmetry_score(
    *,
    pattern: str,
    pct: float | None,
    tech_score: float | None,
) -> float:
    """风险收益不对称粗分：越高越值得下注（仍是规则启发）。"""
    base = 50.0
    if pattern == "强势回踩":
        base += 12
    elif pattern == "突破在即":
        base += 6
    elif pattern == "趋势延续":
        base += 4
    if pct is not None:
        if -3 <= pct <= -0.3:
            base += 8  # 回踩：下行已部分兑现
        elif 0 <= pct <= 4:
            base += 5
        elif pct >= 8:
            base -= 12  # 追高不对称差
    if tech_score is not None:
        base += (tech_score - 60) * 0.25
    return float(max(0.0, min(100.0, base)))


def size_hint(*, regime: MacroRegime, signal: str, asym: float) -> str:
    """仓位档位建议（非下单指令）。"""
    if regime.label == REGIME_DEFENSE:
        return "试探仓（≤总仓 5%）" if signal in (SIGNAL_BUY, "明日偏多") else "观望/不建仓"
    if signal not in (SIGNAL_BUY, "明日偏多", "买入"):
        return "观察仓（≤总仓 5%）"
    if asym >= 70 and regime.risk_budget >= 0.8:
        return "标准仓（总仓 8–12%）"
    if asym >= 55:
        return "轻仓（总仓 5–8%）"
    return "试探仓（≤总仓 5%）"


def build_thesis(
    *,
    name: str,
    pattern: str,
    signal: str,
    regime: MacroRegime,
    one_line: str = "",
) -> tuple[str, str]:
    """论点 + 证伪条件（索罗斯式：先有可被推翻的假设）。"""
    thesis = f"「{name}」在「{regime.label}」体制下，模式「{pattern}」→ {signal}"
    if one_line:
        thesis = f"{thesis}；{one_line[:40]}"
    invalidate = {
        "趋势延续": "跌破 MA20 或放量长阴收阴超 3%",
        "强势回踩": "回踩失守后无反抽 / 再破前低下沿",
        "突破在即": "冲高回落收在平台下沿下方",
    }.get(pattern, "持有期内收盘价相对推荐日跌超 4% 或大盘进入防守体制")
    if regime.label == REGIME_DEFENSE:
        invalidate = "大盘风险未降 + " + invalidate
    return thesis, invalidate


def enrich_pick_dict(
    pick: dict[str, Any],
    regime: MacroRegime,
) -> dict[str, Any]:
    out = dict(pick)
    reason = str(out.get("reason") or "")
    pattern = str(out.get("pattern") or "")
    if not pattern and reason.startswith("[") and "]" in reason:
        pattern = reason[1 : reason.index("]")]
    signal = str(out.get("signal") or "")
    asym = asymmetry_score(pattern=pattern, pct=out.get("pct"), tech_score=out.get("score"))
    thesis, invalidate = build_thesis(
        name=str(out.get("name") or out.get("code") or ""),
        pattern=pattern or "未知",
        signal=signal,
        regime=regime,
        one_line=reason,
    )
    out["pattern"] = pattern or out.get("pattern")
    out["asymmetry"] = round(asym, 1)
    out["size_hint"] = size_hint(regime=regime, signal=signal, asym=asym)
    out["thesis"] = thesis
    out["invalidate"] = invalidate
    out["macro_regime"] = regime.label
    return out


def enrich_daily_picks(
    picks: list[DailyPick],
    regime: MacroRegime,
) -> list[dict[str, Any]]:
    return [enrich_pick_dict(p.as_dict(), regime) for p in picks]


def gate_picks_by_regime(
    picks: list[DailyPick],
    regime: MacroRegime,
) -> list[DailyPick]:
    """宏观闸门：防守时降级买入、压缩数量；进攻时保留头部。"""
    if not picks:
        return []
    work = list(picks)
    # 按分数排序
    work.sort(key=lambda p: float(p.score or 0), reverse=True)

    gated: list[DailyPick] = []
    buy_n = 0
    for p in work:
        if len(gated) >= regime.max_a_picks:
            break
        sig = p.signal
        reason = p.reason
        if sig == SIGNAL_BUY:
            if buy_n >= regime.max_buy_signals:
                sig = SIGNAL_WATCH
                reason = f"[宏观降级] {reason}"
            else:
                buy_n += 1
                reason = f"[宏观{regime.label}] {reason}"
        else:
            reason = f"[宏观{regime.label}] {reason}"
        gated.append(
            DailyPick(
                code=p.code,
                name=p.name,
                score=p.score,
                pct=p.pct,
                signal=sig,
                hold_days=p.hold_days,
                reason=reason,
                price=p.price,
                market=p.market,
                fund_tag=p.fund_tag,
            )
        )
    return gated


def quantum_brief_lines(regime: MacroRegime, picks: list[dict[str, Any]]) -> list[str]:
    lines = [f"**体制** {regime.label} · 风险预算 {regime.risk_budget:.0%} · {regime.summary}"]
    top = [p for p in picks if p.get("thesis")][:2]
    for p in top:
        lines.append(f"**论点** {p.get('name')}：{str(p.get('thesis') or '')[:48]}")
        lines.append(f"**证伪** {p.get('invalidate')}")
    return lines[:5]
