"""P117+ 基本面 + 股东 + 基金持股质量过滤（配合明日预测，非投资建议）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.providers.eastmoney_f10 import fetch_industry_compare
from src.providers.eastmoney_fund_holdings import FundHoldingsSnapshot, fetch_fund_holdings_snapshot
from src.providers.eastmoney_shareholder import ShareholderSnapshot, fetch_shareholder_snapshot

# 总市值下限（元）：过滤过小、易被资金操纵的票
MIN_TOTAL_CAP_YUAN = 5e9  # 50 亿
# 创业板 / 科创板更严
MIN_TOTAL_CAP_GROWTH_YUAN = 8e9  # 80 亿


@dataclass(frozen=True)
class QualityVerdict:
    ok: bool
    score_delta: float
    tags: tuple[str, ...]
    reject_reason: str
    shareholder: dict[str, Any] | None
    fund_holdings: dict[str, Any] | None
    total_cap_yuan: float | None
    pe_ttm: float | None

    def reason_suffix(self) -> str:
        if not self.tags:
            return ""
        return " · 质量：" + "、".join(self.tags[:4])


def _board_penalty(code: str) -> tuple[float, str | None]:
    """主板略加分，创业板/科创板小票更谨慎。"""
    c = str(code).zfill(6)
    if c.startswith(("600", "601", "603", "605", "000", "001", "002")):
        return 2.0, "主板/中小板"
    if c.startswith(("300", "301")):
        return -4.0, "创业板"
    if c.startswith("688"):
        return -3.0, "科创板"
    if c.startswith(("8", "4")):
        return -6.0, "北交所"
    return 0.0, None


def _apply_fund_holdings(
    delta: float,
    tags: list[str],
    fh: FundHoldingsSnapshot,
) -> float:
    """公募基金 / QFII 新进、增减持 → 加减分。"""
    chg = fh.fund_chg
    if chg == "新进":
        delta += 5
        tags.append("公募基金新进")
    elif chg == "增仓":
        delta += 3
        tags.append("基金增仓")
    elif chg == "减仓":
        delta -= 5
        tags.append("基金减持")

    if fh.fund_ratio_chg is not None:
        if fh.fund_ratio_chg >= 0.3:
            delta += 2
            if "基金增仓" not in tags:
                tags.append("基金持股升")
        elif fh.fund_ratio_chg <= -0.5:
            delta -= 3
            tags.append("基金持股降")

    if fh.fund_count_chg is not None:
        if fh.fund_count_chg >= 5:
            delta += 2
            tags.append("基金家数增")
        elif fh.fund_count_chg <= -10:
            delta -= 4
            tags.append("基金家数减")

    qchg = fh.qfii_chg
    if qchg == "新进":
        delta += 4
        tags.append("QFII新进")
    elif qchg == "增仓":
        delta += 2
        tags.append("QFII增仓")
    elif qchg == "减仓":
        delta -= 3
        tags.append("QFII减持")

    if (
        fh.inst_net_chg_shares is not None
        and fh.inst_net_chg_shares < -3_000_000
        and chg in ("减仓", "—")
        and (fh.fund_ratio_chg or 0) <= -0.3
    ):
        delta -= 2
        tags.append("机构净流出")

    return delta


def evaluate_stock_quality(
    code: str,
    *,
    shareholder: ShareholderSnapshot | None = None,
    fund_holdings: FundHoldingsSnapshot | None = None,
    f10: dict[str, Any] | None = None,
    fetch_shareholder: bool = True,
    fetch_fund_holdings: bool = True,
    fetch_f10: bool = True,
) -> QualityVerdict:
    """股东 + 市值/PE/ROE 行业排名 → 是否纳入明日推荐。"""
    c = str(code).strip().zfill(6)
    sh = shareholder
    if sh is None and fetch_shareholder:
        sh = fetch_shareholder_snapshot(c)

    fh = fund_holdings
    if fh is None and fetch_fund_holdings:
        fh = fetch_fund_holdings_snapshot(c)

    fin = f10
    if fin is None and fetch_f10:
        fin = fetch_industry_compare(c)

    total_cap: float | None = None
    pe: float | None = None
    roe_rank: int | None = None
    industry_total = 0
    if fin and fin.get("ok"):
        cols = fin.get("columns") or []
        stock_row = next((r for r in (fin.get("rows") or []) if r.get("kind") == "stock"), None)
        rank_row = next((r for r in (fin.get("rows") or []) if r.get("kind") == "rank"), None)
        industry_total = int(fin.get("industry_total") or 0)
        if stock_row and cols:
            cells = stock_row.get("cells") or []
            try:
                cap_i = cols.index("总市值")
                pe_i = cols.index("市盈率(动)")
                raw_cap = cells[cap_i] if cap_i < len(cells) else ""
                if isinstance(raw_cap, str) and "亿" in raw_cap:
                    total_cap = float(raw_cap.replace("亿", "").replace(",", "").strip()) * 1e8
                pe_s = cells[pe_i] if pe_i < len(cells) else ""
                if pe_s and pe_s != "—":
                    pe = float(str(pe_s).replace(",", ""))
            except (ValueError, TypeError):
                pass
        if rank_row and cols:
            try:
                roe_i = cols.index("ROE")
                rk = rank_row.get("cells") or []
                cell = rk[roe_i] if roe_i < len(rk) else ""
                if cell and "|" in str(cell):
                    roe_rank = int(str(cell).split("|")[0])
            except (ValueError, TypeError):
                pass

    tags: list[str] = []
    delta = 0.0
    reject = ""

    bp, board_tag = _board_penalty(c)
    delta += bp
    if board_tag:
        tags.append(board_tag)

    if sh:
        if sh.holder_count is not None:
            if sh.holder_count >= 80_000:
                delta += 3
                tags.append("股东面广")
            elif sh.holder_count < 12_000:
                delta -= 5
                tags.append("股东过少")
        if sh.top1_ratio is not None:
            if sh.top1_locked and sh.top1_ratio >= 30:
                reject = f"第一大股东限售占比 {sh.top1_ratio:.1f}% 偏高"
            elif sh.top1_ratio >= 55:
                reject = f"第一大股东占比 {sh.top1_ratio:.1f}% 过高"
            elif 15 <= sh.top1_ratio <= 45 and not sh.top1_locked:
                delta += 2
                tags.append("控股适中")
        if sh.top3_ratio is not None and sh.top3_ratio >= 75:
            delta -= 4
            tags.append("前三股东集中")
        if sh.hold_focus == "非常集中" and (sh.holder_count or 0) < 20_000:
            delta -= 3
            tags.append("筹码过集中")
        if sh.holder_chg_pct is not None and sh.holder_chg_pct <= -8:
            delta -= 2
            tags.append("股东户数减少")

    if fh:
        delta = _apply_fund_holdings(delta, tags, fh)

    min_cap = MIN_TOTAL_CAP_GROWTH_YUAN if c.startswith(("300", "301", "688")) else MIN_TOTAL_CAP_YUAN
    if total_cap is not None:
        cap_yi = total_cap / 1e8
        tags.append(f"市值{cap_yi:.0f}亿")
        if total_cap < min_cap:
            reject = reject or f"总市值 {cap_yi:.1f}亿 低于门槛"
        elif total_cap >= 200e8:
            delta += 2

    if pe is not None:
        if pe <= 0:
            reject = reject or "市盈率为负"
        elif pe > 100:
            delta -= 6
            tags.append("PE偏高")
        elif pe > 60:
            delta -= 3
        elif 8 <= pe <= 40:
            delta += 2
            tags.append("PE合理")

    if roe_rank and industry_total >= 5:
        if roe_rank <= max(2, industry_total // 5):
            delta += 3
            tags.append("ROE行业靠前")
        elif roe_rank >= industry_total * 0.8:
            delta -= 3
            tags.append("ROE行业偏弱")

    ok = not reject
    return QualityVerdict(
        ok=ok,
        score_delta=round(delta, 1),
        tags=tuple(tags),
        reject_reason=reject,
        shareholder=sh.as_dict() if sh else None,
        fund_holdings=fh.as_dict() if fh else None,
        total_cap_yuan=total_cap,
        pe_ttm=pe,
    )
