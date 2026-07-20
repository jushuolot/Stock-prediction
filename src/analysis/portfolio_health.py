"""自选组合健康分（P101）：均分、提醒比、陈旧比、板块分散度 → 0–100。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.dashboard_stats import compute_dashboard_stats
from src.analysis.sector_heatmap import UNKNOWN_SECTOR, aggregate_sector_distribution
from src.util.freshness_badge import is_stale

_LABEL_HEALTHY = "健康"
_LABEL_OK = "一般"
_LABEL_ATTENTION = "需关注"


@dataclass(frozen=True)
class PortfolioHealth:
    score: int
    label: str
    avg_score: float | None
    alert_ratio: float
    stale_ratio: float
    diversification: float
    sector_count: int
    watch_count: int


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _health_label(score: int) -> str:
    if score >= 70:
        return _LABEL_HEALTHY
    if score >= 45:
        return _LABEL_OK
    return _LABEL_ATTENTION


def _diversification_score(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> tuple[float, int]:
    """返回 (0–1 分散度, 有效板块数)。单板块或未知板块占比高则分散度低。"""
    n = len(watchlist)
    if n <= 0:
        return 0.0, 0
    if n == 1:
        return 0.0, 1
    buckets = aggregate_sector_distribution(
        watchlist,
        snapshots,
        brief_for_code=brief_for_code,
    )
    known = [b for b in buckets if b.sector != UNKNOWN_SECTOR]
    sector_count = len(known) if known else len(buckets)
    shares = [b.count / n for b in buckets]
    hhi = sum(s * s for s in shares)
    # HHI 1/n（完全均匀）→ 1.0；HHI 1（单板块）→ 0.0
    even_hhi = 1.0 / n
    if hhi <= even_hhi:
        div = 1.0
    elif hhi >= 1.0:
        div = 0.0
    else:
        div = (1.0 - hhi) / (1.0 - even_hhi)
    return max(0.0, min(1.0, div)), sector_count


def compute_portfolio_health(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    *,
    stale_hours: float = 24.0,
    pct_up: float = 5.0,
    pct_down: float = -5.0,
    score_low: float = 40.0,
    score_high: float = 65.0,
    brief_for_code: Callable[[str], str | None] | None = None,
) -> PortfolioHealth:
    """综合 0–100 健康分与傻瓜标签（健康 / 一般 / 需关注）。"""
    watch_count = len(watchlist)
    if watch_count <= 0:
        return PortfolioHealth(
            score=0,
            label=_LABEL_ATTENTION,
            avg_score=None,
            alert_ratio=0.0,
            stale_ratio=0.0,
            diversification=0.0,
            sector_count=0,
            watch_count=0,
        )

    stats = compute_dashboard_stats(
        watchlist,
        snapshots,
        pct_up=pct_up,
        pct_down=pct_down,
        score_low=score_low,
        score_high=score_high,
    )
    alert_ratio = stats.alert_count / watch_count if watch_count else 0.0

    stale_n = 0
    snap_n = 0
    for item in watchlist:
        code = str(item.get("代码") or "")
        snap = snapshots.get(code) or {}
        if not snap:
            continue
        snap_n += 1
        if is_stale(snap.get("updated_at"), stale_hours=stale_hours):
            stale_n += 1
    stale_ratio = stale_n / snap_n if snap_n else 1.0

    diversification, sector_count = _diversification_score(
        watchlist,
        snapshots,
        brief_for_code=brief_for_code,
    )

    avg_component = stats.avg_score if stats.avg_score is not None else 50.0
    alert_component = max(0.0, 100.0 * (1.0 - min(1.0, alert_ratio)))
    stale_component = max(0.0, 100.0 * (1.0 - min(1.0, stale_ratio)))
    div_component = diversification * 100.0

    raw = (
        avg_component * 0.40
        + alert_component * 0.25
        + stale_component * 0.20
        + div_component * 0.15
    )
    score = int(round(max(0.0, min(100.0, raw))))

    return PortfolioHealth(
        score=score,
        label=_health_label(score),
        avg_score=stats.avg_score,
        alert_ratio=round(alert_ratio, 4),
        stale_ratio=round(stale_ratio, 4),
        diversification=round(diversification, 4),
        sector_count=sector_count,
        watch_count=watch_count,
    )


def portfolio_health_markdown(health: PortfolioHealth) -> str:
    """Markdown 段落，供工作台 expander 展示。"""
    avg_txt = f"{health.avg_score:.1f}" if health.avg_score is not None else "—"
    return (
        f"### 自选健康分：**{health.score}** · {health.label}\n\n"
        f"| 维度 | 数值 |\n"
        f"|------|------|\n"
        f"| 均分 | {avg_txt} |\n"
        f"| 提醒占比 | {health.alert_ratio * 100:.0f}% |\n"
        f"| 数据陈旧占比 | {health.stale_ratio * 100:.0f}% |\n"
        f"| 板块分散度 | {health.diversification * 100:.0f}%（{health.sector_count} 个板块） |\n"
        f"| 自选数量 | {health.watch_count} |\n\n"
        f"*健康分由均分 40% + 低提醒 25% + 数据新鲜 20% + 板块分散 15% 加权；非投资建议。*"
    )
