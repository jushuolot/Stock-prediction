"""明日 A 股/全球预测（P110）：今日收盘 + 历史 K 线 → 明日偏强名单。

不是「今天涨最多的」，而是找：
- 趋势延续（多头 + 今日温和放量）
- 强势回踩（趋势里小幅回调）
- 突破在即（近 20 日高位 + 量能配合）
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from datetime import date, timedelta
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.analysis.daily_picks import (
    SIGNAL_BUY,
    SIGNAL_SKIP,
    SIGNAL_WATCH,
    DailyPick,
    _is_st_name,
    _row_to_item,
    picks_to_markdown,
    rank_global_from_ranking,
)
from src.analysis.signals import add_indicators, score_stock
from src.analysis.pick_review import pattern_score_adjustments_from_log
from src.analysis.near_miss import (
    LOW_SCORE_NEAR_BAND,
    NearMiss,
    rank_near_misses,
    summarize_near_misses,
)
from src.analysis.precision_gate import evaluate_precision
from src.analysis.stock_quality import QualityVerdict, evaluate_stock_quality

FetchFn = Callable[..., tuple[pd.DataFrame, str]]

PATTERN_CONTINUATION = "趋势延续"
PATTERN_PULLBACK = "强势回踩"
PATTERN_BREAKOUT = "突破在即"
PATTERN_GLOBAL = "全球动量"

SIGNAL_TOMORROW_BUY = "明日偏多"
SIGNAL_TOMORROW_WATCH = "明日观望"

# P120：创业板/科创板明日偏多门槛更严
_GROWTH_PREFIXES = ("300", "301", "688")


@dataclass(frozen=True)
class TomorrowAnalysis:
    tomorrow_score: float
    pattern: str
    signal: str
    hold_days: str
    reason: str
    today_pct: float | None
    tech_score: float | None


def tomorrow_trading_date(*, from_day: date | None = None) -> str:
    """下一个 A 股交易日（简版：跳过周六日）。"""
    d = from_day or date.today()
    nxt = d + timedelta(days=1)
    while nxt.weekday() >= 5:
        nxt += timedelta(days=1)
    return nxt.isoformat()


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def _vol_ratio(df: pd.DataFrame) -> float | None:
    if df is None or df.empty or "成交量" not in df.columns:
        return None
    vol = pd.to_numeric(df["成交量"], errors="coerce")
    if len(vol) < 21:
        return None
    last_v = float(vol.iloc[-1])
    avg = float(vol.tail(21).iloc[:-1].mean())
    if avg <= 0:
        return None
    return last_v / avg


def _near_high_ratio(df: pd.DataFrame, window: int = 20) -> float | None:
    if df is None or len(df) < window:
        return None
    close = pd.to_numeric(df["收盘"], errors="coerce")
    hi = float(close.tail(window).max())
    last = float(close.iloc[-1])
    if hi <= 0:
        return None
    return last / hi


def analyze_tomorrow_from_kline(
    df: pd.DataFrame,
    *,
    today_pct: float | None = None,
    turnover_pct: float | None = None,
    pattern_adj: dict[str, float] | None = None,
) -> TomorrowAnalysis | None:
    """用历史 K 线 + 今日涨跌，估算明日偏强概率（规则可解释）。"""
    if df is None or len(df) < 25:
        return None

    work = add_indicators(df)
    last = work.iloc[-1]
    close = _f(last.get("收盘"))
    ma20 = _f(last.get("MA20"))
    ma60 = _f(last.get("MA60"))
    mom5 = _f(work["收盘"].pct_change(5).iloc[-1])
    mom20 = _f(last.get("动量20"))
    if close is None:
        return None

    try:
        breakdown = score_stock(df)
        tech = breakdown.total
    except Exception:
        tech = None

    pct = today_pct
    if pct is None and len(work) >= 2:
        pct = _f(work["收盘"].pct_change().iloc[-1])
        if pct is not None:
            pct *= 100.0

    vol_r = _vol_ratio(work)
    near_hi = _near_high_ratio(work, 20)

    score = 42.0
    pattern = PATTERN_CONTINUATION
    tags: list[str] = []

    uptrend = (
        ma20 is not None
        and ma60 is not None
        and close > ma20 > ma60
    )
    above_ma20 = ma20 is not None and close > ma20

    if uptrend:
        score += 18
        tags.append("均线多头")
    elif above_ma20:
        score += 10
        tags.append("站上MA20")

    if pct is not None:
        # P119：放宽趋势延续涨幅带 0~8%（原 0.5~5.5% 过窄，易偏向微涨小盘）
        if 0 <= pct <= 8.0:
            if 1.0 <= pct <= 6.0:
                score += 16
            elif pct < 1.0:
                score += 11
            else:
                score += 13
            tags.append("趋势动能")
            pattern = PATTERN_CONTINUATION
        elif -3.0 <= pct <= -0.3 and above_ma20:
            score += 16
            tags.append("趋势内回踩")
            pattern = PATTERN_PULLBACK
        elif pct >= 9.5:
            score -= 22
            tags.append("今日已涨停/过热")
        elif pct <= -4:
            score -= 15
            tags.append("今日弱势")
        elif 8.0 < pct < 9.5:
            score += 5
            tags.append("涨幅偏大")

    if vol_r is not None:
        if vol_r >= 1.35:
            score += 12
            tags.append("放量")
            if near_hi is not None and near_hi >= 0.98:
                pattern = PATTERN_BREAKOUT
                score += 4
                tags.append("近20日高位")
            elif near_hi is not None and near_hi >= 0.96:
                tags.append("近高位")
        elif vol_r >= 1.05:
            score += 5
        elif vol_r < 0.65:
            score -= 4

    if mom5 is not None and mom5 > 0.02:
        score += 6
        tags.append("5日动量正")
    if mom20 is not None and mom20 > 0.05:
        score += 5

    if turnover_pct is not None and turnover_pct >= 3:
        score += min(5.0, turnover_pct * 0.5)

    if tech is not None:
        score += (tech - 50) * 0.22

    if pattern_adj and pattern in pattern_adj:
        score += pattern_adj[pattern]

    tags = list(dict.fromkeys(tags))
    if pattern == PATTERN_BREAKOUT:
        score = min(score, 82.0)

    score = float(np.clip(score, 0, 86))

    buy_th = 80 if pattern == PATTERN_BREAKOUT else (78 if pattern == PATTERN_PULLBACK else 77)
    if score >= buy_th and pattern in (PATTERN_CONTINUATION, PATTERN_BREAKOUT, PATTERN_PULLBACK):
        signal = SIGNAL_TOMORROW_BUY
        hold = "1–3天"
    elif score >= 62:
        signal = SIGNAL_TOMORROW_WATCH
        hold = "1–2天"
    else:
        return None

    if pattern == PATTERN_PULLBACK:
        reason = f"明日看反弹：{'、'.join(tags[:4])}"
    elif pattern == PATTERN_BREAKOUT:
        reason = f"明日看突破：{'、'.join(tags[:4])}"
    else:
        reason = f"明日看延续：{'、'.join(tags[:4])}"

    return TomorrowAnalysis(
        tomorrow_score=round(score, 1),
        pattern=pattern,
        signal=signal,
        hold_days=hold,
        reason=reason,
        today_pct=pct,
        tech_score=round(tech, 1) if tech is not None else None,
    )


def _fund_tag_from_quality(qv: QualityVerdict) -> str | None:
    bits = [t for t in qv.tags if any(k in t for k in ("基金", "QFII", "机构"))]
    if not bits:
        return None
    return "、".join(bits[:3])


def _a_buy_threshold(code: str, adj: float, qv: QualityVerdict, *, extra: float = 0) -> bool:
    """P120：成长板明日偏多需更高综合分与质量加分。"""
    c = str(code).zfill(6)
    delta = qv.score_delta
    if c.startswith("301"):
        return adj >= 82 + extra and delta >= 1.0
    if c.startswith(_GROWTH_PREFIXES):
        return adj >= 80 + extra and delta >= 0.0
    return adj >= 74 + extra


def _merge_ranking_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for df in frames:
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            code = str(row.get("代码") or "").replace(".0", "").strip()
            if not code or code in seen:
                continue
            if len(code) == 6 and code.isdigit():
                seen.add(code)
                rows.append(row.to_dict())
    return pd.DataFrame(rows)


def build_a_universe(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]],
) -> tuple[pd.DataFrame, str]:
    """多榜单合并：涨幅 + 换手 + 成交额，避免只看今日冠军。"""
    from src.providers import market_data

    df1, src1 = fetch_ranking()
    df2, src2 = market_data.fetch_a_ranking_multi(board="换手率榜", limit=50)
    df3, src3 = market_data.fetch_a_ranking_multi(board="成交额榜", limit=50)
    merged = _merge_ranking_frames([df1, df2, df3])
    src = f"{src1} + 换手/成交额"
    return merged, src


def rank_tomorrow_a_picks(
    universe: pd.DataFrame,
    fetch_fn: FetchFn,
    *,
    max_scan: int = 28,
    max_picks: int = 5,
    pick_log: list[dict[str, Any]] | None = None,
    calibration: dict[str, Any] | None = None,
) -> tuple[list[DailyPick], dict[str, Any]]:
    stats: dict[str, Any] = {
        "scanned": 0,
        "skipped_st": 0,
        "skipped_pct": 0,
        "no_kline": 0,
        "low_score": 0,
        "errors": 0,
        "skipped_quality": 0,
        "skipped_precision": 0,
        "mode": "tomorrow_predict_precision",
        "near_misses": [],
    }
    if universe is None or universe.empty:
        return [], stats

    target = tomorrow_trading_date()
    work = universe.copy()
    pattern_adj = pattern_score_adjustments_from_log(pick_log or [])
    cal = calibration or {}
    for k, v in (cal.get("pattern") or {}).items():
        pattern_adj[str(k)] = pattern_adj.get(str(k), 0.0) + float(v)
    score_floor = float(cal.get("score_floor_delta") or 0)
    buy_delta = float(cal.get("buy_threshold_delta") or 0)
    near_raw: list[NearMiss] = []

    def _sort_key(row: pd.Series) -> float:
        pct = _f(row.get("涨跌幅%"))
        turn = _f(row.get("换手率%"))
        amt = _f(row.get("成交额"))
        # 优先：趋势动能 + 成交额（减少小盘微涨霸榜）
        if pct is None:
            base = 0.0
        elif 0 <= pct <= 8:
            base = 11 - abs(pct - 3.0) * 0.8
        elif -3 <= pct <= 0:
            base = 6 - abs(pct + 1.5)
        elif pct > 9:
            base = -5
        else:
            base = 2
        amt_bonus = 0.0
        if amt is not None and amt > 0:
            amt_bonus = min(4.0, math.log10(max(amt, 1)) * 0.35)
        return base + (turn or 0) * 0.12 + amt_bonus

    work["_prio"] = work.apply(_sort_key, axis=1)
    work = work.sort_values("_prio", ascending=False)

    candidates: list[tuple[dict[str, Any], float | None, float | None, float | None]] = []
    for _, row in work.iterrows():
        if len(candidates) >= max_scan:
            break
        item = _row_to_item(row)
        if _is_st_name(item["名称"]):
            stats["skipped_st"] += 1
            continue
        code = item["代码"]
        if len(code) != 6 or not code.isdigit():
            continue
        pct = _f(row.get("涨跌幅%"))
        if pct is not None and (pct < -5 or pct > 19.9):
            stats["skipped_pct"] += 1
            continue
        turn = _f(row.get("换手率%"))
        amt = _f(row.get("成交额"))
        candidates.append((item, pct, turn, amt))

    scored: list[tuple[DailyPick, float]] = []
    end = date.today()
    start = end - timedelta(days=120)

    for item, list_pct, turn, amt in candidates:
        stats["scanned"] += 1
        try:
            df, _ = fetch_fn(item, start=start, end=end, kline="日线")
        except Exception:
            stats["errors"] += 1
            continue
        if df is None or df.empty:
            stats["no_kline"] += 1
            continue

        ta = analyze_tomorrow_from_kline(
            df, today_pct=list_pct, turnover_pct=turn, pattern_adj=pattern_adj
        )
        if ta is None:
            stats["low_score"] += 1
            continue

        price = _f(df["收盘"].iloc[-1]) if "收盘" in df.columns else None
        qv = evaluate_stock_quality(item["代码"])
        if not qv.ok:
            stats["skipped_quality"] = int(stats.get("skipped_quality") or 0) + 1
            near_raw.append(
                NearMiss(
                    code=item["代码"],
                    name=item["名称"],
                    stage="quality",
                    reason=(qv.reject_reason or "质量未过")[:72],
                    score=round(float(ta.tomorrow_score), 1),
                    pattern=ta.pattern,
                    pct=list_pct,
                )
            )
            continue
        adj = float(np.clip(ta.tomorrow_score + qv.score_delta, 0, 88))
        min_score = 64.0 + score_floor  # P129：底线抬高
        if adj < min_score:
            stats["low_score"] += 1
            if adj >= min_score - LOW_SCORE_NEAR_BAND:
                near_raw.append(
                    NearMiss(
                        code=item["代码"],
                        name=item["名称"],
                        stage="low_score",
                        reason=f"明日分 {adj:.0f}<{min_score:.0f}",
                        score=round(adj, 1),
                        pattern=ta.pattern,
                        pct=list_pct,
                    )
                )
            continue
        want_buy = ta.signal == SIGNAL_TOMORROW_BUY and _a_buy_threshold(
            item["代码"], adj, qv, extra=buy_delta
        )
        pv = evaluate_precision(
            pattern=ta.pattern,
            pct=list_pct,
            adj_score=adj,
            amount=amt,
            pattern_adj=pattern_adj,
            quality_delta=float(qv.score_delta),
            want_buy=want_buy,
        )
        if not pv.ok:
            stats["skipped_precision"] = int(stats.get("skipped_precision") or 0) + 1
            near_raw.append(
                NearMiss(
                    code=item["代码"],
                    name=item["名称"],
                    stage="precision",
                    reason=(pv.reject_reason or "精准闸门未过")[:72],
                    score=round(adj, 1),
                    precision_score=float(pv.precision_score),
                    pattern=ta.pattern,
                    pct=list_pct,
                )
            )
            continue
        sig = SIGNAL_BUY if pv.allow_buy else SIGNAL_WATCH
        tag_s = (" · " + "、".join(pv.tags[:3])) if pv.tags else ""
        reason = f"[{ta.pattern}] {ta.reason}{qv.reason_suffix()} · 精准{pv.precision_score:.0f}{tag_s}"
        pick = DailyPick(
            code=item["代码"],
            name=item["名称"],
            score=round(adj, 1),
            pct=list_pct,
            signal=sig,
            hold_days=ta.hold_days,
            reason=reason,
            price=price,
            market="A股",
            fund_tag=_fund_tag_from_quality(qv),
        )
        # 排序键：精准分优先，其次技术分
        scored.append((pick, float(pv.precision_score) * 1.2 + adj * 0.3, item["代码"][:3]))

    scored.sort(key=lambda x: -x[1])
    picks: list[DailyPick] = []
    prefix_count: dict[str, int] = {}
    buy_count = 0
    for pick, _rank, prefix in scored:
        cap = 1 if prefix == "301" else 2
        if prefix_count.get(prefix, 0) >= cap:
            continue
        # P129：买入信号全局最多 2 只，提高集中度
        if pick.signal == SIGNAL_BUY:
            if buy_count >= 2:
                pick = DailyPick(
                    code=pick.code,
                    name=pick.name,
                    score=pick.score,
                    pct=pick.pct,
                    signal=SIGNAL_WATCH,
                    hold_days=pick.hold_days,
                    reason=f"[精准限流] {pick.reason}",
                    price=pick.price,
                    market=pick.market,
                    fund_tag=pick.fund_tag,
                )
            else:
                buy_count += 1
        picks.append(pick)
        prefix_count[prefix] = prefix_count.get(prefix, 0) + 1
        if len(picks) >= max_picks:
            break

    # P129：取消轻量兜底荐股（宁可空，不滥竽）
    if not picks:
        stats["empty_precision"] = True

    near_rows = rank_near_misses(near_raw)
    stats["near_misses"] = near_rows
    stats["near_miss_summary"] = summarize_near_misses(near_rows)
    stats["target_date"] = target
    stats["buy_signals"] = buy_count
    return picks, stats


def fetch_tomorrow_a_picks(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]],
    fetch_fn: FetchFn,
    *,
    max_picks: int = 5,
    pick_log: list[dict[str, Any]] | None = None,
    calibration: dict[str, Any] | None = None,
    universe_override: pd.DataFrame | None = None,
) -> tuple[list[DailyPick], str, dict[str, Any]]:
    if universe_override is not None and not universe_override.empty:
        universe, src = universe_override, "快照精选池"
    else:
        universe, src = build_a_universe(fetch_ranking)
    picks, stats = rank_tomorrow_a_picks(
        universe,
        fetch_fn,
        max_scan=30,
        max_picks=max_picks,
        pick_log=pick_log,
        calibration=calibration,
    )
    stats["source"] = src
    stats["market"] = "A股"
    return picks, src, stats


def rank_tomorrow_global(
    ranking_df: pd.DataFrame,
    *,
    market_label: str = "港股",
    max_picks: int = 2,
) -> tuple[list[DailyPick], dict[str, Any]]:
    """全球：沿用异动分，文案改为明日视角。"""
    picks, stats = rank_global_from_ranking(
        ranking_df,
        market_label=market_label,
        max_picks=max_picks,
    )
    out: list[DailyPick] = []
    for p in picks:
        sig = p.signal
        if sig == SIGNAL_BUY:
            sig = SIGNAL_WATCH
        out.append(
            DailyPick(
                code=p.code,
                name=p.name,
                score=p.score,
                pct=p.pct,
                signal=sig,
                hold_days="1–3天",
                reason=f"[{PATTERN_GLOBAL}] 明日全球视角：{p.reason[:50]}",
                price=p.price,
                market=p.market,
            )
        )
    stats["mode"] = "tomorrow_global"
    return out, stats


def fetch_tomorrow_global_picks(
    *,
    max_per_market: int = 2,
) -> tuple[list[DailyPick], dict[str, Any]]:
    from src.providers import market_data

    all_picks: list[DailyPick] = []
    gstats: dict[str, Any] = {"hk": 0, "us": 0}
    for label in ("港股", "美股"):
        df, src = market_data.fetch_global_ranking_multi(market=label, board="涨幅榜", limit=35)
        part, st = rank_tomorrow_global(df, market_label=label, max_picks=max_per_market)
        all_picks.extend(part)
        gstats["us" if label == "美股" else "hk"] = len(part)
        gstats[f"source_{label}"] = src
    gstats["total"] = len(all_picks)
    gstats["target_date"] = tomorrow_trading_date()
    return all_picks, gstats


def fetch_garden_picks_bundle(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]],
    fetch_fn: FetchFn,
    *,
    max_a: int = 5,
    max_global_per_market: int = 2,
    pick_log: list[dict[str, Any]] | None = None,
    calibration: dict[str, Any] | None = None,
    universe_override: pd.DataFrame | None = None,
    outlook: dict[str, Any] | None = None,
) -> tuple[list[DailyPick], list[DailyPick], str, dict[str, Any]]:
    """花园扫盘：宏观体制先行 → 明日 A 股 + 全球关注。"""
    from src.analysis.quantum_style import (
        gate_picks_by_regime,
        merge_regime_into_calibration,
        regime_from_outlook,
    )

    regime = regime_from_outlook(outlook)
    cal = merge_regime_into_calibration(calibration, regime)
    max_picks = min(max_a, regime.max_a_picks)

    a_picks, src, stats = fetch_tomorrow_a_picks(
        fetch_ranking,
        fetch_fn,
        max_picks=max_picks,
        pick_log=pick_log,
        calibration=cal,
        universe_override=universe_override,
    )
    a_picks = gate_picks_by_regime(a_picks, regime)
    global_picks, gstats = fetch_tomorrow_global_picks(max_per_market=max_global_per_market)
    if regime.label == "防守":
        global_picks = global_picks[:1]
    stats["global"] = gstats
    stats["global_count"] = len(global_picks)
    stats["predict_for"] = tomorrow_trading_date()
    stats["macro_regime"] = regime.as_dict()
    return a_picks, global_picks, src, stats


def picks_to_markdown(
    picks: list[DailyPick],
    *,
    day: str | None = None,
    global_picks: list[DailyPick] | None = None,
    target_date: str | None = None,
) -> str:
    tgt = target_date or tomorrow_trading_date()
    d = day or date.today().isoformat()
    lines = [
        f"# 明日推荐 · 目标交易日 {tgt}",
        "",
        f"> 基于 **{d}** 收盘数据 + 历史 K 线规则预测，非保证上涨。",
        "",
        "## 🇨🇳 A股 · 明日偏强",
    ]
    if not picks:
        lines.append("暂无达标标的（已扫涨幅/换手/成交额多榜 + K 线）。")
    else:
        lines.append("| 信号 | 名称 | 代码 | 明日分 | 今日% | 理由 |")
        lines.append("|------|------|------|--------|-------|------|")
        for p in picks:
            sc = f"{p.score:.1f}" if p.score is not None else "—"
            pc = f"{p.pct:+.2f}" if p.pct is not None else "—"
            sig = p.signal.replace("买入", "明日偏多").replace("观望", "明日观望")
            lines.append(f"| {sig} | {p.name} | {p.code} | {sc} | {pc} | {p.reason[:44]} |")

    gp = global_picks or []
    lines.extend(["", "## 🌍 全球 · 明日关注（港/美）"])
    if not gp:
        lines.append("暂无港/美明日关注。")
    else:
        lines.append("| 市场 | 信号 | 名称 | 代码 | 分数 | 今日% | 理由 |")
        lines.append("|------|------|------|------|------|-------|------|")
        for p in gp:
            sc = f"{p.score:.1f}" if p.score is not None else "—"
            pc = f"{p.pct:+.2f}" if p.pct is not None else "—"
            lines.append(
                f"| {p.market} | {p.signal} | {p.name} | {p.code} | {sc} | {pc} | {p.reason[:36]} |"
            )
    lines.extend(["", "*规则型预测，非投资建议。*"])
    return "\n".join(lines)
