"""A 股代码 → 交易所 / Yahoo 后缀（统一规则，避免 92xxxx 误标为 .SZ）。"""

from __future__ import annotations


def is_bj_code(code6: str) -> bool:
    c = str(code6).strip().zfill(6)
    return c.isdigit() and len(c) == 6 and (c[0] in ("4", "8") or c.startswith("92"))


def a_market_label(code6: str) -> str:
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return "其他"
    if c[0] == "6":
        return "沪市A股"
    if c[0] in ("0", "3"):
        return "深市A股"
    if is_bj_code(c):
        return "北交所"
    return "A股"


def yahoo_ticker_a(code6: str) -> str:
    """6 位 A 股代码 → Yahoo 代码（如 920161.BJ）。"""
    c = str(code6).strip().zfill(6)
    if not c.isdigit() or len(c) != 6:
        return ""
    if c[0] == "6":
        return f"{c}.SS"
    if c[0] in ("0", "3"):
        return f"{c}.SZ"
    if is_bj_code(c):
        return f"{c}.BJ"
    return f"{c}.SZ"
