#!/usr/bin/env python3
"""GitHub Actions / 公网定时：预测明日 A 股并写入 cloud_state（零本地）。

用法:
  cd stock-assistant
  python3 scripts/garden_cloud_cron.py
  python3 scripts/garden_cloud_cron.py --stdout

环境变量（GitHub Secrets）:
  STOCK_WEBHOOK_URL  — 可选，推送今日推荐 Markdown
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.tomorrow_picks import fetch_garden_picks_bundle, picks_to_markdown, tomorrow_trading_date  # noqa: E402
from src.analysis.market_outlook import compute_market_outlook, outlook_to_markdown  # noqa: E402
from src.providers import market_data  # noqa: E402
from src.ui import app_core as C  # noqa: E402
from src.analysis.prediction_calibration import (
    build_calibration_report,
    load_calibration_adjustments,
    merge_pick_logs,
)
from src.analysis.market_snapshot import run_daily_snapshot_pipeline
from src.storage.cloud_pick_log import load_cloud_pick_log, sync_cloud_pick_log  # noqa: E402
from src.util.buddha_nightly_brief import build_nightly_brief  # noqa: E402
from src.util.buddha_ritual import build_ritual_meta, probe_a_market  # noqa: E402

CLOUD_STATE_DIR = ROOT / "cloud_state"
LATEST_JSON = CLOUD_STATE_DIR / "latest_picks.json"


def _fetch_ranking():
    return market_data.fetch_a_ranking_multi(board="涨幅榜", limit=60)


def run_scan(*, max_picks: int = 5) -> dict:
    probe = probe_a_market()
    if not probe.fresh:
        raise RuntimeError(
            f"佛祖金标准：A股数据不新鲜（需 {probe.expected_lo}~{probe.expected_hi}，"
            f"实际 {probe.bar_date or '无'}）。{probe.error}"
        )
    existing = merge_pick_logs(load_cloud_pick_log())

    snap_pack = run_daily_snapshot_pipeline(
        _fetch_ranking,
        fetch_fn=C._fetch_one,
        yesterday_picks=existing[-30:],
        day=date.today().isoformat(),
    )
    deep_uni = snap_pack.get("deep_universe")

    calibration = None
    if existing:
        try:
            calibration = build_calibration_report(
                existing,
                C._fetch_one,
                snapshot_diff=snap_pack.get("diff"),
            ).as_dict()
        except Exception:
            calibration = None
    cal_adj = load_calibration_adjustments(calibration)

    # 宏观先行（量子启发）：先定体制，再扫盘
    outlook = compute_market_outlook()
    outlook_d = outlook.as_dict()

    a_picks, global_picks, src, stats = fetch_garden_picks_bundle(
        _fetch_ranking,
        C._fetch_one,
        max_a=max_picks,
        max_global_per_market=2,
        pick_log=existing,
        calibration=cal_adj,
        universe_override=deep_uni if deep_uni is not None and not deep_uni.empty else None,
        outlook=outlook_d,
    )
    if snap_pack.get("deep_reasons"):
        stats["snapshot_deep_reasons"] = snap_pack.get("deep_reasons")
        stats["snapshot_deep_rows"] = snap_pack.get("deep_universe_rows")
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    tgt = stats.get("predict_for") or tomorrow_trading_date()
    ritual = build_ritual_meta(
        probe,
        a_picks=len(a_picks),
        global_picks=len(global_picks),
        predict_for=tgt,
    )
    pick_day = now[:10]
    pick_meta = sync_cloud_pick_log(
        [p.as_dict() for p in a_picks],
        pick_day=pick_day,
        fetch_fn=C._fetch_one,
    )
    calibration = pick_meta.get("calibration") or calibration

    from src.analysis.quantum_style import enrich_daily_picks, quantum_brief_lines, regime_from_outlook

    regime = regime_from_outlook(outlook_d)
    a_dicts = enrich_daily_picks(a_picks, regime)
    g_dicts = enrich_daily_picks(global_picks, regime)
    q_hints = quantum_brief_lines(regime, a_dicts)
    strategy_hints = list(pick_meta.get("strategy_hints") or []) + q_hints

    nightly = build_nightly_brief(
        ritual=ritual,
        predict_for=tgt,
        a_picks=a_dicts,
        global_picks=g_dicts,
        outlook=outlook_d,
        hit_summary=pick_meta.get("hit_summary"),
        cloud_sync_at=now,
        strategy_hints=strategy_hints,
        macro_regime=regime.as_dict(),
    )
    payload = {
        "generated_at": now,
        "source": src,
        "stats": stats,
        "predict_for": tgt,
        "market_outlook": outlook_d,
        "macro_regime": regime.as_dict(),
        "ritual": ritual,
        "nightly_brief": nightly,
        "hit_summary": pick_meta.get("hit_summary"),
        "strategy_hints": strategy_hints,
        "calibration": calibration,
        "snapshot_diff": snap_pack.get("diff"),
        "weekly_summary": snap_pack.get("weekly_summary"),
        "deep_followups": snap_pack.get("deep_followups") or [],
        "snapshot_meta": {
            "count": (snap_pack.get("snapshot") or {}).get("count"),
            "deep_rows": snap_pack.get("deep_universe_rows"),
        },
        "data_probe": probe.as_dict(),
        "picks": a_dicts,
        "global_picks": g_dicts,
        "markdown": picks_to_markdown(
            a_picks, day=now[:10], global_picks=global_picks, target_date=tgt
        )
        + "\n\n"
        + outlook_to_markdown(outlook),
    }
    return payload


def write_cloud_state(payload: dict) -> Path:
    CLOUD_STATE_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = CLOUD_STATE_DIR / "meta.json"
    meta.write_text(
        json.dumps(
            {
                "last_run": payload.get("generated_at"),
                "pick_count": len(payload.get("picks") or []),
                "runner": "garden_cloud_cron",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return LATEST_JSON


def maybe_webhook(payload: dict) -> None:
    url = os.environ.get("STOCK_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        import urllib.request

        md = str(payload.get("markdown") or "")
        body = json.dumps({"text": md[:3500]}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=20)
        print("[garden_cloud_cron] webhook OK")
    except Exception as exc:
        print(f"[garden_cloud_cron] webhook FAIL: {exc}")


def main() -> int:
    stdout_only = "--stdout" in sys.argv
    try:
        payload = run_scan()
    except Exception as exc:
        print(f"[garden_cloud_cron] scan FAIL: {exc}")
        return 1
    n = len(payload.get("picks") or [])
    gn = len(payload.get("global_picks") or [])
    print(
        f"[garden_cloud_cron] a_picks={n} global={gn} "
        f"crash_prob={payload.get('market_outlook', {}).get('crash_prob_1_2w_pct')}% "
        f"source={payload.get('source')}"
    )
    if stdout_only:
        print(payload.get("markdown") or "")
        return 0
    if n == 0 and gn == 0 and LATEST_JSON.exists():
        try:
            old = json.loads(LATEST_JSON.read_text(encoding="utf-8"))
            old_n = len(old.get("picks") or [])
            old_gn = len(old.get("global_picks") or [])
            if old_n or old_gn:
                old["ritual"] = payload.get("ritual")
                old["data_probe"] = payload.get("data_probe")
                old["generated_at"] = payload.get("generated_at")
                old["market_outlook"] = payload.get("market_outlook")
                old["stats"] = payload.get("stats")
                old["predict_for"] = payload.get("predict_for")
                path = write_cloud_state(old)
                print(
                    f"[garden_cloud_cron] empty scan, kept previous "
                    f"a_picks={old_n} global={old_gn} ritual updated"
                )
                maybe_webhook(old)
                return 0
        except Exception as exc:
            print(f"[garden_cloud_cron] keep-previous skip: {exc}")
    path = write_cloud_state(payload)
    print(f"[garden_cloud_cron] wrote {path}")
    maybe_webhook(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
