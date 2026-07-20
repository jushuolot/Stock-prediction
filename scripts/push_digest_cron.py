#!/usr/bin/env python3
"""定时任务：从本地 history 推送自选股速览（P8，无需打开浏览器）。

用法（cron / launchd）:
  cd stock-assistant
  export STOCK_WEBHOOK_URL='https://hooks.example.com/...'
  # 或配置 SMTP 环境变量，见 docs/PUSH.md
  python3 scripts/push_digest_cron.py

仅在有提醒时推送:
  python3 scripts/push_digest_cron.py --alerts-only

附带重点提醒标的一页纸摘要:
  python3 scripts/push_digest_cron.py --with-onepager
  # 或 export STOCK_PUSH_ONEPAGER=1

附带作战优先级 Top 3:
  python3 scripts/push_digest_cron.py --with-priority
  # 或 export STOCK_PUSH_PRIORITY=1

一键全开（提醒 + 一页纸 + 优先关注）:
  python3 scripts/push_digest_cron.py --push-all
  # 或 export STOCK_PUSH_ALL=1

多用户:
  export STOCK_USER='alice'   # 对应 secrets [passwords] 的键名
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.daily_digest import build_watchlist_digest  # noqa: E402
from src.analysis.institutional_onepager import build_onepager_push_summary  # noqa: E402
from src.analysis.priority_queue import (  # noqa: E402
    format_priority_digest_section,
    rank_watchlist_priority,
)
from src.analysis.sector_relative import compute_sector_relative, sector_relative_for_ticker  # noqa: E402
from src.analysis.watch_alerts import compute_watch_alerts, top_alert_ticker  # noqa: E402
from src.notify.digest_push import push_digest_email, push_digest_webhook  # noqa: E402
from src.notify.email_digest import get_smtp_config  # noqa: E402
from src.notify.webhook import get_webhook_url  # noqa: E402
from src.storage.paths import history_file_path  # noqa: E402


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


def _push_all_enabled() -> bool:
    if "--push-all" in sys.argv:
        return True
    return os.environ.get("STOCK_PUSH_ALL", "").strip().lower() in ("1", "true", "yes")


def _onepager_enabled() -> bool:
    if _push_all_enabled():
        return True
    if "--with-onepager" in sys.argv:
        return True
    return os.environ.get("STOCK_PUSH_ONEPAGER", "").strip().lower() in ("1", "true", "yes")


def _priority_enabled() -> bool:
    if _push_all_enabled():
        return True
    if "--with-priority" in sys.argv:
        return True
    return os.environ.get("STOCK_PUSH_PRIORITY", "").strip().lower() in ("1", "true", "yes")


def _build_onepager_section(
    *,
    alerts: list,
    wl: list,
    snaps: dict,
) -> str:
    top = top_alert_ticker(alerts)
    if not top:
        return ""
    rel_rows = compute_sector_relative(wl, snaps)
    rel = sector_relative_for_ticker(rel_rows, top.code)
    snap = snaps.get(top.code) or {}
    return build_onepager_push_summary(
        name=top.name,
        code=top.code,
        snap=snap,
        sector_relative=rel,
        alert_message=top.message,
    )


def main() -> int:
    user = os.environ.get("STOCK_USER", "default").strip() or "default"
    dry = "--dry-run" in sys.argv
    alerts_only = "--alerts-only" in sys.argv
    push_all = _push_all_enabled()
    with_onepager = _onepager_enabled()
    with_priority = _priority_enabled()
    try:
        store = load_store(user)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    wl = store.get("watchlist") or []
    latest = store.get("latest") or {}
    snaps = latest.get("watch_snapshots") or {}
    prefs = latest.get("user_prefs") or {}
    notes = prefs.get("watch_notes") or {}
    if not wl:
        print("[push_digest_cron] 自选股为空，跳过")
        return 0
    thresholds = _alert_thresholds(store)
    alerts = compute_watch_alerts(wl, snaps, **thresholds)
    if alerts_only and not alerts:
        print("[push_digest_cron] --alerts-only: 无提醒，跳过")
        return 0
    priority_section = ""
    if with_priority:
        ranks = rank_watchlist_priority(wl, snaps, alerts=alerts, **thresholds, top_n=3)
        priority_section = format_priority_digest_section(ranks, top_n=3)
    digest = build_watchlist_digest(
        wl,
        snaps,
        alerts=alerts or None,
        watch_notes=notes,
        priority_section=priority_section,
        onepager_section=_build_onepager_section(alerts=alerts, wl=wl, snaps=snaps)
        if with_onepager
        else "",
    )
    if dry:
        print(
            f"[push_digest_cron] dry-run bytes={len(digest.encode('utf-8'))} "
            f"alerts={len(alerts)} alerts_only={alerts_only} push_all={push_all} "
            f"with_onepager={with_onepager} with_priority={with_priority}"
        )
        return 0

    from src.notify.retry import drain_queue, load_queue  # noqa: E402

    def _retry_handler(item: dict) -> tuple[bool, str]:
        d = str(item.get("digest") or digest)
        ch = str(item.get("channel") or "")
        ss_d = item.get("session") or {"watchlist": wl, "watch_snapshots": snaps, "_auth_user": user}

        class SS:
            def __init__(self, dct):
                self._d = dct

            def get(self, k, default=None):
                return self._d.get(k, default)

        ss = SS(ss_d)
        if ch == "webhook":
            return push_digest_webhook(digest=d, session_state=ss)
        if ch == "email":
            return push_digest_email(digest=d, session_state=ss)
        return False, "unknown"

    if load_queue(user_id=user):
        for line in drain_queue(_retry_handler, user_id=user, max_items=5):
            print(f"Retry: {line}")

    class _SS:
        def __init__(self) -> None:
            self._d = {
                "watchlist": wl,
                "watch_snapshots": snaps,
                "_auth_user": user,
            }

        def get(self, k, default=None):
            return self._d.get(k, default)

    ss = _SS()
    ok_any = False
    if get_webhook_url():
        ok, msg = push_digest_webhook(digest=digest, session_state=ss)
        print(f"Webhook: {'OK' if ok else 'FAIL'} {msg}")
        ok_any = ok_any or ok
    if get_smtp_config():
        ok, msg = push_digest_email(digest=digest, session_state=ss, alert_count=len(alerts))
        print(f"Email: {'OK' if ok else 'FAIL'} {msg}")
        ok_any = ok_any or ok
    if not get_webhook_url() and not get_smtp_config():
        print("[push_digest_cron] 未配置 STOCK_WEBHOOK_URL 或 SMTP")
        return 1
    return 0 if ok_any else 1


if __name__ == "__main__":
    raise SystemExit(main())
