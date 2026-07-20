"""单股全维档案 + 可读结论（P125：搜一只讲清楚）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable

import pandas as pd

from src.analysis.pick_tracker import normalize_pick_log
from src.analysis.signals import add_indicators, score_stock
from src.analysis.stock_quality import QualityVerdict, evaluate_stock_quality
from src.analysis.tomorrow_picks import analyze_tomorrow_from_kline
from src.analysis.quick_analyze import analyze_watch_light
from src.providers.eastmoney import SearchHit
from src.util.watchlist_add import hit_to_watchlist_item

FetchFn = Callable[..., tuple[Any, str]]


@dataclass(frozen=True)
class StockDossier:
    code: str
    name: str
    market: str
    verdict: str
    bullets: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    markdown: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "market": self.market,
            "verdict": self.verdict,
            "bullets": list(self.bullets),
            "rows": list(self.rows),
            "markdown": self.markdown,
        }


def _pick_rows_for_code(code: str, pick_log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    c6 = str(code).zfill(6)
    return [r for r in normalize_pick_log(pick_log) if str(r.get("code") or "").zfill(6) == c6]


def _verdict_label(score: float | None, qv: QualityVerdict | None, tomorrow_sig: str) -> str:
    if tomorrow_sig == "明日偏多":
        base = "偏多"
    elif tomorrow_sig == "明日观望":
        base = "观望"
    else:
        base = "中性"
    if qv and not qv.ok:
        return f"回避（{qv.reject_reason[:20]}）"
    if score is not None and score >= 75:
        return f"谨慎{base}"
    if score is not None and score < 55:
        return "偏弱"
    return base


def build_stock_dossier(
    hit: SearchHit,
    fetch_fn: FetchFn,
    pick_log: list[dict[str, Any]] | None = None,
    *,
    pattern_adj: dict[str, float] | None = None,
) -> StockDossier:
    item = hit_to_watchlist_item(hit)
    code = str(item.get("代码") or hit.code)
    name = str(item.get("名称") or hit.name)
    market = str(hit.market or "")

    price = pct = score = None
    one_line = "—"
    try:
        snap = analyze_watch_light(item, fetch_fn, days=90)
        price, pct, score, one_line = snap.price, snap.pct, snap.score, snap.one_line
    except Exception as exc:
        one_line = f"行情暂不可用：{exc}"

    qv: QualityVerdict | None = None
    if hit.kind == "A" and str(hit.code).isdigit():
        qv = evaluate_stock_quality(str(hit.code).zfill(6))

    tomorrow_pat = ""
    tomorrow_sig = ""
    trend_note = "—"
    if hit.kind == "A":
        end = date.today()
        start = end - timedelta(days=120)
        try:
            df, _ = fetch_fn(item, start=start, end=end, kline="日线")
            if df is not None and not df.empty:
                ta = analyze_tomorrow_from_kline(df, today_pct=pct, pattern_adj=pattern_adj)
                if ta:
                    tomorrow_pat = ta.pattern
                    tomorrow_sig = ta.signal
                work = add_indicators(df)
                last = work.iloc[-1]
                ma20 = last.get("MA20")
                close = last.get("收盘")
                if ma20 is not None and close is not None:
                    trend_note = "站上MA20" if float(close) > float(ma20) else "MA20下方"
                try:
                    trend_note += f" · 技术{score_stock(df).total:.0f}分"
                except Exception:
                    pass
        except Exception:
            pass

    hist = _pick_rows_for_code(code, pick_log or [])
    pred_line = "未在系统预测记录中"
    if hist:
        last = hist[-1]
        d = str(last.get("pick_date") or "")[:10]
        if last.get("verified"):
            ok = "命中" if last.get("hit") else "未命中"
            ret = last.get("end_pct")
            ret_s = f"，3日最高 {ret:+.1f}%" if ret is not None else ""
            pred_line = f"{d} 预测「{last.get('signal') or '—'}」→ {ok}{ret_s}"
        else:
            pred_line = f"{d} 预测「{last.get('signal') or '—'}」（待验证）"

    quality_line = "—"
    if qv:
        if qv.ok:
            quality_line = "、".join(qv.tags[:4]) if qv.tags else "通过质量过滤"
            if qv.pe_ttm is not None:
                quality_line += f" · PE {qv.pe_ttm:.1f}"
            if qv.total_cap_yuan:
                quality_line += f" · 市值 {qv.total_cap_yuan / 1e8:.0f}亿"
        else:
            quality_line = qv.reject_reason

    bullets: list[str] = []
    bullets.append(f"**结论**：{_verdict_label(score, qv, tomorrow_sig)} · {one_line}")
    if tomorrow_pat:
        bullets.append(f"**明日模型**：{tomorrow_sig} · 模式「{tomorrow_pat}」")
    bullets.append(f"**质量/机构**：{quality_line}")
    bullets.append(f"**预测复盘**：{pred_line}")
    if pct is not None and score is not None:
        bullets.append(f"**今日**：{pct:+.2f}% · 综合技术 {score:.0f} 分 · {trend_note}")

    try:
        from src.analysis.quantum_style import (
            asymmetry_score,
            build_thesis,
            regime_from_outlook,
            size_hint,
        )

        import streamlit as st

        outlook = None
        try:
            outlook = st.session_state.get("market_outlook")
        except Exception:
            outlook = None
        regime = regime_from_outlook(outlook if isinstance(outlook, dict) else None)
        asym = asymmetry_score(pattern=tomorrow_pat or "未知", pct=pct, tech_score=score)
        thesis, invalidate = build_thesis(
            name=name,
            pattern=tomorrow_pat or "未知",
            signal=tomorrow_sig or "中性",
            regime=regime,
            one_line=one_line,
        )
        size = size_hint(regime=regime, signal=tomorrow_sig or "", asym=asym)
        bullets.append(f"**体制**：{regime.label} · 仓位建议 {size}")
        bullets.append(f"**论点**：{thesis}")
        bullets.append(f"**证伪**：若出现「{invalidate}」则论点失效")
    except Exception:
        pass

    table_rows = [
        {"维度": "行情", "要点": f"现价 {price if price is not None else '—'} · 涨跌 {pct:+.2f}%" if pct is not None else "—"},
        {"维度": "技术面", "要点": f"{score:.0f} 分 · {trend_note}" if score is not None else trend_note},
        {"维度": "质量", "要点": quality_line},
        {"维度": "明日预测", "要点": f"{tomorrow_sig or '—'} · {tomorrow_pat or '—'}"},
        {"维度": "历史预测", "要点": pred_line},
    ]
    if len(bullets) > 5:
        # 体制/论点/证伪已在 bullets 末尾
        for b in bullets[5:8]:
            if "体制" in b:
                table_rows.append({"维度": "宏观体制", "要点": b.replace("**体制**：", "")})
            elif "论点" in b:
                table_rows.append({"维度": "论点", "要点": b.replace("**论点**：", "")})
            elif "证伪" in b:
                table_rows.append({"维度": "证伪条件", "要点": b.replace("**证伪**：", "")})

    md_lines = [
        f"# {name} `{code}` · {market}",
        "",
        f"## {_verdict_label(score, qv, tomorrow_sig)}",
        "",
        *[f"- {b.replace('**', '')}" for b in bullets],
        "",
        "| 维度 | 要点 |",
        "|------|------|",
    ]
    for row in table_rows:
        md_lines.append(f"| {row['维度']} | {row['要点']} |")
    md_lines.extend(["", "*规则分析，非投资建议。*"])

    return StockDossier(
        code=code,
        name=name,
        market=market,
        verdict=_verdict_label(score, qv, tomorrow_sig),
        bullets=tuple(bullets[:8]),
        rows=tuple(table_rows),
        markdown="\n".join(md_lines),
    )
