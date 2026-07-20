"""预测 vs 真实：K 线复核、准确率统计、模型校准（P125 核心）。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from src.analysis.pick_review import (
    Pick3dReview,
    extract_pattern,
    review_pick_3d,
    review_recent_picks,
    strategy_hints_from_reviews,
)
from src.analysis.pick_tracker import normalize_pick_log

FetchFn = Callable[..., tuple[Any, str]]

HIT_THRESHOLD_PCT = 0.0  # 持有期内最高涨幅 > 0 视为命中


@dataclass(frozen=True)
class CalibrationReport:
    generated_at: str
    reviewed: int
    hit_rate_pct: float | None
    avg_max_ret_pct: float | None
    by_pattern: tuple[dict[str, Any], ...]
    by_signal: tuple[dict[str, Any], ...]
    pattern_adjustments: dict[str, float]
    score_floor_delta: float
    buy_threshold_delta: float
    conclusions: tuple[str, ...]
    recent_rows: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "reviewed": self.reviewed,
            "hit_rate_pct": self.hit_rate_pct,
            "avg_max_ret_pct": self.avg_max_ret_pct,
            "by_pattern": list(self.by_pattern),
            "by_signal": list(self.by_signal),
            "pattern_adjustments": dict(self.pattern_adjustments),
            "score_floor_delta": self.score_floor_delta,
            "buy_threshold_delta": self.buy_threshold_delta,
            "conclusions": list(self.conclusions),
            "recent_rows": list(self.recent_rows),
        }


def merge_pick_logs(*logs: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    """合并本地/云端推荐记录（同日期同代码去重，保留较新 verified 状态）。"""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in logs:
        for r in normalize_pick_log(raw):
            key = (str(r.get("pick_date") or "")[:10], str(r.get("code") or "").zfill(6))
            if not key[0] or not key[1]:
                continue
            prev = merged.get(key)
            if prev is None or bool(r.get("verified")) or not prev.get("verified"):
                merged[key] = dict(r)
    return sorted(merged.values(), key=lambda x: (str(x.get("pick_date")), str(x.get("code"))))


def verify_log_with_kline(
    log: list[dict[str, Any]] | Any,
    fetch_fn: FetchFn,
    *,
    today: date | None = None,
    horizon: int = 3,
) -> list[dict[str, Any]]:
    """用推荐日收盘价 vs 后续 K 线真实涨跌验证（替代榜单涨跌幅对比）。"""
    ref = today or date.today()
    out: list[dict[str, Any]] = []
    for rec in normalize_pick_log(log):
        row = dict(rec)
        pick_day_s = str(row.get("pick_date") or "")[:10]
        try:
            pick_day = date.fromisoformat(pick_day_s)
        except ValueError:
            out.append(row)
            continue
        if (ref - pick_day).days < 1:
            out.append(row)
            continue
        rev = review_pick_3d(row, fetch_fn, today=ref, horizon=horizon)
        if rev is None or rev.max_ret_3d_pct is None:
            out.append(row)
            continue
        row["verified"] = True
        row["end_pct"] = rev.max_ret_3d_pct
        row["hit"] = bool(rev.hit_3d)
        row["ret_d1_pct"] = rev.ret_d1_pct
        row["ret_d2_pct"] = rev.ret_d2_pct
        row["ret_d3_pct"] = rev.ret_d3_pct
        row["note"] = rev.note
        if not row.get("pattern"):
            row["pattern"] = rev.pattern
        out.append(row)
    return out[-200:]


def build_calibration_report(
    log: list[dict[str, Any]] | Any,
    fetch_fn: FetchFn,
    *,
    today: date | None = None,
    review_limit: int = 30,
    snapshot_diff: dict[str, Any] | None = None,
) -> CalibrationReport:
    """复盘全部可验证推荐 → 统计准确率 → 输出模型校准参数与可读结论。"""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    verified_log = verify_log_with_kline(log, fetch_fn, today=today)
    reviews = review_recent_picks(verified_log, fetch_fn, today=today, within_days=30, limit=review_limit)

    verified = [r for r in verified_log if r.get("verified") and r.get("hit") is not None]
    hits = sum(1 for r in verified if r.get("hit"))
    total = len(verified)
    rate = (hits / total * 100.0) if total else None
    rets = [float(r["end_pct"]) for r in verified if r.get("end_pct") is not None]
    avg_ret = sum(rets) / len(rets) if rets else None

    by_pat: dict[str, list[bool]] = defaultdict(list)
    by_pat_ret: dict[str, list[float]] = defaultdict(list)
    by_sig: dict[str, list[bool]] = defaultdict(list)
    for r in verified:
        pat = str(r.get("pattern") or "") or extract_pattern(
            str(r.get("reason") or ""), str(r.get("signal") or "")
        )
        by_pat[pat].append(bool(r.get("hit")))
        if r.get("end_pct") is not None:
            by_pat_ret[pat].append(float(r["end_pct"]))
        sig = str(r.get("signal") or "未知")
        by_sig[sig].append(bool(r.get("hit")))

    pat_rows: list[dict[str, Any]] = []
    pattern_adj: dict[str, float] = {}
    for pat, arr in sorted(by_pat.items(), key=lambda x: -len(x[1])):
        if not pat:
            continue
        n = len(arr)
        h = sum(1 for x in arr if x)
        pr = h / n * 100.0 if n else 0.0
        avg_p = sum(by_pat_ret.get(pat) or [0]) / max(1, len(by_pat_ret.get(pat) or []))
        pat_rows.append({"模式": pat, "样本": n, "命中%": round(pr, 1), "均最高涨幅%": round(avg_p, 2)})
        if n >= 3:
            if pr >= 60:
                pattern_adj[pat] = 3.0
            elif pr <= 35:
                pattern_adj[pat] = -5.0
            elif pr <= 45:
                pattern_adj[pat] = -2.5

    sig_rows: list[dict[str, Any]] = []
    for sig, arr in sorted(by_sig.items(), key=lambda x: -len(x[1])):
        n = len(arr)
        h = sum(1 for x in arr if x)
        sig_rows.append({"信号": sig, "样本": n, "命中%": round(h / n * 100.0, 1) if n else 0.0})

    score_floor_delta = 0.0
    buy_threshold_delta = 0.0
    if rate is not None:
        if rate < 40:
            score_floor_delta = 4.0
            buy_threshold_delta = 3.0
        elif rate < 50:
            score_floor_delta = 2.0
            buy_threshold_delta = 1.5
        elif rate >= 65:
            score_floor_delta = -1.0
            buy_threshold_delta = -0.5

    conclusions: list[str] = []
    if total == 0:
        conclusions.append("尚无足够到期样本；每次预测后会自动与后续 K 线对比。")
    else:
        conclusions.append(f"近 {total} 次预测，3 日内跑赢 {hits} 次（{rate:.0f}%）。")
        if avg_ret is not None:
            conclusions.append(f"持有期最高涨幅均值 {avg_ret:+.2f}%。")
        conclusions.extend(strategy_hints_from_reviews(reviews)[:4])
        if score_floor_delta > 0:
            conclusions.append(
                f"整体偏弱 → 明日扫盘最低分 +{score_floor_delta:.0f}、买入门槛 +{buy_threshold_delta:.1f}。"
            )
        for pat, delta in pattern_adj.items():
            if delta < 0:
                conclusions.append(f"「{pat}」近绩不佳，模式权重 {delta:+.1f}。")

    score_floor_delta, buy_threshold_delta, conclusions = _apply_snapshot_calibration(
        snapshot_diff,
        score_floor_delta,
        buy_threshold_delta,
        conclusions,
    )

    recent: list[dict[str, Any]] = []
    for r in verified[-8:][::-1]:
        recent.append(
            {
                "日期": str(r.get("pick_date") or "")[:10],
                "代码": r.get("code"),
                "名称": r.get("name"),
                "模式": r.get("pattern") or "—",
                "预测": r.get("signal") or "—",
                "3日最高%": r.get("end_pct"),
                "结果": "✅" if r.get("hit") else "❌",
                "明细": r.get("note") or "",
            }
        )

    return CalibrationReport(
        generated_at=now,
        reviewed=total,
        hit_rate_pct=round(rate, 1) if rate is not None else None,
        avg_max_ret_pct=round(avg_ret, 2) if avg_ret is not None else None,
        by_pattern=tuple(pat_rows),
        by_signal=tuple(sig_rows),
        pattern_adjustments=pattern_adj,
        score_floor_delta=score_floor_delta,
        buy_threshold_delta=buy_threshold_delta,
        conclusions=tuple(conclusions[:10]),
        recent_rows=tuple(recent),
    )


def _apply_snapshot_calibration(
    diff: dict[str, Any] | None,
    score_floor: float,
    buy_delta: float,
    conclusions: list[str],
) -> tuple[float, float, list[str]]:
    """快照次日验证并入校准（便宜层反馈）。"""
    if not diff:
        return score_floor, buy_delta, conclusions
    checks = list(diff.get("pick_checks") or [])
    if not checks:
        return score_floor, buy_delta, conclusions
    hits = sum(1 for c in checks if c.get("hit"))
    rate = hits / len(checks) * 100.0
    conclusions = list(conclusions)
    conclusions.append(f"快照次日验证 {hits}/{len(checks)} 方向正确（{rate:.0f}%）。")
    if rate < 40:
        score_floor += 1.5
        buy_delta += 1.0
    elif rate < 55:
        score_floor += 0.5
    return score_floor, buy_delta, conclusions


def load_calibration_adjustments(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {}
    return {
        "pattern": dict(report.get("pattern_adjustments") or {}),
        "score_floor_delta": float(report.get("score_floor_delta") or 0),
        "buy_threshold_delta": float(report.get("buy_threshold_delta") or 0),
    }
