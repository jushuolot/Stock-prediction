"""组合涨跌贡献（P70）：各标的加权贡献组合涨跌幅。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.util.watch_weights import pie_slices_for_watchlist


@dataclass(frozen=True)
class ContributionRow:
    code: str
    name: str
    pct: float | None
    weight_pct: float
    contribution_pts: float | None
    share_pct: float | None


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def compute_portfolio_contribution(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    weights: dict[str, float],
) -> tuple[float | None, list[ContributionRow]]:
    """返回 (组合加权涨跌幅%, 各标的贡献行)。权重来自 watch_weights 或等权。"""
    slices = pie_slices_for_watchlist(watchlist, weights)
    rows: list[ContributionRow] = []
    portfolio_pts = 0.0
    has_contrib = False

    for s in slices:
        code = str(s["code"])
        name = str(s["name"])
        weight_pct = float(s["pct"])
        snap = snapshots.get(code) or {}
        pct = _float_or_none(snap.get("pct"))
        contribution_pts: float | None = None
        if pct is not None and weight_pct > 0:
            contribution_pts = weight_pct / 100.0 * pct
            portfolio_pts += contribution_pts
            has_contrib = True
        rows.append(
            ContributionRow(
                code=code,
                name=name,
                pct=pct,
                weight_pct=weight_pct,
                contribution_pts=contribution_pts,
                share_pct=None,
            )
        )

    portfolio_pct = portfolio_pts if has_contrib else None
    if portfolio_pct is None or abs(portfolio_pct) < 1e-12:
        return portfolio_pct, rows

    enriched: list[ContributionRow] = []
    for r in rows:
        share: float | None = None
        if r.contribution_pts is not None:
            share = r.contribution_pts / portfolio_pct * 100.0
        enriched.append(
            ContributionRow(
                code=r.code,
                name=r.name,
                pct=r.pct,
                weight_pct=r.weight_pct,
                contribution_pts=r.contribution_pts,
                share_pct=share,
            )
        )
    enriched.sort(
        key=lambda x: abs(x.contribution_pts or 0.0),
        reverse=True,
    )
    return portfolio_pct, enriched


def contribution_table_rows(
    watchlist: list[dict[str, Any]],
    snapshots: dict[str, Any],
    weights: dict[str, float],
) -> tuple[float | None, list[dict[str, Any]]]:
    """UI 表格行：名称、代码、涨跌幅、权重%、贡献点、贡献占比%。"""
    portfolio_pct, rows = compute_portfolio_contribution(watchlist, snapshots, weights)
    table: list[dict[str, Any]] = []
    for r in rows:
        table.append(
            {
                "名称": r.name,
                "代码": r.code,
                "涨跌幅%": r.pct,
                "权重%": round(r.weight_pct, 2),
                "贡献点": round(r.contribution_pts, 4) if r.contribution_pts is not None else None,
                "贡献占比%": round(r.share_pct, 2) if r.share_pct is not None else None,
            }
        )
    return portfolio_pct, table
