"""花园搜索透镜：单股简化体检卡（命中率 + 基金持股 + 对照价）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.analysis.pick_tracker import hit_rate_summary, normalize_pick_log
from src.analysis.quick_analyze import analyze_watch_light
from src.providers.eastmoney import SearchHit
from src.providers.eastmoney_fund_holdings import fetch_fund_holdings_snapshot
from src.providers.google_finance import (
    compare_prices,
    fetch_google_finance_quote,
    google_finance_symbol,
)
from src.analysis.garden_cohort import cohort_note_for_code, resolve_cohort_data
from src.util.watchlist_add import hit_to_watchlist_item

FetchFn = Callable[..., tuple[Any, str]]


@dataclass(frozen=True)
class GardenLensCard:
    code: str
    name: str
    market: str
    price: float | None
    pct: float | None
    score: float | None
    one_line: str
    fund_tags: str
    pick_history: str
    hit_rate_label: str
    google_note: str
    google_url: str
    cohort_note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "market": self.market,
            "price": self.price,
            "pct": self.pct,
            "score": self.score,
            "one_line": self.one_line,
            "fund_tags": self.fund_tags,
            "pick_history": self.pick_history,
            "hit_rate_label": self.hit_rate_label,
            "google_note": self.google_note,
            "google_url": self.google_url,
            "cohort_note": self.cohort_note,
        }


def _fund_tags_for_code(code6: str) -> str:
    c = str(code6).zfill(6)
    if not c.isdigit() or len(c) != 6:
        return "—"
    snap = fetch_fund_holdings_snapshot(c)
    if not snap:
        return "—"
    bits: list[str] = []
    if snap.fund_chg and snap.fund_chg != "—":
        bits.append(f"基金{snap.fund_chg}")
    if snap.qfii_chg and snap.qfii_chg not in ("—", "不变"):
        bits.append(f"QFII{snap.qfii_chg}")
    if snap.fund_count_chg is not None and snap.fund_count_chg <= -10:
        bits.append("基金家数减")
    elif snap.fund_count_chg is not None and snap.fund_count_chg >= 5:
        bits.append("基金家数增")
    return "、".join(bits[:3]) if bits else "—"


def _pick_history_line(hit: SearchHit, pick_log: list[dict[str, Any]]) -> str:
    code = str(hit.code or "").zfill(6) if hit.kind == "A" else str(hit.code or "")
    rows = [
        r
        for r in normalize_pick_log(pick_log)
        if str(r.get("code") or "").zfill(6) == code.zfill(6)
        or str(r.get("code") or "") == str(hit.yahoo or hit.code)
    ]
    if not rows:
        return "未在花园推荐过"
    last = rows[-1]
    d = str(last.get("pick_date") or "")[:10]
    if last.get("verified"):
        ok = "✅" if last.get("hit") else "❌"
        return f"{d} 推荐过 → 持有期{ok}"
    return f"{d} 推荐过（待验证）"


def build_garden_lens_card(
    hit: SearchHit,
    fetch_fn: FetchFn,
    pick_log: list[dict[str, Any]] | None = None,
    *,
    fetch_google: bool = True,
    cohort: dict[str, Any] | None = None,
) -> GardenLensCard:
    item = hit_to_watchlist_item(hit)
    code = str(item.get("代码") or hit.code)
    name = str(item.get("名称") or hit.name)
    try:
        snap = analyze_watch_light(item, fetch_fn, days=90)
        price, pct, score, one_line = snap.price, snap.pct, snap.score, snap.one_line
    except Exception as exc:
        price, pct, score = None, None, None
        one_line = f"行情暂不可用：{exc}"

    fund_tags = _fund_tags_for_code(hit.code) if hit.kind == "A" else "—"
    pick_hist = _pick_history_line(hit, pick_log or [])
    hr = hit_rate_summary(pick_log or [])
    hr_label = hr.get("label") or "尚无验证记录"
    if hr.get("rate_pct") is not None:
        hr_label = f"花园命中率 {hr['rate_pct']:.0f}%（{hr.get('hits', 0)}/{hr.get('total_verified', 0)}）"

    google_note = ""
    google_url = ""
    if fetch_google:
        sym = google_finance_symbol(hit)
        if sym:
            google_url = f"https://www.google.com/finance/quote/{sym}?hl=zh-CN"
            gq = fetch_google_finance_quote(sym)
            if gq:
                google_note = compare_prices(price, gq.price)
                if not google_note:
                    google_note = f"Google {gq.price:.2f}"

    cohort_data = cohort if cohort is not None else resolve_cohort_data()
    c_note = cohort_note_for_code(cohort_data, hit.code)

    return GardenLensCard(
        code=code,
        name=name,
        market=str(hit.market or ""),
        price=price,
        pct=pct,
        score=score,
        one_line=one_line,
        fund_tags=fund_tags,
        pick_history=pick_hist,
        hit_rate_label=hr_label,
        google_note=google_note,
        google_url=google_url,
        cohort_note=c_note,
    )
