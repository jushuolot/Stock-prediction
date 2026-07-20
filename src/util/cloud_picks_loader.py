"""读取 GitHub Actions 写入的 cloud_state；Streamlit Cloud 运行时拉 GitHub 最新 JSON。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.util.cloud_runtime import is_streamlit_cloud

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "cloud_state" / "latest_picks.json"
COHORT = ROOT / "cloud_state" / "cohort_insights.json"
CLOUD_PICK_LOG = ROOT / "cloud_state" / "cloud_pick_log.json"
DEFAULT_RAW_URL = (
    "https://raw.githubusercontent.com/jushuolot/jinshouzhi/main/"
    "stock-assistant/cloud_state/latest_picks.json"
)
DEFAULT_COHORT_URL = (
    "https://raw.githubusercontent.com/jushuolot/jinshouzhi/main/"
    "stock-assistant/cloud_state/cohort_insights.json"
)
REMOTE_TTL_SEC = 300


def _cloud_state_url() -> str:
    env_url = os.environ.get("STOCK_CLOUD_STATE_URL", "").strip()
    if env_url:
        return env_url
    try:
        import streamlit as st

        secret_url = st.secrets.get("STOCK_CLOUD_STATE_URL")
        if secret_url:
            return str(secret_url).strip()
    except Exception:
        pass
    return DEFAULT_RAW_URL


def _normalize_payload(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    if (
        not data.get("picks")
        and not data.get("global_picks")
        and not data.get("market_outlook")
        and not data.get("generated_at")
    ):
        return None
    return data


def _load_local(path: Path | None = None) -> dict[str, Any] | None:
    p = path or LATEST
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return _normalize_payload(data)


def _fetch_remote_json(url: str) -> dict[str, Any] | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "stock-assistant-cloud-loader/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _normalize_payload(data)


_remote_cache_fn = None


def _cached_remote_picks(url: str) -> dict[str, Any] | None:
    global _remote_cache_fn
    if _remote_cache_fn is None:
        try:
            import streamlit as st

            @st.cache_data(ttl=REMOTE_TTL_SEC, show_spinner=False)
            def _fetch(url_key: str) -> dict[str, Any] | None:
                try:
                    return _fetch_remote_json(url_key)
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
                    return None

            _remote_cache_fn = _fetch
        except Exception:
            _remote_cache_fn = False  # type: ignore[assignment]

    if callable(_remote_cache_fn):
        return _remote_cache_fn(url)
    try:
        return _fetch_remote_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _normalize_cohort(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict) or not data.get("generated_at"):
        return None
    return data


def load_cohort_insights(path: Path | None = None, *, prefer_remote: bool | None = None) -> dict[str, Any] | None:
    p = path or COHORT
    use_remote = is_streamlit_cloud() if prefer_remote is None else prefer_remote
    if use_remote:
        url = os.environ.get("STOCK_COHORT_URL", "").strip() or DEFAULT_COHORT_URL
        try:
            remote = _fetch_remote_json(url)
            if remote and _normalize_cohort(remote):
                return remote
        except Exception:
            pass
    if p.is_file():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return _normalize_cohort(data)
        except (json.JSONDecodeError, OSError):
            pass
    return None


def load_cloud_pick_summary(*, prefer_remote: bool | None = None) -> dict[str, Any] | None:
    """云端推荐成绩单摘要（含命中率与复盘提示）。"""
    use_remote = is_streamlit_cloud() if prefer_remote is None else prefer_remote
    if use_remote:
        cloud = load_cloud_picks(prefer_remote=True)
        if cloud and cloud.get("hit_summary"):
            return {
                "hit_summary": cloud.get("hit_summary"),
                "strategy_hints": cloud.get("strategy_hints") or [],
            }
    if CLOUD_PICK_LOG.is_file():
        try:
            data = json.loads(CLOUD_PICK_LOG.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("hit_summary"):
                return {
                    "hit_summary": data.get("hit_summary"),
                    "strategy_hints": [],
                }
        except (json.JSONDecodeError, OSError):
            pass
    return None


def load_cloud_picks(path: Path | None = None, *, prefer_remote: bool | None = None) -> dict[str, Any] | None:
    """本地文件 +（云端）GitHub raw 热更新，无需 Reboot 即可看到 nightly 扫盘。"""
    use_remote = is_streamlit_cloud() if prefer_remote is None else prefer_remote
    if use_remote:
        remote = _cached_remote_picks(_cloud_state_url())
        if remote:
            return remote
    return _load_local(path)
