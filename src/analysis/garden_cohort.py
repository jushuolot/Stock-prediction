"""花园页多人选股数据与纯函数（P123）。"""

from __future__ import annotations

from typing import Any

from src.analysis.cohort_analytics import build_cohort_insights
from src.storage.cloud_contrib import load_all_contributions
from src.util.cloud_picks_loader import load_cohort_insights


def resolve_cohort_data() -> dict[str, Any] | None:
    cohort = load_cohort_insights()
    if not cohort:
        local = load_all_contributions()
        if local:
            cohort = build_cohort_insights(local).as_dict()
    return cohort


def _norm_code(code: str) -> str:
    c = str(code or "").strip()
    if c.isdigit() and len(c) <= 6:
        return c.zfill(6)
    return c.upper()


def cohort_note_for_code(cohort: dict[str, Any] | None, code: str) -> str:
    """透镜卡同伴提示，如「👥 2人也在关注」。"""
    if not cohort or not code:
        return ""
    target = _norm_code(code)
    for row in cohort.get("stock_consensus") or []:
        row_code = _norm_code(str(row.get("代码") or ""))
        if row_code != target:
            continue
        watchers = int(row.get("关注人数") or 0)
        if watchers >= 2:
            return f"👥 {watchers}人也在关注"
        if watchers == 1:
            return "👥 另有同伴关注"
    return ""


def format_top_consensus_lines(cohort: dict[str, Any], *, limit: int = 3) -> list[str]:
    """Top N 共识股票：代码/名称/关注人数。"""
    lines: list[str] = []
    for row in (cohort.get("stock_consensus") or [])[:limit]:
        code = str(row.get("代码") or "—")
        name = str(row.get("名称") or "").strip()
        watchers = int(row.get("关注人数") or 0)
        label = f"{code} {name}".strip() if name else code
        lines.append(f"{label} · {watchers}人关注")
    return lines


def build_cohort_strip_payload(cohort: dict[str, Any] | None) -> dict[str, Any]:
    """纯函数：组装花园条展示内容（便于单测）。"""
    if not cohort or not int(cohort.get("user_count") or 0):
        return {
            "has_data": False,
            "message": "云端尚无多人汇总；配置多组密码后，各用户使用后会在每晚扫盘合并分析。",
        }
    user_count = int(cohort.get("user_count") or 0)
    top_lines = format_top_consensus_lines(cohort, limit=3)
    return {
        "has_data": True,
        "user_count": user_count,
        "headline": f"共 {user_count} 位用户画像已汇总",
        "top_lines": top_lines,
        "detail_caption": "详情见专家模式 · 历史",
    }


def cohort_brief_line(cohort: dict[str, Any] | None) -> str:
    """佛祖简报一行：user_count>=2 时返回共识摘要。"""
    if not cohort or int(cohort.get("user_count") or 0) < 2:
        return ""
    stocks = cohort.get("stock_consensus") or []
    if stocks:
        top = stocks[0]
        name = str(top.get("名称") or top.get("代码") or "—")
        watchers = int(top.get("关注人数") or 0)
        return f"**同伴选股** {cohort['user_count']}人汇总 · 最热 {name}（{watchers}人关注）"
    return f"**同伴选股** {cohort['user_count']}人画像已汇总"
