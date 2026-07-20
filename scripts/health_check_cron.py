#!/usr/bin/env python3
"""定时健康检查 + 可选告警（P14）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.notify.health_alert import maybe_send_health_alert  # noqa: E402
from src.ui.health_panel import _probe_eastmoney, _probe_yahoo  # noqa: E402


def main() -> int:
    probes = [
        {"name": r.name, "ok": r.ok, "detail": r.detail}
        for r in (_probe_eastmoney(), _probe_yahoo())
    ]
    failed = [p for p in probes if not p.get("ok")]
    for p in probes:
        icon = "OK" if p["ok"] else "FAIL"
        print(f"{icon} {p['name']}: {p['detail']}")
    app_url = os.environ.get("STOCK_APP_PUBLIC_URL", "")
    ok, msg = maybe_send_health_alert(probes, app_url=app_url)
    if ok:
        print(f"ALERT sent: {msg}")
    elif failed:
        print(f"ALERT skip: {msg}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
