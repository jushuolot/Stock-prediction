"""
资金结构「推测占比」——基于公开量价特征的规则模型，非交易所真实分单数据。

真实基金/散户/大单占比需 Level-2 或付费数据源；本模块输出供人工参考的估计值。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapitalMix:
    """各资金类型占比（合计约 100%）。"""
    fund_pct: float  # 公募基金等
    institution_pct: float  # 保险/社保/券商自营等机构
    large_account_pct: float  # 大客户/产业资本/北上等大资金
    hot_money_pct: float  # 游资/短线
    retail_pct: float  # 散户
    foreign_pct: float  # 外资/QFII 等（港美股权重更高）
    method: str
    notes: list[str]

    def as_dict(self) -> dict[str, float]:
        return {
            "公募基金%": self.fund_pct,
            "机构(保险社保等)%": self.institution_pct,
            "大客户/产业资本%": self.large_account_pct,
            "游资短线%": self.hot_money_pct,
            "散户%": self.retail_pct,
            "外资%": self.foreign_pct,
        }


def estimate_capital_mix(
    *,
    pct_change: float | None,
    turnover_pct: float | None,
    volume_ratio: float | None,
    amount: float | None = None,
    market: str = "A股",
    kind: str = "A",
) -> CapitalMix:
    """
    根据涨跌幅、换手率、量比等推测当日主导资金结构。
    """
    pct = float(pct_change or 0)
    turn = float(turnover_pct or 0)
    vr = float(volume_ratio or 1.0)
    notes: list[str] = []

    fund, inst, large, hot, retail, foreign = 15.0, 15.0, 15.0, 15.0, 25.0, 15.0

    if kind in ("US", "HK") or market in ("美股", "港股"):
        foreign += 20
        retail -= 10
        notes.append("港/美股：外资与全球机构权重上调。")

    if abs(pct) >= 7 and turn >= 8:
        hot += 25
        retail += 10
        fund -= 10
        inst -= 10
        notes.append("大涨大跌+高换手：游资与散户博弈成分上升。")
    elif abs(pct) >= 3 and 1.5 <= vr < 3:
        fund += 12
        inst += 8
        retail -= 12
        notes.append("温和放量趋势：公募/机构跟随行业逻辑可能性更高。")
    elif vr >= 2.5 and turn >= 5:
        hot += 18
        large += 8
        retail += 5
        fund -= 12
        notes.append("量比突出：短线资金与大户异动概率高。")
    elif vr < 0.7:
        inst += 10
        large += 8
        hot -= 15
        retail -= 8
        notes.append("缩量：观望为主，机构调仓多于散户追涨。")

    if turn >= 15:
        retail += 15
        hot += 5
        fund -= 8
        notes.append("极高换手：散户交易占比通常抬升。")

    if amount and amount > 5e8:
        large += 12
        inst += 5
        retail -= 8
        notes.append("成交额居前：大单与机构参与概率上升。")

    raw = [max(0, fund), max(0, inst), max(0, large), max(0, hot), max(0, retail), max(0, foreign)]
    s = sum(raw) or 1.0
    fund, inst, large, hot, retail, foreign = [round(x / s * 100, 1) for x in raw]

    return CapitalMix(
        fund_pct=fund,
        institution_pct=inst,
        large_account_pct=large,
        hot_money_pct=hot,
        retail_pct=retail,
        foreign_pct=foreign,
        method="公开量价规则模型（非真实分单）",
        notes=notes,
    )


def capital_mix_from_dict(d: Any) -> CapitalMix:
    """从 JSON / 百分比列名 / 已有 CapitalMix 恢复。"""
    if isinstance(d, CapitalMix):
        return d
    if not isinstance(d, dict):
        return estimate_capital_mix(pct_change=0, turnover_pct=0, volume_ratio=1.0)
    if "公募基金%" in d:
        return CapitalMix(
            fund_pct=float(d.get("公募基金%", 0)),
            institution_pct=float(d.get("机构(保险社保等)%", 0)),
            large_account_pct=float(d.get("大客户/产业资本%", 0)),
            hot_money_pct=float(d.get("游资短线%", 0)),
            retail_pct=float(d.get("散户%", 0)),
            foreign_pct=float(d.get("外资%", 0)),
            method=str(d.get("method") or "公开量价规则模型（非真实分单）"),
            notes=list(d.get("notes") or []),
        )
    return CapitalMix(
        fund_pct=float(d.get("fund_pct", 0)),
        institution_pct=float(d.get("institution_pct", 0)),
        large_account_pct=float(d.get("large_account_pct", 0)),
        hot_money_pct=float(d.get("hot_money_pct", 0)),
        retail_pct=float(d.get("retail_pct", 0)),
        foreign_pct=float(d.get("foreign_pct", 0)),
        method=str(d.get("method") or "公开量价规则模型（非真实分单）"),
        notes=list(d.get("notes") or []),
    )
