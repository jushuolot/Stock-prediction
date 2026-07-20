"""单用户选股画像：从推荐记录、自选、搜索历史提炼特点。"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from src.analysis.pick_review import extract_pattern
from src.analysis.pick_tracker import hit_rate_summary, normalize_pick_log

_PATTERN_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class UserPickProfile:
    user_id: str
    style_label: str
    hit_rate_pct: float | None
    hit_summary: str
    top_patterns: tuple[str, ...]
    top_codes: tuple[str, ...]
    board_mix: dict[str, int]
    watch_count: int
    pick_count: int
    search_top: tuple[str, ...]
    notes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "style_label": self.style_label,
            "hit_rate_pct": self.hit_rate_pct,
            "hit_summary": self.hit_summary,
            "top_patterns": list(self.top_patterns),
            "top_codes": list(self.top_codes),
            "board_mix": dict(self.board_mix),
            "watch_count": self.watch_count,
            "pick_count": self.pick_count,
            "search_top": list(self.search_top),
            "notes": list(self.notes),
        }


def _board_bucket(code: str) -> str:
    c = str(code or "").zfill(6)
    if not c.isdigit():
        return "港美/其他"
    if c.startswith(("600", "601", "603", "605")):
        return "沪市主板"
    if c.startswith(("000", "001", "002")):
        return "深市主板"
    if c.startswith(("300", "301")):
        return "创业板"
    if c.startswith("688"):
        return "科创板"
    if c.startswith(("8", "4")):
        return "北交所"
    return "A股其他"


def _infer_style(board_mix: Counter[str], patterns: Counter[str]) -> str:
    if not board_mix and not patterns:
        return "尚无足够记录"
    top_board = board_mix.most_common(1)[0][0] if board_mix else ""
    top_pat = patterns.most_common(1)[0][0] if patterns else ""
    if board_mix.get("创业板", 0) + board_mix.get("科创板", 0) >= max(2, sum(board_mix.values()) // 2):
        base = "偏成长小盘"
    elif board_mix.get("沪市主板", 0) + board_mix.get("深市主板", 0) >= max(2, sum(board_mix.values()) // 2):
        base = "偏主板蓝筹"
    else:
        base = "均衡混合"
    if top_pat in ("突破在即",):
        return f"{base} · 爱追突破"
    if top_pat in ("强势回踩",):
        return f"{base} · 爱等回踩"
    if top_pat in ("趋势延续",):
        return f"{base} · 趋势跟随"
    return base


def build_user_pick_profile(
    user_id: str,
    *,
    pick_log: list[dict[str, Any]] | Any = None,
    watchlist: list[dict[str, Any]] | None = None,
    search_history: list[str] | None = None,
) -> UserPickProfile:
    picks = normalize_pick_log(pick_log or [])
    wl = list(watchlist or [])
    searches = [str(s).strip() for s in (search_history or []) if str(s).strip()]

    patterns: Counter[str] = Counter()
    codes: Counter[str] = Counter()
    boards: Counter[str] = Counter()

    for r in picks:
        code = str(r.get("code") or "")
        if code:
            codes[code] += 1
            boards[_board_bucket(code)] += 1
        pat = str(r.get("pattern") or "") or extract_pattern(
            str(r.get("reason") or ""), str(r.get("signal") or "")
        )
        if pat:
            patterns[pat] += 1

    for item in wl:
        code = str(item.get("代码") or "")
        if code:
            codes[code] += 1
            boards[_board_bucket(code)] += 1

    hr = hit_rate_summary(picks)
    notes: list[str] = []
    if picks and not hr.get("total_verified"):
        notes.append("推荐记录尚少，画像将随使用变准")
    if len(wl) >= 8:
        notes.append(f"自选较广（{len(wl)}只）")
    if patterns.get("突破在即", 0) >= 3:
        notes.append("多次出现突破模式")

    return UserPickProfile(
        user_id=user_id,
        style_label=_infer_style(boards, patterns),
        hit_rate_pct=hr.get("rate_pct"),
        hit_summary=str(hr.get("label") or ""),
        top_patterns=tuple(p for p, _ in patterns.most_common(3)),
        top_codes=tuple(c for c, _ in codes.most_common(5)),
        board_mix=dict(boards),
        watch_count=len(wl),
        pick_count=len(picks),
        search_top=tuple(searches[:6]),
        notes=tuple(notes[:4]),
    )
