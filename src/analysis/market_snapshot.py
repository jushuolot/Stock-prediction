"""全市场轻量快照：每日榜单合并 → 次日对比 → 精选深度分析（P126）。

资源策略（省算力）：
- 第 1 层：3 次榜单 API → ~150 只股票快照（无 K 线）
- 第 2 层：与昨日快照 diff → 验证昨日预测 + 挑异动
- 第 3 层：仅对 ~20 只候选跑 K 线明日模型（现有进化逻辑）
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.storage.paths import project_root

SNAPSHOT_DIR = project_root() / "cloud_state" / "market_snapshots"
DIFF_JSON = project_root() / "cloud_state" / "market_snapshot_diff.json"
WEEKLY_JSON = project_root() / "cloud_state" / "weekly_summary.json"
FOLLOWUPS_JSON = project_root() / "cloud_state" / "deep_followups.json"

FetchRankingFn = Callable[[], tuple[pd.DataFrame, str]]
FetchFn = Callable[..., tuple[Any, str]]


def _f(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def rows_from_universe(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        code = str(row.get("代码") or "").replace(".0", "").strip()
        if len(code) != 6 or not code.isdigit():
            continue
        out.append(
            {
                "code": code,
                "name": str(row.get("名称") or ""),
                "pct": _f(row.get("涨跌幅%")),
                "turn": _f(row.get("换手率%")),
                "amount": _f(row.get("成交额")),
                "price": _f(row.get("最新价") or row.get("现价") or row.get("价格")),
            }
        )
    return out


def capture_market_snapshot(
    universe: pd.DataFrame,
    *,
    day: str | None = None,
    source: str = "",
) -> dict[str, Any]:
    d = day or date.today().isoformat()
    rows = rows_from_universe(universe)
    return {
        "date": d,
        "count": len(rows),
        "source": source,
        "rows": rows,
    }


def save_market_snapshot(snapshot: dict[str, Any], *, root: Path | None = None) -> Path:
    base = root or SNAPSHOT_DIR
    base.mkdir(parents=True, exist_ok=True)
    day = str(snapshot.get("date") or date.today().isoformat())
    path = base / f"{day}.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_market_snapshot(day: str, *, root: Path | None = None) -> dict[str, Any] | None:
    base = root or SNAPSHOT_DIR
    path = base / f"{day}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def find_previous_snapshot_day(before: str, *, root: Path | None = None, lookback: int = 10) -> str | None:
    try:
        d0 = date.fromisoformat(before[:10])
    except ValueError:
        return None
    base = root or SNAPSHOT_DIR
    for i in range(1, lookback + 1):
        d = (d0 - timedelta(days=i)).isoformat()
        if (base / f"{d}.json").is_file():
            return d
    return None


def _row_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(r.get("code") or ""): r for r in (snapshot.get("rows") or []) if r.get("code")}


@dataclass(frozen=True)
class SnapshotDiff:
    prev_date: str
    curr_date: str
    compared: int
    avg_pct_delta: float | None
    movers: tuple[dict[str, Any], ...]
    pick_checks: tuple[dict[str, Any], ...]
    conclusions: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "prev_date": self.prev_date,
            "curr_date": self.curr_date,
            "compared": self.compared,
            "avg_pct_delta": self.avg_pct_delta,
            "movers": list(self.movers),
            "pick_checks": list(self.pick_checks),
            "conclusions": list(self.conclusions),
        }


def diff_snapshots(
    prev: dict[str, Any],
    curr: dict[str, Any],
    *,
    yesterday_picks: list[dict[str, Any]] | None = None,
) -> SnapshotDiff:
    pm = _row_map(prev)
    cm = _row_map(curr)
    codes = set(pm) & set(cm)
    movers: list[dict[str, Any]] = []
    deltas: list[float] = []

    for code in codes:
        p_pct = _f(pm[code].get("pct"))
        c_pct = _f(cm[code].get("pct"))
        if p_pct is None or c_pct is None:
            continue
        delta = c_pct - p_pct
        deltas.append(delta)
        movers.append(
            {
                "code": code,
                "name": cm[code].get("name") or pm[code].get("name"),
                "prev_pct": round(p_pct, 2),
                "curr_pct": round(c_pct, 2),
                "delta_pct": round(delta, 2),
            }
        )

    movers.sort(key=lambda x: abs(float(x.get("delta_pct") or 0)), reverse=True)
    avg_d = sum(deltas) / len(deltas) if deltas else None

    pick_checks: list[dict[str, Any]] = []
    for p in yesterday_picks or []:
        code = str(p.get("code") or "").zfill(6)
        if code not in codes:
            continue
        m = next((x for x in movers if x["code"] == code), None)
        if not m:
            continue
        predicted = str(p.get("signal") or "")
        hit = float(m["delta_pct"]) > 0
        pick_checks.append(
            {
                "code": code,
                "name": p.get("name") or m.get("name"),
                "signal": predicted,
                "delta_pct": m["delta_pct"],
                "hit": hit,
            }
        )

    conclusions: list[str] = []
    if avg_d is not None:
        conclusions.append(f"快照对比 {len(codes)} 只，均涨跌变化 {avg_d:+.2f}%。")
    if pick_checks:
        hits = sum(1 for x in pick_checks if x.get("hit"))
        conclusions.append(f"昨日推荐 {len(pick_checks)} 只，快照验证 {hits} 只方向正确。")
    if movers:
        top = movers[0]
        conclusions.append(
            f"最大异动 {top.get('name')} {top.get('code')} Δ{top.get('delta_pct'):+.1f}%。"
        )

    return SnapshotDiff(
        prev_date=str(prev.get("date") or ""),
        curr_date=str(curr.get("date") or ""),
        compared=len(codes),
        avg_pct_delta=round(avg_d, 2) if avg_d is not None else None,
        movers=tuple(movers[:15]),
        pick_checks=tuple(pick_checks),
        conclusions=tuple(conclusions),
    )


def select_deep_candidates(
    universe: pd.DataFrame,
    diff: SnapshotDiff | dict[str, Any] | None,
    *,
    yesterday_picks: list[dict[str, Any]] | None = None,
    max_scan: int = 24,
) -> tuple[pd.DataFrame, list[str]]:
    """从全量快照中筛出值得跑 K 线的候选（小集合）。"""
    reasons: list[str] = []
    codes: dict[str, str] = {}

    for p in yesterday_picks or []:
        c = str(p.get("code") or "").zfill(6)
        if c.isdigit() and len(c) == 6:
            codes[c] = "昨日推荐"
    if diff:
        d = diff if isinstance(diff, dict) else diff.as_dict()
        for m in d.get("movers") or []:
            c = str(m.get("code") or "")
            if abs(float(m.get("delta_pct") or 0)) >= 1.5 and c not in codes:
                codes[c] = "快照异动"
        for pc in d.get("pick_checks") or []:
            c = str(pc.get("code") or "")
            if pc.get("hit") is False and c:
                codes[c] = "预测未中·复盘"

    if universe is None or universe.empty:
        return pd.DataFrame(), reasons

    work = universe.copy()
    work["_code"] = work["代码"].astype(str).str.replace(".0", "", regex=False).str.strip()
    if codes:
        sub = work[work["_code"].isin(codes.keys())].copy()
        reasons = [f"{codes.get(c, '候选')}: {c}" for c in sub["_code"].tolist()[:max_scan]]
    else:
        sub = work.head(max_scan).copy()
        reasons.append("无 diff 时取榜单前段")

    if len(sub) < max_scan:
        extra = work[~work["_code"].isin(sub["_code"])].head(max_scan - len(sub))
        sub = pd.concat([sub, extra], ignore_index=True)

    sub = sub.drop(columns=["_code"], errors="ignore")
    return sub.head(max_scan), reasons[:12]


def run_daily_snapshot_pipeline(
    fetch_ranking: FetchRankingFn,
    *,
    fetch_fn: FetchFn | None = None,
    yesterday_picks: list[dict[str, Any]] | None = None,
    day: str | None = None,
) -> dict[str, Any]:
    """每日 cron：快照 → diff → 精选 universe → 异动再分析。"""
    from src.analysis.deep_followup import build_deep_followups
    from src.analysis.tomorrow_picks import build_a_universe

    universe, src = build_a_universe(fetch_ranking)
    today = day or date.today().isoformat()
    snap = capture_market_snapshot(universe, day=today, source=src)
    save_market_snapshot(snap)

    prev_day = find_previous_snapshot_day(today)
    diff_dict: dict[str, Any] | None = None
    if prev_day:
        prev = load_market_snapshot(prev_day)
        if prev:
            diff = diff_snapshots(prev, snap, yesterday_picks=yesterday_picks)
            diff_dict = diff.as_dict()
            DIFF_JSON.parent.mkdir(parents=True, exist_ok=True)
            DIFF_JSON.write_text(json.dumps(diff_dict, ensure_ascii=False, indent=2), encoding="utf-8")

    deep_uni, reasons = select_deep_candidates(universe, diff_dict, yesterday_picks=yesterday_picks)
    weekly = append_weekly_rollup(diff_dict, snap, yesterday_picks=yesterday_picks)

    followups: list[dict[str, Any]] = []
    if fetch_fn and diff_dict:
        followups = build_deep_followups(diff_dict, universe, fetch_fn)
        FOLLOWUPS_JSON.parent.mkdir(parents=True, exist_ok=True)
        FOLLOWUPS_JSON.write_text(
            json.dumps({"date": today, "items": followups}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return {
        "snapshot": snap,
        "diff": diff_dict,
        "deep_universe_rows": len(deep_uni),
        "deep_reasons": reasons,
        "deep_universe": deep_uni,
        "deep_followups": followups,
        "weekly_summary": weekly,
    }


def append_weekly_rollup(
    diff: dict[str, Any] | None,
    snapshot: dict[str, Any],
    *,
    yesterday_picks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """滚动 7 日汇总，供你每周看成果。"""
    today = str(snapshot.get("date") or date.today().isoformat())
    entry = {
        "date": today,
        "snapshot_count": snapshot.get("count"),
        "diff": diff,
        "picks_checked": len((diff or {}).get("pick_checks") or []),
    }
    hist: list[dict[str, Any]] = []
    if WEEKLY_JSON.is_file():
        try:
            data = json.loads(WEEKLY_JSON.read_text(encoding="utf-8"))
            hist = list(data.get("days") or [])
        except (json.JSONDecodeError, OSError):
            hist = []
    hist = [h for h in hist if str(h.get("date")) != today] + [entry]
    hist = hist[-7:]
    hits = 0
    checks = 0
    for h in hist:
        for pc in (h.get("diff") or {}).get("pick_checks") or []:
            checks += 1
            if pc.get("hit"):
                hits += 1
    summary = {
        "updated_at": today,
        "days": hist,
        "week_hit_rate_pct": round(hits / checks * 100, 1) if checks else None,
        "week_checks": checks,
        "headline": (
            f"近 {len(hist)} 个交易日快照；预测快照验证 {hits}/{checks} 方向正确。"
            if checks
            else f"近 {len(hist)} 日全市场快照已积累，待预测样本验证。"
        ),
    }
    WEEKLY_JSON.parent.mkdir(parents=True, exist_ok=True)
    WEEKLY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def weekly_summary_to_markdown(
    weekly: dict[str, Any] | None,
    *,
    calibration: dict[str, Any] | None = None,
    followups: list[dict[str, Any]] | None = None,
) -> str:
    """供每周汇总的可读 Markdown。"""
    w = weekly or {}
    lines = ["# 选股花园 · 周成果汇总", ""]
    lines.append(f"**{w.get('headline') or '暂无数据'}**")
    rate = w.get("week_hit_rate_pct")
    if rate is not None:
        lines.append(f"- 快照验证命中率：**{rate:.0f}%**（{w.get('week_checks')} 次）")
    cal = calibration or {}
    if cal.get("hit_rate_pct") is not None:
        lines.append(
            f"- K线校准命中率：**{cal['hit_rate_pct']:.0f}%**（样本 {cal.get('reviewed')}）"
        )
    for c in cal.get("conclusions") or []:
        lines.append(f"- {c}")
    lines.append("")
    if followups:
        lines.append("## 值得再分析")
        for f in followups:
            lines.append(
                f"- **{f.get('name')}** `{f.get('code')}` · {f.get('tag')} · "
                f"{f.get('verdict')} · {f.get('one_line')}"
            )
    lines.extend(["", "*规则分析，非投资建议。*"])
    return "\n".join(lines)
