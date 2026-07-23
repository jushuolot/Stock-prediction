"""P116 佛祖每晚一页简报 — 打开花园先看结论。"""

from __future__ import annotations

from datetime import date
from typing import Any

from src.analysis.garden_cohort import cohort_brief_line, resolve_cohort_data
from src.util.app_meta import APP_VERSION, EVOLUTION_STEP


def build_nightly_brief(
    *,
    ritual: dict[str, Any] | None,
    predict_for: str,
    a_picks: list[dict[str, Any]],
    global_picks: list[dict[str, Any]],
    outlook: dict[str, Any] | None,
    hit_summary: dict[str, Any] | None,
    cloud_sync_at: str | None = None,
    strategy_hints: list[str] | None = None,
    macro_regime: dict[str, Any] | None = None,
    near_miss_summary: str | None = None,
    version: str = APP_VERSION,
    step: int = EVOLUTION_STEP,
) -> dict[str, Any]:
    """生成花园顶栏「今晚查岗」结构化简报。"""
    fresh = bool((ritual or {}).get("data_fresh"))
    level = str((ritual or {}).get("ritual_level") or ("green" if fresh else "red"))
    bar = (ritual or {}).get("data_bar_date") or "—"
    src = (ritual or {}).get("data_source") or "—"

    buy_n = sum(
        1
        for p in a_picks
        if str(p.get("signal") or "") in ("买入", "明日偏多", "buy")
    )
    prob = float((outlook or {}).get("crash_prob_1_2w_pct") or 0)
    o2w = str((outlook or {}).get("outlook_2w") or "—")[:16]
    advice = str((outlook or {}).get("advice") or "")[:120]
    regime_label = str((macro_regime or {}).get("label") or "")
    risk_budget = (macro_regime or {}).get("risk_budget")

    hit_rate = (hit_summary or {}).get("rate_pct")
    hit_src = (hit_summary or {}).get("source")
    hit_label = (hit_summary or {}).get("label") or "尚无到期验证"
    if hit_src == "cloud" and hit_label != "尚无到期验证记录":
        hit_label = f"云端{hit_label}"

    nm = (near_miss_summary or "").strip()

    if not fresh:
        action = "数据未达今日标准，请勿采信推荐；等收盘后或明日再开。"
        mood = "red"
    elif not a_picks and not global_picks:
        action = (
            f"今日暂无达标推荐；{nm}。"
            if nm
            else "今日暂无达标推荐；可点「预测明日」或等晚间自动扫盘。"
        )
        mood = "yellow"
    elif regime_label == "防守" or prob >= 55:
        action = f"防守体制（大跌概率 {prob:.0f}%）：轻仓、偏观望，勿追高。"
        mood = "yellow"
    elif buy_n >= 1:
        action = f"可看 A 股 {buy_n} 只「明日偏多」；结合大盘 {prob:.0f}% 大跌概率决策。"
        mood = "green"
    else:
        action = f"以观望为主；全球 {len(global_picks)} 只仅作关注。"
        mood = "green" if fresh else "yellow"

    lines = [
        f"**版本** v{version} · 进化 {step} 步",
        f"**行情截止** {bar} · {src} · {'✅新鲜' if fresh else '❌滞后'}",
        f"**明日目标** {predict_for} · A股 **{len(a_picks)}** · 全球 **{len(global_picks)}** · 偏多 **{buy_n}**",
        f"**大盘** 1~2周大跌概率 **{prob:.0f}%** · {o2w}",
        f"**成绩单** {hit_label}" + (f" · 命中率 **{hit_rate:.0f}%**" if hit_rate is not None else ""),
    ]
    if nm:
        lines.append(f"**近失** {nm}")
    if regime_label:
        rb = f" · 风险预算 {float(risk_budget):.0%}" if risk_budget is not None else ""
        lines.append(f"**体制** {regime_label}{rb} · {(macro_regime or {}).get('summary') or ''}")
    if cloud_sync_at:
        lines.append(f"**云端同步** {cloud_sync_at}")
    cohort_line = cohort_brief_line(resolve_cohort_data())
    if cohort_line:
        lines.append(cohort_line)
    for hint in (strategy_hints or [])[:4]:
        lines.append(f"**复盘** {hint}" if not str(hint).startswith("**") else hint)

    return {
        "as_of": date.today().isoformat(),
        "predict_for": predict_for,
        "mood": mood,
        "action": action,
        "lines": lines,
        "markdown": "\n\n".join(["# 🪷 佛祖今晚查岗", "", *lines, "", f"**建议：** {action}", "", "*规则预测，非投资建议。*"]),
    }


def brief_to_markdown(brief: dict[str, Any]) -> str:
    return str(brief.get("markdown") or "")
