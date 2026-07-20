#!/usr/bin/env python3
"""定时任务：从本地 history 生成每日作战清单 Markdown（P82）。

用法（cron / launchd）:
  cd stock-assistant
  export STOCK_USER='default'   # 多用户见 secrets [passwords] 键名
  python3 scripts/battle_plan_cron.py              # 写入 data/
  python3 scripts/battle_plan_cron.py --stdout     # 仅打印到 stdout
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.battle_plan import build_battle_plan  # noqa: E402
from src.storage.paths import history_file_path, project_root, safe_user_id  # noqa: E402


def load_store(user_id: str) -> dict:
    path = history_file_path(user_id=user_id)
    if not path.is_file():
        raise FileNotFoundError(f"无历史文件：{path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _alert_thresholds(store: dict) -> dict[str, float]:
    prefs = (store.get("latest") or {}).get("user_prefs") or {}
    return {
        "pct_up": float(prefs.get("alert_pct_up") or 5.0),
        "pct_down": float(prefs.get("alert_pct_down") or -5.0),
        "score_low": float(prefs.get("alert_score_low") or 40.0),
        "score_high": float(prefs.get("alert_score_high") or 65.0),
    }


def plan_output_path(*, user_id: str, now: datetime | None = None) -> Path:
    ref = now or datetime.now()
    stamp = ref.strftime("%Y%m%d")
    uid = safe_user_id(user_id)
    root = project_root()
    if uid == "default":
        out_dir = root / "data"
    else:
        out_dir = root / "data" / "users" / uid
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"battle_plan_{stamp}.md"


def main() -> int:
    user = os.environ.get("STOCK_USER", "default").strip() or "default"
    to_stdout = "--stdout" in sys.argv
    try:
        store = load_store(user)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    wl = store.get("watchlist") or []
    latest = store.get("latest") or {}
    snaps = latest.get("watch_snapshots") or {}
    prefs = latest.get("user_prefs") or {}
    thresholds = _alert_thresholds(store)
    md = build_battle_plan(
        wl,
        snaps,
        price_targets=prefs.get("price_targets") or {},
        **thresholds,
    )

    if to_stdout:
        print(md)
        return 0

    path = plan_output_path(user_id=user)
    path.write_text(md, encoding="utf-8")
    print(f"[battle_plan_cron] wrote {path} ({len(md.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
