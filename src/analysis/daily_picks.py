"""今日 A 股自动筛选（P103）：公开榜单 + 技术评分 → 买/观望信号。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Callable

import pandas as pd

from src.analysis.quick_analyze import analyze_watch_light

FetchFn = Callable[..., tuple[pd.DataFrame, str]]

SIGNAL_BUY = "买入"
SIGNAL_WATCH = "观望"
SIGNAL_SKIP = "回避"


@dataclass(frozen=True)
class DailyPick:
    code: str
    name: str
    score: float | None
    pct: float | None
    signal: str
    hold_days: str
    reason: str
    price: float | None = None
    market: str = "A股"
    fund_tag: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _row_to_item(row: pd.Series) -> dict[str, Any]:
    code = str(row.get("代码") or "").replace(".0", "").strip()
    market = str(row.get("市场") or "A")
    return {
        "代码": code,
        "名称": str(row.get("名称") or code),
        "类型": str(row.get("类型") or "A"),
        "市场": market,
        "货币": "CNY",
    }


def _signal_from(score: float | None, pct: float | None) -> tuple[str, str, str]:
    """返回 (信号, 持有建议, 理由片段)。"""
    if score is None:
        if pct is not None and 1.0 <= pct <= 19.9:
            return SIGNAL_WATCH, "1–3天", "榜单动能强（轻量模式）"
        if pct is not None and 0.3 <= pct < 1.0:
            return SIGNAL_WATCH, "1–2天", "温和上涨，可观察"
        return SIGNAL_SKIP, "—", "暂无评分"
    if pct is not None and pct >= 9.5:
        return SIGNAL_WATCH, "1–2天", "涨停附近，仅观察不追"
    if pct is not None and pct <= -3:
        return SIGNAL_SKIP, "—", "弱势下跌，暂不介入"
    if score >= 68 and (pct is None or pct >= 0.5):
        return SIGNAL_BUY, "3–5天", "评分偏强且动能尚可"
    if score >= 55:
        return SIGNAL_WATCH, "2–3天", "评分中性偏上，可小仓观察"
    if score >= 48 and (pct is None or pct >= 0.3):
        return SIGNAL_WATCH, "2–3天", "评分尚可，谨慎观察"
    return SIGNAL_SKIP, "—", "评分偏弱"


def _is_st_name(name: str) -> bool:
    n = (name or "").upper()
    return "ST" in n or "*ST" in n


def _pct_ok(pct: float | None, lo: float, hi: float) -> bool:
    if pct is None:
        return True
    return lo <= pct <= hi


def _collect_candidates(
    df: pd.DataFrame,
    *,
    max_scan: int,
    pct_tiers: list[tuple[float, float]],
) -> tuple[list[tuple[dict[str, Any], float | None]], dict[str, Any]]:
    """按多档涨跌幅阈值收集候选；强市日涨停多也能扫出标的。"""
    stats: dict[str, Any] = {"skipped_st": 0, "skipped_pct": 0, "skipped_anomaly": 0}
    if df is None or df.empty:
        return [], stats

    work = df.copy()
    if "涨跌幅%" in work.columns:
        work = work.sort_values("涨跌幅%", ascending=False)

    chosen: list[tuple[dict[str, Any], float | None]] = []
    seen: set[str] = set()

    for lo, hi in pct_tiers:
        for _, row in work.iterrows():
            if len(chosen) >= max_scan:
                break
            item = _row_to_item(row)
            code = item["代码"]
            name = item["名称"]
            if not code or code in seen:
                continue
            if item.get("市场") == "A" or item.get("类型") == "A":
                if len(code) != 6 or not code.isdigit():
                    continue
            if _is_st_name(name):
                stats["skipped_st"] += 1
                continue
            try:
                pct = float(row.get("涨跌幅%"))
            except (TypeError, ValueError):
                pct = None
            if pct is not None and abs(pct) > 35:
                stats["skipped_anomaly"] += 1
                continue
            if not _pct_ok(pct, lo, hi):
                stats["skipped_pct"] += 1
                continue
            seen.add(code)
            chosen.append((item, pct))
        if chosen:
            break
    return chosen, stats


def _signal_from_global(anomaly: float, pct: float | None) -> tuple[str, str, str]:
    if pct is not None and pct >= 12:
        return SIGNAL_WATCH, "1–2天", "短线涨幅偏大，仅观察"
    if anomaly >= 62 and (pct is None or pct >= 0.5):
        return SIGNAL_BUY, "3–7天", "全球榜单动能强"
    if anomaly >= 40 and (pct is None or pct >= 0.3):
        return SIGNAL_WATCH, "2–5天", "全球异动可关注"
    return SIGNAL_SKIP, "—", "动能偏弱"


GLOBAL_PCT_ABS_MAX = 50.0


def _is_weird_global_ticker(code: str, name: str, market_label: str) -> bool:
    """过滤权证壳股、OTC 粉单等异常代码。"""
    c = (code or "").upper().strip().replace(".HK", "")
    n = (name or "").upper()
    if market_label == "港股" and c.isdigit() and len(c) >= 5 and c.startswith("55"):
        return True
    if market_label == "美股":
        if len(c) > 6 or (len(c) == 5 and c.endswith("F")):
            return True
        if len(n) > 45:
            return True
    return False


def _global_price_penalty(price: float | None, market_label: str) -> float:
    if price is None:
        return 0.0
    if market_label == "美股" and price < 2.0:
        return 22.0
    if market_label == "港股" and price < 0.5:
        return 18.0
    return 0.0


def rank_global_from_ranking(
    ranking_df: pd.DataFrame,
    *,
    market_label: str = "港股",
    max_picks: int = 2,
) -> tuple[list[DailyPick], dict[str, Any]]:
    """港/美涨幅榜 → 轻量异动分 → 观望/买入。"""
    from src.analysis.global_anomaly import analyze_one_mover_fast

    stats: dict[str, Any] = {
        "scanned": 0,
        "market": market_label,
        "skipped_anomaly": 0,
        "skipped_weird": 0,
    }
    if ranking_df is None or ranking_df.empty:
        return [], stats

    picks: list[DailyPick] = []
    df = ranking_df.copy()
    if "涨跌幅%" in df.columns:
        df = df.sort_values("涨跌幅%", ascending=False)

    for _, row in df.iterrows():
        if len(picks) >= max_picks:
            break
        stats["scanned"] += 1
        item = _row_to_item(row)
        code = item["代码"]
        name = item["名称"]
        if not code:
            continue
        if _is_weird_global_ticker(code, name, market_label):
            stats["skipped_weird"] = int(stats.get("skipped_weird") or 0) + 1
            continue
        try:
            pct = float(row.get("涨跌幅%"))
        except (TypeError, ValueError):
            pct = None
        if pct is not None and (pct <= 0 or abs(pct) > GLOBAL_PCT_ABS_MAX):
            stats["skipped_anomaly"] = int(stats.get("skipped_anomaly") or 0) + 1
            continue
        price = row.get("最新价")
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None
        fast = analyze_one_mover_fast(row.to_dict(), market=market_label)
        anomaly = float(fast.anomaly_score) - _global_price_penalty(price_f, market_label)
        signal, hold, reason_bit = _signal_from_global(anomaly, pct)
        if signal == SIGNAL_SKIP:
            continue
        cap = fast.capital.as_dict()
        flow = str(cap.get("主力倾向") or "")
        reason = reason_bit
        if flow:
            reason = f"{reason_bit}；{flow[:40]}"
        if price_f is not None and _global_price_penalty(price_f, market_label) > 0:
            reason = f"{reason_bit}（低价股降权）"
        picks.append(
            DailyPick(
                code=code,
                name=item["名称"],
                score=round(max(0.0, anomaly), 1),
                pct=pct,
                signal=signal,
                hold_days=hold,
                reason=reason,
                price=price_f,
                market=market_label,
            )
        )
    return picks, stats


def rank_candidates_from_ranking(
    ranking_df: pd.DataFrame,
    *,
    fetch_fn: FetchFn | None = None,
    max_scan: int = 18,
    max_picks: int = 5,
) -> tuple[list[DailyPick], dict[str, Any]]:
    """
    从 A 股涨幅榜 DataFrame 筛出今日可关注标的。
    fetch_fn 提供时对前 max_scan 只做轻量 K 线评分；否则仅用榜单涨跌幅粗筛。
    """
    stats: dict[str, Any] = {"scanned": 0, "skipped_st": 0, "skipped_pct": 0, "skipped_anomaly": 0, "errors": 0}
    if ranking_df is None or ranking_df.empty:
        return [], stats

    pct_tiers = [
        (0.3, 9.5),
        (0.0, 19.9),
        (-2.0, 29.9),
    ]
    candidates, collect_stats = _collect_candidates(
        ranking_df,
        max_scan=max_scan,
        pct_tiers=pct_tiers,
    )
    stats.update(collect_stats)

    picks: list[DailyPick] = []
    for item, list_pct in candidates:
        stats["scanned"] += 1
        score: float | None = None
        price: float | None = None
        one_line = ""
        try:
            if fetch_fn is not None:
                snap = analyze_watch_light(item, fetch_fn, days=60)
                score = snap.score
                price = snap.price
                one_line = snap.one_line
                if list_pct is None and snap.pct is not None:
                    list_pct = snap.pct
            else:
                try:
                    list_pct = float(list_pct) if list_pct is not None else None
                except (TypeError, ValueError):
                    list_pct = None
        except Exception:
            stats["errors"] += 1
            continue

        signal, hold, reason_bit = _signal_from(score, list_pct)
        if signal == SIGNAL_SKIP and score is not None and score < 50:
            continue
        reason = reason_bit
        if one_line and one_line not in ("—", "暂无评分。"):
            reason = f"{reason_bit}；{one_line[:60]}"
        try:
            price = price or float(item.get("最新价") or 0) or None
        except (TypeError, ValueError):
            pass

        picks.append(
            DailyPick(
                code=item["代码"],
                name=item["名称"],
                score=score,
                pct=list_pct,
                signal=signal,
                hold_days=hold,
                reason=reason,
                price=price,
                market=str(item.get("市场") or "A股"),
            )
        )

    # 买入优先，其次观望，按评分降序
    order = {SIGNAL_BUY: 0, SIGNAL_WATCH: 1, SIGNAL_SKIP: 2}

    def sort_key(p: DailyPick) -> tuple:
        sc = p.score if p.score is not None else 0.0
        return (order.get(p.signal, 9), -sc)

    picks.sort(key=sort_key)
    buy_watch = [p for p in picks if p.signal in (SIGNAL_BUY, SIGNAL_WATCH)]
    if not buy_watch and picks:
        # 强市日涨停多：兜底取评分最高的 2 只标为观望
        fallback = sorted(picks, key=lambda p: -(p.score or 0))[:2]
        buy_watch = [
            DailyPick(
                code=p.code,
                name=p.name,
                score=p.score,
                pct=p.pct,
                signal=SIGNAL_WATCH,
                hold_days="1–3天",
                reason=f"强市兜底；{p.reason[:50]}",
                price=p.price,
                market=p.market,
            )
            for p in fallback
            if (p.score or 0) >= 40
        ]
    if not buy_watch and candidates:
        # K 线拉取失败时：纯榜单轻量推荐
        for item, list_pct in candidates[:max_picks]:
            signal, hold, reason = _signal_from(None, list_pct)
            if signal == SIGNAL_SKIP:
                continue
            buy_watch.append(
                DailyPick(
                    code=item["代码"],
                    name=item["名称"],
                    score=None,
                    pct=list_pct,
                    signal=signal,
                    hold_days=hold,
                    reason=reason,
                    price=None,
                    market=str(item.get("市场") or "A股"),
                )
            )
    return buy_watch[:max_picks], stats


def fetch_and_rank_a_picks(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]],
    fetch_fn: FetchFn,
    *,
    max_picks: int = 5,
) -> tuple[list[DailyPick], str, dict[str, Any]]:
    """拉 A 股涨幅榜并评分筛选；无结果时尝试换手率榜。"""
    df, src = fetch_ranking()
    picks, stats = rank_candidates_from_ranking(
        df,
        fetch_fn=fetch_fn,
        max_scan=24,
        max_picks=max_picks,
    )
    if not picks:
        from src.providers import market_data

        df2, src2 = market_data.fetch_a_ranking_multi(board="换手率榜", limit=40)
        if not df2.empty:
            picks2, stats2 = rank_candidates_from_ranking(
                df2,
                fetch_fn=fetch_fn,
                max_scan=20,
                max_picks=max_picks,
            )
            if picks2:
                picks, stats = picks2, stats2
                src = f"{src2}（换手率榜备用）"
    stats["source"] = src
    stats["board"] = "涨幅榜"
    stats["market"] = "A股"
    return picks, src, stats


def fetch_global_watch_picks(
    *,
    max_per_market: int = 2,
) -> tuple[list[DailyPick], dict[str, Any]]:
    """港/美各取少量全球关注（A 股为主、全球不丢）。"""
    from src.providers import market_data

    all_picks: list[DailyPick] = []
    gstats: dict[str, Any] = {"hk": 0, "us": 0}
    for label in ("港股", "美股"):
        df, src = market_data.fetch_global_ranking_multi(market=label, board="涨幅榜", limit=30)
        part, st = rank_global_from_ranking(df, market_label=label, max_picks=max_per_market)
        all_picks.extend(part)
        gstats["us" if label == "美股" else "hk"] = len(part)
        gstats[f"source_{label}"] = src
    gstats["total"] = len(all_picks)
    return all_picks, gstats


def fetch_garden_picks_bundle(
    fetch_ranking: Callable[[], tuple[pd.DataFrame, str]],
    fetch_fn: FetchFn,
    *,
    max_a: int = 5,
    max_global_per_market: int = 2,
) -> tuple[list[DailyPick], list[DailyPick], str, dict[str, Any]]:
    """已迁移至 tomorrow_picks（明日预测引擎）。"""
    from src.analysis.tomorrow_picks import fetch_garden_picks_bundle as _bundle

    return _bundle(
        fetch_ranking,
        fetch_fn,
        max_a=max_a,
        max_global_per_market=max_global_per_market,
    )


def picks_to_markdown(
    picks: list[DailyPick],
    *,
    day: str | None = None,
    global_picks: list[DailyPick] | None = None,
) -> str:
    d = day or date.today().isoformat()
    lines = [f"# 今日推荐 · {d}", ""]
    lines.append("## 🇨🇳 A股")
    if not picks:
        lines.append("暂无符合条件的 A 股推荐（已尝试涨幅榜/换手率榜）。")
    else:
        lines.append("| 信号 | 名称 | 代码 | 评分 | 涨跌% | 持有 | 理由 |")
        lines.append("|------|------|------|------|-------|------|------|")
        for p in picks:
            sc = f"{p.score:.1f}" if p.score is not None else "—"
            pc = f"{p.pct:+.2f}" if p.pct is not None else "—"
            lines.append(
                f"| {p.signal} | {p.name} | {p.code} | {sc} | {pc} | {p.hold_days} | {p.reason[:40]} |"
            )
    gp = global_picks or []
    lines.extend(["", "## 🌍 全球关注（港/美）"])
    if not gp:
        lines.append("暂无港/美推荐。")
    else:
        lines.append("| 市场 | 信号 | 名称 | 代码 | 异动分 | 涨跌% | 理由 |")
        lines.append("|------|------|------|------|--------|-------|------|")
        for p in gp:
            sc = f"{p.score:.1f}" if p.score is not None else "—"
            pc = f"{p.pct:+.2f}" if p.pct is not None else "—"
            lines.append(
                f"| {p.market} | {p.signal} | {p.name} | {p.code} | {sc} | {pc} | {p.reason[:36]} |"
            )
    lines.extend(["", "*公开数据自动筛选，非投资建议。*"])
    return "\n".join(lines)
