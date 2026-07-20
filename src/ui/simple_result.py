"""傻瓜化结论展示：一眼看懂涨跌幅、评分与一句话。"""

from __future__ import annotations

from typing import Any, Literal

import streamlit as st

from src.analysis.dashboard_stats import DashboardStats

VerdictLevel = Literal["good", "warn", "bad", "neutral"]


def plain_score_label(score: Any) -> str:
    if score is None:
        return "待分析"
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "待分析"
    if s >= 65:
        return "偏强"
    if s <= 40:
        return "偏弱"
    return "中性"


def plain_pct_label(pct: Any) -> str:
    if pct is None:
        return "涨跌未知"
    try:
        p = float(pct)
    except (TypeError, ValueError):
        return "涨跌未知"
    if p >= 3:
        return f"明显上涨 {p:+.2f}%"
    if p <= -3:
        return f"明显下跌 {p:+.2f}%"
    if p > 0:
        return f"小幅上涨 {p:+.2f}%"
    if p < 0:
        return f"小幅下跌 {p:+.2f}%"
    return "平盘 0.00%"


def overall_verdict(score: Any, pct: Any) -> tuple[str, str, VerdictLevel]:
    """返回 (结论标题, 补充说明, 展示级别)。"""
    sl = plain_score_label(score)
    pl = plain_pct_label(pct)
    if sl == "待分析":
        return "还没分析过", "请先点「刷新全部摘要」或「一键分析」", "neutral"
    if sl == "偏强" and (pct is None or float(pct) >= 0):
        return "整体偏强", f"评分偏强 · {pl}", "good"
    if sl == "偏弱" or (pct is not None and float(pct) <= -5):
        return "需要留意", f"评分偏弱 · {pl}", "bad"
    if sl == "中性":
        return "中性观望", f"评分中性 · {pl}", "warn"
    return "整体偏强" if sl == "偏强" else "需要留意", f"{sl} · {pl}", "warn" if sl == "偏强" else "bad"


def _render_box(title: str, body: str, level: VerdictLevel) -> None:
    text = f"**{title}**\n\n{body}"
    if level == "good":
        st.success(text)
    elif level == "bad":
        st.error(text)
    elif level == "warn":
        st.warning(text)
    else:
        st.info(text)


def render_stock_verdict_card(
    *,
    name: str,
    code: str,
    score: Any = None,
    pct: Any = None,
    one_line: str | None = None,
) -> None:
    """单只股票结论卡片（工作台选中标的时展示）。"""
    title, sub, level = overall_verdict(score, pct)
    lines = [f"**{name}（{code}）**", "", f"**结论：{title}**", sub]
    if score is not None:
        try:
            lines.append(f"- 综合评分：**{float(score):.1f}** / 100（{plain_score_label(score)}）")
        except (TypeError, ValueError):
            pass
    if pct is not None:
        lines.append(f"- 今日涨跌：**{plain_pct_label(pct)}**")
    ol = (one_line or "").strip()
    if ol and ol not in ("—", "暂无评分。"):
        lines.extend(["", f"**一句话：** {ol}"])
    _render_box("📌 这只股票怎么样？", "\n".join(lines), level)


def render_analysis_done(
    *,
    name: str,
    code: str,
    score: Any = None,
    pct: Any = None,
    one_line: str | None = None,
) -> None:
    """一键分析完成后的明确反馈。"""
    title, sub, level = overall_verdict(score, pct)
    body = (
        f"**{name}（{code}）** 分析已完成。\n\n"
        f"**结论：{title}** — {sub}\n\n"
        "向下滚动可查看 **K 线**、**行动路线** 与 **可读简报**；也可直接下载 `.md` 文件。"
    )
    ol = (one_line or "").strip()
    if ol and ol not in ("—", "暂无评分。"):
        body += f"\n\n**一句话：** {ol}"
    _render_box("✅ 分析完成", body, level)


def render_dashboard_verdict(stats: DashboardStats) -> None:
    if stats.watch_count <= 0:
        return
    parts: list[str] = [f"共 **{stats.watch_count}** 只自选"]
    if stats.up_count or stats.down_count:
        parts.append(f"**{stats.up_count}** 涨 · **{stats.down_count}** 跌")
    if stats.avg_score is not None:
        parts.append(f"平均评分 **{stats.avg_score:.1f}**（{plain_score_label(stats.avg_score)}）")
    if stats.alert_count:
        parts.append(f"⚠️ **{stats.alert_count}** 条提醒需关注")
    elif stats.snapshot_count >= stats.watch_count:
        parts.append("暂无提醒触发")
    line = " · ".join(parts)
    if stats.alert_count:
        st.warning(f"**今日自选概况** — {line}")
    else:
        st.info(f"**今日自选概况** — {line}")


def render_home_steps() -> None:
    """首页三步傻瓜指引。"""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**① 找股票**")
        st.caption("打开「② 发现标的」→ 输入名字或代码 → 点「加入自选」")
    with c2:
        st.markdown("**② 看结论**")
        st.caption("回到「① 自选分析」→ 刷新摘要或「一键分析」→ 看绿色/红色结论框")
    with c3:
        st.markdown("**③ 发同事**")
        st.caption("下载 `.md` 简报，或左侧「分享给同事」（需先部署公网）")


def render_search_result_banner(*, total: int, a: int, hk: int, us: int, other: int) -> None:
    if total <= 0:
        return
    bits = [f"找到 **{total}** 条结果"]
    bits.append(f"A股 **{a}** · 港股 **{hk}** · 美股 **{us}**")
    if other:
        bits.append(f"其他 **{other}**")
    st.success(" · ".join(bits) + "\n\n每行右侧点 **「加入自选」**，然后到 **① 自选分析** 查看。")


def render_brief_tldr(one_line: str | None, score: Any = None) -> None:
    """简报顶部的结论摘要。"""
    ol = (one_line or "").strip()
    if not ol or ol in ("—", "暂无评分。"):
        if score is not None:
            st.info(f"**结论摘要：** 综合评分 {float(score):.1f}，{plain_score_label(score)}。")
        return
    label = plain_score_label(score) if score is not None else ""
    head = f"**结论摘要：** {ol}"
    if label:
        head += f"（{label}）"
    st.info(head)
