"""财务对比表（东财风格 HTML，适配 Streamlit 深色主题）。"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st
import streamlit.components.v1 as components


def render_industry_compare_table(data: dict[str, Any]) -> None:
    if not data or not data.get("ok"):
        reason = str(data.get("reason") or "")
        if reason == "not_a_share":
            st.caption("财务对比：仅 A 股支持（东财 F10）。")
        else:
            st.caption(f"财务对比暂不可用{('：' + reason) if reason else '。'}")
        return

    cols = data.get("columns") or []
    rows = data.get("rows") or []
    report = data.get("report_type") or ""
    src = data.get("source") or ""
    note = data.get("note") or ""

    header = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
    body: list[str] = []
    for row in rows:
        kind = row.get("kind") or ""
        label = html.escape(str(row.get("label") or ""))
        cells = row.get("cells") or []
        if kind == "quartile":
            tds = []
            for cell in cells:
                if isinstance(cell, dict):
                    tds.append(f"<td>{_quartile_bar_html(cell)}</td>")
                else:
                    tds.append(f"<td>{html.escape(str(cell))}</td>")
            body.append(
                f'<tr class="row-quartile"><th class="row-label">{label}</th>{"".join(tds)}</tr>'
            )
        else:
            cls = {
                "stock": "row-stock",
                "industry_avg": "row-ind",
                "rank": "row-rank",
            }.get(kind, "")
            tds = "".join(f"<td>{html.escape(str(c))}</td>" for c in cells)
            body.append(f'<tr class="{cls}"><th class="row-label">{label}</th>{tds}</tr>')

    cap = []
    if report:
        cap.append(f"报告期：{html.escape(report)}")
    if src:
        cap.append(html.escape(src))
    cap_html = " · ".join(cap)
    note_html = f'<div class="note">{html.escape(note)}</div>' if note else ""

    table_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    background: rgb(14, 17, 23);
    color: #fafafa;
  }}
  .cap {{ padding: 4px 10px 8px; color: #9ca3af; font-size: 12px; }}
  .note {{ padding: 0 10px 8px; color: #6b7280; font-size: 11px; line-height: 1.4; }}
  .wrap {{ overflow-x: auto; padding: 0 6px 8px; }}
  table.ic {{
    width: 100%;
    border-collapse: collapse;
    min-width: 720px;
  }}
  table.ic th, table.ic td {{
    padding: 8px 10px;
    border-bottom: 1px solid #31333f;
    text-align: right;
    white-space: nowrap;
  }}
  table.ic thead th {{
    background: #262730;
    color: #e5e7eb;
    font-weight: 600;
    position: sticky;
    top: 0;
  }}
  table.ic th.row-label {{
    text-align: left;
    min-width: 108px;
    color: #d1d5db;
    font-weight: 500;
    background: #1a1d24;
  }}
  table.ic tr.row-stock td {{ color: #fbbf24; }}
  table.ic tr.row-ind td {{ color: #93c5fd; }}
  table.ic tr.row-rank td {{ color: #9ca3af; font-size: 12px; }}
  table.ic tr.row-quartile td {{ vertical-align: middle; }}
  .qcell {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    justify-content: flex-end;
    width: 100%;
  }}
  .qbar {{
    display: flex;
    flex-direction: column-reverse;
    gap: 2px;
    height: 36px;
    width: 10px;
  }}
  .qseg {{
    flex: 1;
    background: #3f4251;
    border-radius: 1px;
    min-height: 6px;
  }}
  .qseg.on {{ background: linear-gradient(180deg, #f97316, #ea580c); }}
  .qseg.on.top {{ background: linear-gradient(180deg, #fbbf24, #f59e0b); }}
  .qlabel {{
    font-size: 12px;
    color: #e5e7eb;
    min-width: 2.5em;
    text-align: left;
  }}
</style>
</head>
<body>
  <div class="cap">{cap_html}</div>
  {note_html}
  <div class="wrap">
    <table class="ic">
      <thead><tr><th class="row-label">对比项</th>{header}</tr></thead>
      <tbody>{"".join(body)}</tbody>
    </table>
  </div>
</body>
</html>
"""
    ncols = max(len(cols), 1)
    height = min(320, 88 + len(rows) * 36)
    components.html(table_html, height=height, scrolling=ncols > 6)


def _quartile_bar_html(cell: dict[str, Any]) -> str:
    level = cell.get("level")
    label = html.escape(str(cell.get("label") or "—"))
    if level is None:
        return f'<span class="qlabel">{label}</span>'
    level = int(level)
    filled = min(level + 1, 4)
    segs: list[str] = []
    for i in range(4):
        cls = "qseg"
        if i < filled:
            cls += " on"
            if level >= 4 and i == 3:
                cls += " top"
        segs.append(f'<div class="{cls}"></div>')
    return (
        f'<div class="qcell"><div class="qbar">{"".join(segs)}</div>'
        f'<span class="qlabel">{label}</span></div>'
    )


def show_industry_compare_block(
    *,
    code: str,
    kind: str,
    lazy: bool = False,
    load_key: str | None = None,
) -> None:
    """财务对比区块；lazy=True 时需用户点击加载按钮后才请求接口。"""
    if kind != "A" or not str(code).replace(".", "").isdigit():
        st.caption("财务对比：仅 A 股支持（东财 F10）。")
        return
    code6 = str(code).split(".")[0].zfill(6)[:6]
    sk = load_key or f"fin_compare_loaded_{code6}"
    if lazy:
        if st.button("加载财务对比", key=f"{sk}_btn", type="secondary"):
            st.session_state[sk] = True
        if not st.session_state.get(sk):
            st.caption("点击上方按钮拉取个股 vs 行业财务对比（东财 F10）。")
            return
    from src.providers.eastmoney_f10 import fetch_industry_compare

    with st.spinner("正在拉取行业财务对比…"):
        data = fetch_industry_compare(code6)
    render_industry_compare_table(data)
