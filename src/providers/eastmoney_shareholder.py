"""东财 F10 股东研究：十大股东 + 股东人数/集中度。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.providers.eastmoney import EM_HEADERS, _get
from src.providers.eastmoney_f10 import _f10_code

_PAGE = "https://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax"


@dataclass(frozen=True)
class ShareholderSnapshot:
    code: str
    holder_count: int | None
    hold_focus: str
    top1_name: str
    top1_ratio: float | None
    top1_locked: bool
    top3_ratio: float | None
    free_top_ratio: float | None
    holder_chg_pct: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "holder_count": self.holder_count,
            "hold_focus": self.hold_focus,
            "top1_name": self.top1_name,
            "top1_ratio": self.top1_ratio,
            "top1_locked": self.top1_locked,
            "top3_ratio": self.top3_ratio,
            "free_top_ratio": self.free_top_ratio,
            "holder_chg_pct": self.holder_chg_pct,
        }


def _f(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        x = float(v)
        return None if x != x else x
    except (TypeError, ValueError):
        return None


def _i(v: Any) -> int | None:
    f = _f(v)
    return int(f) if f is not None else None


def fetch_shareholder_snapshot(code6: str) -> ShareholderSnapshot | None:
    """拉取最新一期股东人数 + 前十股东占比（东财公开接口）。"""
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return None
    try:
        r = _get(
            _PAGE,
            params={"code": _f10_code(c)},
            headers={**EM_HEADERS, "Referer": "https://emweb.securities.eastmoney.com/"},
            timeout=18,
        )
        r.raise_for_status()
        payload = r.json()
    except Exception:
        return None

    gdrs = payload.get("gdrs")
    row_g = gdrs[0] if isinstance(gdrs, list) and gdrs else (gdrs if isinstance(gdrs, dict) else {})
    sdgd = payload.get("sdgd") or []
    top1 = sdgd[0] if isinstance(sdgd, list) and sdgd else {}

    top3 = 0.0
    has_top3 = False
    if isinstance(sdgd, list):
        for item in sdgd[:3]:
            r3 = _f(item.get("HOLD_NUM_RATIO"))
            if r3 is not None:
                top3 += r3
                has_top3 = True

    stype = str(top1.get("SHARES_TYPE") or "")
    return ShareholderSnapshot(
        code=c,
        holder_count=_i(row_g.get("HOLDER_TOTAL_NUM")),
        hold_focus=str(row_g.get("HOLD_FOCUS") or "—"),
        top1_name=str(top1.get("HOLDER_NAME") or "—")[:24],
        top1_ratio=_f(top1.get("HOLD_NUM_RATIO")),
        top1_locked=("限售" in stype),
        top3_ratio=round(top3, 2) if has_top3 else None,
        free_top_ratio=_f(row_g.get("FREEHOLD_RATIO_TOTAL")),
        holder_chg_pct=_f(row_g.get("TOTAL_NUM_RATIO")),
    )
