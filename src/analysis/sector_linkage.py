"""自选股板块联动分析（P7）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd


@dataclass(frozen=True)
class SectorLink:
    plate_code: str
    plate_name: str
    stocks: tuple[str, ...]
    pct: float | None

    @property
    def count(self) -> int:
        return len(self.stocks)


def _is_a_item(item: dict) -> bool:
    kind = str(item.get("类型") or "A")
    code = str(item.get("代码") or "").strip()
    return kind == "A" and code.replace(".", "").isdigit()


def analyze_plate_rows(rows: list[dict]) -> dict[str, dict]:
    """plate_code -> {name, stocks:set, pcts:list}"""
    acc: dict[str, dict] = {}
    for row in rows:
        code = str(row.get("stock_code") or "")
        name = str(row.get("stock_name") or code)
        plate_code = str(row.get("plate_code") or "")
        plate_name = str(row.get("plate_name") or plate_code)
        if not plate_code:
            continue
        slot = acc.setdefault(
            plate_code,
            {"name": plate_name, "stocks": set(), "pcts": []},
        )
        slot["stocks"].add(f"{name}({code})")
        pct = row.get("pct")
        if pct is not None:
            try:
                slot["pcts"].append(float(pct))
            except (TypeError, ValueError):
                pass
    return acc


def links_from_accumulator(acc: dict[str, dict], *, min_stocks: int = 2) -> list[SectorLink]:
    out: list[SectorLink] = []
    for plate_code, data in acc.items():
        stocks = tuple(sorted(data.get("stocks") or []))
        if len(stocks) < min_stocks:
            continue
        pcts = data.get("pcts") or []
        avg_pct = sum(pcts) / len(pcts) if pcts else None
        out.append(
            SectorLink(
                plate_code=plate_code,
                plate_name=str(data.get("name") or plate_code),
                stocks=stocks,
                pct=avg_pct,
            )
        )
    out.sort(key=lambda x: (-x.count, -(x.pct or 0)))
    return out


def build_linkage_alerts(links: list[SectorLink], *, hot_pct: float = 3.0) -> list[str]:
    alerts: list[str] = []
    for link in links:
        names = "、".join(link.stocks[:4])
        extra = f" 等{link.count}只" if link.count > 4 else ""
        pct_s = f"，板块均涨 {link.pct:+.2f}%" if link.pct is not None else ""
        tag = "🔥" if link.pct is not None and link.pct >= hot_pct else "🔗"
        alerts.append(f"{tag} **{link.plate_name}**：{names}{extra}{pct_s}")
    return alerts


def scan_watchlist_sector_linkage(
    watchlist: list[dict],
    fetch_plates: Callable[[str], pd.DataFrame],
    *,
    max_stocks: int = 10,
    plates_per_stock: int = 12,
) -> list[SectorLink]:
    """扫描 A 股自选所属板块，返回多股共用板块。"""
    rows: list[dict] = []
    scanned = 0
    for item in watchlist:
        if not _is_a_item(item):
            continue
        if scanned >= max_stocks:
            break
        code = str(item.get("代码") or "").split(".")[0].zfill(6)[:6]
        name = str(item.get("名称") or code)
        try:
            df = fetch_plates(code)
        except Exception:
            scanned += 1
            continue
        if df is None or df.empty:
            scanned += 1
            continue
        for _, r in df.head(plates_per_stock).iterrows():
            rows.append(
                {
                    "stock_code": code,
                    "stock_name": name,
                    "plate_code": str(r.get("板块代码") or ""),
                    "plate_name": str(r.get("名称") or ""),
                    "pct": r.get("涨跌幅%"),
                }
            )
        scanned += 1
    acc = analyze_plate_rows(rows)
    return links_from_accumulator(acc)
