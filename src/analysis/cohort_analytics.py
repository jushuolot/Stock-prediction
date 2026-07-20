"""多人选股汇总：合并各用户画像与标的共识。"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.analysis.user_pick_profile import UserPickProfile, build_user_pick_profile


@dataclass(frozen=True)
class CohortInsights:
    generated_at: str
    user_count: int
    users: tuple[dict[str, Any], ...]
    stock_consensus: tuple[dict[str, Any], ...]
    pattern_totals: dict[str, int]
    summary_lines: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "user_count": self.user_count,
            "users": list(self.users),
            "stock_consensus": list(self.stock_consensus),
            "pattern_totals": dict(self.pattern_totals),
            "summary_lines": list(self.summary_lines),
        }


def build_cohort_insights(contributions: list[dict[str, Any]]) -> CohortInsights:
    """从各用户 cloud contribution 合并。"""
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if not contributions:
        return CohortInsights(
            generated_at=now,
            user_count=0,
            users=(),
            stock_consensus=(),
            pattern_totals={},
            summary_lines=("尚无多人云端数据",),
        )

    users_out: list[dict[str, Any]] = []
    stock_users: dict[str, set[str]] = defaultdict(set)
    stock_names: dict[str, str] = {}
    stock_mentions: Counter[str] = Counter()
    pattern_totals: Counter[str] = Counter()

    for c in contributions:
        uid = str(c.get("user_id") or "unknown")
        profile = c.get("profile") or {}
        users_out.append(
            {
                "user_id": uid,
                "style": profile.get("style_label") or "—",
                "hit_rate_pct": profile.get("hit_rate_pct"),
                "top_patterns": profile.get("top_patterns") or [],
                "top_codes": profile.get("top_codes") or [],
                "watch_count": profile.get("watch_count", 0),
                "pick_count": profile.get("pick_count", 0),
                "updated_at": c.get("updated_at"),
            }
        )
        for pat in profile.get("top_patterns") or []:
            pattern_totals[str(pat)] += 1
        for code in (profile.get("top_codes") or []) + (c.get("recent_picks") or []):
            code_s = str(code).zfill(6) if str(code).isdigit() and len(str(code)) <= 6 else str(code)
            stock_mentions[code_s] += 1
            stock_users[code_s].add(uid)
            for item in c.get("watchlist_hint") or []:
                if str(item.get("代码") or "") == code_s:
                    stock_names[code_s] = str(item.get("名称") or code_s)

    consensus: list[dict[str, Any]] = []
    for code, n in stock_mentions.most_common(15):
        uids = stock_users.get(code) or set()
        consensus.append(
            {
                "代码": code,
                "名称": stock_names.get(code, ""),
                "提及次数": n,
                "关注人数": len(uids),
                "用户": sorted(uids)[:6],
            }
        )

    lines: list[str] = []
    lines.append(f"共 {len(users_out)} 位用户画像已汇总")
    if consensus:
        top = consensus[0]
        lines.append(
            f"最热共识：{top.get('名称') or top.get('代码')}（{top.get('关注人数')}人关注）"
        )
    if pattern_totals:
        p, cnt = pattern_totals.most_common(1)[0]
        lines.append(f"群体偏好模式：{p}（{cnt}人）")

    return CohortInsights(
        generated_at=now,
        user_count=len(users_out),
        users=tuple(users_out),
        stock_consensus=tuple(consensus),
        pattern_totals=dict(pattern_totals),
        summary_lines=tuple(lines),
    )


def profile_from_history_store(user_id: str, store: dict[str, Any]) -> UserPickProfile:
    latest = store.get("latest") or {}
    prefs = latest.get("user_prefs") or {}
    return build_user_pick_profile(
        user_id,
        pick_log=latest.get("pick_log") or store.get("pick_log"),
        watchlist=store.get("watchlist") or [],
        search_history=prefs.get("search_history") or [],
    )
