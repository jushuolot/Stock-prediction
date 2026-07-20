"""双股对比（P16）：并排比较涨跌幅、评分与摘要字段。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StockCompareRow:
    code: str
    name: str
    pct: float | None
    score: float | None
    one_line: str
    fin_summary: str
    updated_at: str
    market: str = ""
    currency: str = ""


@dataclass(frozen=True)
class StockCompareResult:
    left: StockCompareRow
    right: StockCompareRow

    @property
    def pct_delta(self) -> float | None:
        if self.left.pct is None or self.right.pct is None:
            return None
        return round(self.left.pct - self.right.pct, 2)

    @property
    def score_delta(self) -> float | None:
        if self.left.score is None or self.right.score is None:
            return None
        return round(self.left.score - self.right.score, 1)


def _row_from_watch(item: dict[str, Any], snap: dict[str, Any]) -> StockCompareRow:
    code = str(item.get("代码") or "")
    name = str(item.get("名称") or code)

    def _f(key: str) -> float | None:
        v = snap.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    return StockCompareRow(
        code=code,
        name=name,
        pct=_f("pct"),
        score=_f("score"),
        one_line=str(snap.get("one_line") or "—").strip() or "—",
        fin_summary=str(snap.get("fin_summary") or "").strip(),
        updated_at=str(snap.get("updated_at") or "").strip(),
        market=str(item.get("市场") or ""),
        currency=str(item.get("货币") or ""),
    )


def compare_two_stocks(
    item_a: dict[str, Any],
    item_b: dict[str, Any],
    snap_a: dict[str, Any] | None,
    snap_b: dict[str, Any] | None,
) -> StockCompareResult:
    """对比两只自选：快照字段来自 watch_snapshots。"""
    return StockCompareResult(
        left=_row_from_watch(item_a, snap_a or {}),
        right=_row_from_watch(item_b, snap_b or {}),
    )


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:+.2f}%"


def _fmt_score(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:.1f}"


def compare_table_rows(result: StockCompareResult) -> list[dict[str, str]]:
    """供 Streamlit dataframe 使用的行列表。"""
    la, rb = result.left, result.right
    delta_pct = result.pct_delta
    delta_score = result.score_delta
    return [
        {"指标": "代码", "A": la.code, "B": rb.code, "差值(A-B)": ""},
        {"指标": "名称", "A": la.name, "B": rb.name, "差值(A-B)": ""},
        {"指标": "涨跌幅", "A": _fmt_pct(la.pct), "B": _fmt_pct(rb.pct), "差值(A-B)": _fmt_pct(delta_pct) if delta_pct is not None else "—"},
        {"指标": "评分", "A": _fmt_score(la.score), "B": _fmt_score(rb.score), "差值(A-B)": f"{delta_score:+.1f}" if delta_score is not None else "—"},
        {"指标": "一句话", "A": la.one_line, "B": rb.one_line, "差值(A-B)": ""},
        {"指标": "财务摘要", "A": la.fin_summary or "—", "B": rb.fin_summary or "—", "差值(A-B)": ""},
        {"指标": "市场", "A": la.market or "—", "B": rb.market or "—", "差值(A-B)": ""},
        {"指标": "货币", "A": la.currency or "—", "B": rb.currency or "—", "差值(A-B)": ""},
        {"指标": "摘要时间", "A": la.updated_at or "—", "B": rb.updated_at or "—", "差值(A-B)": ""},
    ]


def compare_to_markdown(result: StockCompareResult, *, title: str = "双股对比") -> str:
    la, rb = result.left, result.right
    lines = [
        f"# {title}",
        "",
        f"| 指标 | {la.name}（{la.code}） | {rb.name}（{rb.code}） | 差值(A-B) |",
        "| --- | --- | --- | --- |",
    ]
    for row in compare_table_rows(result):
        lines.append(f"| {row['指标']} | {row['A']} | {row['B']} | {row['差值(A-B)']} |")
    if result.pct_delta is not None or result.score_delta is not None:
        lines.extend(["", "## 小结", ""])
        if result.pct_delta is not None:
            lines.append(f"- 涨跌幅差：A 比 B {'高' if result.pct_delta >= 0 else '低'} {abs(result.pct_delta):.2f} 个百分点")
        if result.score_delta is not None:
            lines.append(f"- 评分差：A 比 B {'高' if result.score_delta >= 0 else '低'} {abs(result.score_delta):.1f} 分")
    lines.append("")
    return "\n".join(lines)
