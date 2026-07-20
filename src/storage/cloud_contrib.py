"""多人选股：本地上传贡献 + 可选 GitHub 同步到 cloud_state。"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.analysis.cohort_analytics import build_cohort_insights, profile_from_history_store
from src.analysis.user_pick_profile import build_user_pick_profile
from src.storage.paths import project_root

CONTRIB_DIR = project_root() / "cloud_state" / "user_contrib"
LOCAL_CONTRIB_DIR = project_root() / "data" / "cloud_contrib"
COHORT_JSON = project_root() / "cloud_state" / "cohort_insights.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_user_contribution(user_id: str, store: dict[str, Any]) -> dict[str, Any]:
    latest = store.get("latest") or {}
    prefs = latest.get("user_prefs") or {}
    pick_log = latest.get("pick_log") or []
    watchlist = store.get("watchlist") or []
    profile = build_user_pick_profile(
        user_id,
        pick_log=pick_log,
        watchlist=watchlist,
        search_history=prefs.get("search_history") or [],
    )
    recent_picks = [str(r.get("code") or "") for r in pick_log[-8:] if r.get("code")]
    watch_hint = [
        {"代码": str(w.get("代码") or ""), "名称": str(w.get("名称") or "")}
        for w in watchlist[:12]
        if w.get("代码")
    ]
    return {
        "user_id": user_id,
        "updated_at": _now_iso(),
        "profile": profile.as_dict(),
        "recent_picks": recent_picks,
        "watchlist_hint": watch_hint,
        "search_top": list(prefs.get("search_history") or [])[:8],
    }


def save_user_contribution_local(user_id: str, contrib: dict[str, Any]) -> Path:
    LOCAL_CONTRIB_DIR.mkdir(parents=True, exist_ok=True)
    CONTRIB_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(contrib, ensure_ascii=False, indent=2)
    p1 = LOCAL_CONTRIB_DIR / f"{user_id}.json"
    p2 = CONTRIB_DIR / f"{user_id}.json"
    p1.write_text(payload, encoding="utf-8")
    p2.write_text(payload, encoding="utf-8")
    return p2


def load_all_contributions() -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for base in (CONTRIB_DIR, LOCAL_CONTRIB_DIR):
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.json")):
            uid = p.stem
            if uid in seen:
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("user_id"):
                    out.append(data)
                    seen.add(uid)
            except (json.JSONDecodeError, OSError):
                continue
    return out


def aggregate_cohort_to_file() -> dict[str, Any]:
    contribs = load_all_contributions()
    insights = build_cohort_insights(contribs)
    payload = insights.as_dict()
    COHORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    COHORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def scan_local_user_histories() -> list[dict[str, Any]]:
    """扫描 data/users/*/user_history.json（同机多用户）。"""
    root = project_root() / "data" / "users"
    out: list[dict[str, Any]] = []
    if not root.is_dir():
        return out
    for hist in root.glob("*/user_history.json"):
        uid = hist.parent.name
        try:
            store = json.loads(hist.read_text(encoding="utf-8"))
            if not isinstance(store, dict):
                continue
            contrib = build_user_contribution(uid, store)
            save_user_contribution_local(uid, contrib)
            out.append(contrib)
        except (json.JSONDecodeError, OSError):
            continue
    return out


def try_push_contribution_github(user_id: str, contrib: dict[str, Any]) -> bool:
    token = os.environ.get("GITHUB_CONTRIB_TOKEN", "").strip()
    if not token:
        try:
            import streamlit as st

            token = str(st.secrets.get("GITHUB_CONTRIB_TOKEN") or "").strip()
        except Exception:
            pass
    if not token:
        return False
    repo = os.environ.get("GITHUB_CONTRIB_REPO", "jushuolot/jinshouzhi").strip()
    path = f"stock-assistant/cloud_state/user_contrib/{user_id}.json"
    content = json.dumps(contrib, ensure_ascii=False, indent=2).encode("utf-8")
    b64 = base64.b64encode(content).decode("ascii")
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    sha = None
    try:
        r0 = requests.get(url, headers=headers, timeout=15)
        if r0.status_code == 200:
            sha = (r0.json() or {}).get("sha")
    except Exception:
        pass
    body: dict[str, Any] = {
        "message": f"contrib: {user_id} pick profile",
        "content": b64,
    }
    if sha:
        body["sha"] = sha
    try:
        r = requests.put(url, headers=headers, json=body, timeout=25)
        return r.status_code in (200, 201)
    except Exception:
        return False


def sync_user_contribution(user_id: str, store: dict[str, Any], *, push_github: bool = True) -> dict[str, Any]:
    contrib = build_user_contribution(user_id, store)
    save_user_contribution_local(user_id, contrib)
    if push_github:
        try:
            import streamlit as st
            from datetime import datetime, timedelta

            last = st.session_state.get("_contrib_github_push_at")
            if last:
                try:
                    t0 = datetime.fromisoformat(str(last))
                    if datetime.now() - t0 < timedelta(hours=1):
                        push_github = False
                except ValueError:
                    pass
            if push_github:
                if try_push_contribution_github(user_id, contrib):
                    st.session_state["_contrib_github_push_at"] = datetime.now().isoformat(
                        timespec="seconds"
                    )
        except Exception:
            try_push_contribution_github(user_id, contrib)
    return contrib
