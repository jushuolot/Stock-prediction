#!/usr/bin/env python3
"""汇总多人选股画像 → cloud_state/cohort_insights.json（GitHub Actions / 本地）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.storage.cloud_contrib import (  # noqa: E402
    aggregate_cohort_to_file,
    scan_local_user_histories,
)


def main() -> int:
    scan_local_user_histories()
    payload = aggregate_cohort_to_file()
    print(json.dumps({"user_count": payload.get("user_count"), "generated_at": payload.get("generated_at")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
