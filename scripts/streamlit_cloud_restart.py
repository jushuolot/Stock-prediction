#!/usr/bin/env python3
"""Push 后可选：调用 Streamlit Community Cloud API 重启应用（需 GitHub Secrets）。"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def restart_streamlit_app(*, token: str, app_id: str) -> bool:
    url = f"https://api.streamlit.io/v1/apps/{app_id.strip()}/restart"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    print(f"[streamlit_restart] OK {resp.status}: {body[:200]}")
    return True


def main() -> int:
    token = os.environ.get("STREAMLIT_API_TOKEN", "").strip()
    app_id = os.environ.get("STREAMLIT_APP_ID", "").strip()
    if not token or not app_id:
        print(
            "[streamlit_restart] skip — 未配置 STREAMLIT_API_TOKEN / STREAMLIT_APP_ID "
            "（可选；Streamlit 也会在 git push 后自动部署）"
        )
        return 0
    try:
        restart_streamlit_app(token=token, app_id=app_id)
        return 0
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        print(f"[streamlit_restart] HTTP {exc.code}: {err[:400]}")
        return 1
    except Exception as exc:
        print(f"[streamlit_restart] FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
