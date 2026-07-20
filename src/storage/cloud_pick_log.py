"""云端推荐成绩单：GitHub nightly 写入，跨终端共享命中率（P124）。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Callable

from src.analysis.prediction_calibration import (
    build_calibration_report,
    load_calibration_adjustments,
    merge_pick_logs,
    verify_log_with_kline,
)
from src.analysis.pick_tracker import (
    append_today_picks,
    hit_rate_summary,
    normalize_pick_log,
)
from src.storage.paths import project_root

CLOUD_PICK_LOG = project_root() / "cloud_state" / "cloud_pick_log.json"


def load_cloud_pick_log(path: Path | None = None) -> list[dict[str, Any]]:
    p = path or CLOUD_PICK_LOG
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, dict):
        return normalize_pick_log(data.get("records") or [])
    return normalize_pick_log(data)


def save_cloud_pick_log(log: list[dict[str, Any]], *, path: Path | None = None) -> Path:
    p = path or CLOUD_PICK_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": date.today().isoformat(),
        "records": normalize_pick_log(log)[-200:],
        "hit_summary": hit_rate_summary(log),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


FetchRankingFn = Callable[[], tuple[Any, str]]
FetchFn = Callable[..., tuple[Any, str]]


def sync_cloud_pick_log(
    picks: list[Any],
    *,
    pick_day: str,
    fetch_fn: FetchFn,
    path: Path | None = None,
) -> dict[str, Any]:
    """追加今日推荐、K 线验证到期记录、写盘并返回元数据。"""
    log = load_cloud_pick_log(path=path)
    log = append_today_picks(log, picks, day=pick_day)
    try:
        log = verify_log_with_kline(log, fetch_fn)
    except Exception:
        pass
    save_cloud_pick_log(log, path=path)
    summary = hit_rate_summary(log)
    summary["source"] = "cloud"
    try:
        cal = build_calibration_report(log, fetch_fn).as_dict()
    except Exception:
        cal = None
    hints = list((cal or {}).get("conclusions") or [])[:6]
    return {"log": log, "hit_summary": summary, "strategy_hints": hints, "calibration": cal}


def load_cloud_pick_meta(path: Path | None = None) -> dict[str, Any] | None:
    p = path or CLOUD_PICK_LOG
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data
