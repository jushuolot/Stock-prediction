"""公开数据能力地图（P91/P94/P95）：侧边栏列出关键分析能力并支持快捷跳转。"""

from __future__ import annotations

import streamlit as st

from src.util.app_meta import EVOLUTION_STEP
from src.util.watch_expander_nav import capability_watch_href

CAPABILITY_ITEMS: list[tuple[str, str, str]] = [
    (
        "🏆 相对板块",
        "sector_relative",
        "自选内同板块均涨跌幅/均评分对比，工作台「相对板块」expander",
    ),
    (
        "📄 机构一页纸",
        "institutional_onepager",
        "结论/相对板块/风险/下一步 Markdown，可下载或 cron 推送",
    ),
    (
        "📋 作战清单",
        "battle_plan",
        "dashboard + alerts + Top 3 行动，历史页/工作台下载",
    ),
    (
        "🎯 优先关注",
        "priority_queue",
        "提醒/风险/板块综合排序 Top 5，首页与 digest 推送",
    ),
]

SECTION_KEY = "capability_map"
PLAYBOOK_PATH = "docs/PUBLIC_DATA_PLAYBOOK.md"


def capability_map_markdown(*, step: int = EVOLUTION_STEP) -> str:
    """能力地图 Markdown 正文（含 ?tab=watch&expand= 深链接）。"""
    lines = [
        f"基于公开行情数据的规则型能力（进化 step **{step}**）：",
        "",
    ]
    for title, module, desc in CAPABILITY_ITEMS:
        href = capability_watch_href(module)
        lines.append(f"- **[{title}]({href})** · `{module}` — {desc}")
    lines.extend(
        [
            "",
            f"📖 完整作战手册：[PUBLIC_DATA_PLAYBOOK.md]({PLAYBOOK_PATH})",
            "",
            "*以上均为整理型输出，非投资建议。*",
        ]
    )
    return "\n".join(lines)


def render_capability_map_sidebar(*, expanded: bool = False) -> None:
    """侧边栏「公开数据能力地图」expander。"""
    with st.expander("公开数据能力地图", expanded=expanded):
        st.markdown(capability_map_markdown())
        st.markdown(f"[📖 公开数据作战手册]({PLAYBOOK_PATH})")
