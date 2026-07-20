"""公开数据作战手册内置预览（P97）：侧边栏展示手册关键章节摘要。"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.storage.paths import project_root
from src.ui.capability_map import PLAYBOOK_PATH

PREVIEW_LINE_LIMIT = 80
SECTION_KEY = "playbook_preview"


def playbook_file_path() -> Path:
    return project_root() / PLAYBOOK_PATH


def load_playbook_preview(*, line_limit: int = PREVIEW_LINE_LIMIT) -> str:
    """读取作战手册前 N 行（含每日流程、能力对照等关键章节）。"""
    path = playbook_file_path()
    if not path.is_file():
        return f"*作战手册未找到：{PLAYBOOK_PATH}*"
    lines = path.read_text(encoding="utf-8").splitlines()
    clipped = lines[: max(1, line_limit)]
    text = "\n".join(clipped)
    if len(lines) > line_limit:
        text += f"\n\n…（完整手册见 [{PLAYBOOK_PATH}]({PLAYBOOK_PATH})）"
    return text


def render_playbook_preview_sidebar(*, expanded: bool = False) -> None:
    """侧边栏「作战手册预览」expander。"""
    with st.expander("📖 作战手册预览", expanded=expanded):
        st.markdown(load_playbook_preview())
        st.markdown(f"[📖 完整手册]({PLAYBOOK_PATH})")
