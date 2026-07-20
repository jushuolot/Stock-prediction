#!/usr/bin/env python3
"""定时任务：从本地 history 生成周报 Markdown（P50）。

用法（cron / launchd）:
  cd stock-assistant
  export STOCK_USER='default'   # 多用户见 secrets [passwords] 键名
  python3 scripts/weekly_report_cron.py              # 写入 data/
  python3 scripts/weekly_report_cron.py --stdout     # 仅打印到 stdout
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

from src.analysis.weekly_report import build_weekly_report  # noqa: E402
from src.storage.paths import history_file_path, project_root, safe_user_id  # noqa: E402


def load_store(user_id: str) -> dict:
    path = history_file_path(user_id=user_id)
    if not path.is_file():
        raise FileNotFoundError(f"无历史文件：{path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def report_output_path(*, user_id: str, now: datetime | None = None) -> Path:
    ref = now or datetime.now()
    stamp = ref.strftime("%Y%m%d")
    uid = safe_user_id(user_id)
    root = project_root()
    if uid == "default":
        out_dir = root / "data"
    else:
        out_dir = root / "data" / "users" / uid
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"weekly_report_{stamp}.md"


def main() -> int:
    user = os.environ.get("STOCK_USER", "default").strip() or "default"
    to_stdout = "--stdout" in sys.argv
    try:
        store = load_store(user)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    latest = store.get("latest") or {}
    md = build_weekly_report(
        store.get("query_log") or [],
        store.get("watchlist") or [],
        latest.get("watch_snapshots") or {},
        days=7,
    )

    if to_stdout:
        print(md)
        return 0

    path = report_output_path(user_id=user)
    path.write_text(md, encoding="utf-8")
    print(f"[weekly_report_cron] wrote {path} ({len(md.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
