"""全球股市榜单：双击行同步到「深度溯源」下拉框。"""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.ui.df_style import html_pct_color, show_df


_DISPLAY_COLS = (
    "代码",
    "名称",
    "市场",
    "最新价",
    "涨跌幅%",
    "涨跌额",
    "成交量",
    "成交额",
    "换手率%",
    "振幅%",
)


def sync_mover_pick_from_query() -> None:
    """读取 ?mover_pick= 并写入 session，供 selectbox 使用。"""
    raw = st.query_params.get("mover_pick")
    if not raw:
        return
    code = raw[0] if isinstance(raw, list) else str(raw)
    code = code.strip()
    if code:
        st.session_state["movers_pick_code"] = code
    try:
        del st.query_params["mover_pick"]
    except Exception:
        st.query_params.clear()


def _fmt_cell(val: Any, col: str) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        if col in ("涨跌幅%", "换手率%", "振幅%"):
            return f"{float(val):.2f}%"
        if col in ("最新价", "涨跌额"):
            return f"{float(val):.2f}"
        if col in ("成交量", "成交额"):
            v = float(val)
            if v >= 1e8:
                return f"{v / 1e8:.2f}亿"
            if v >= 1e4:
                return f"{v / 1e4:.2f}万"
            return f"{v:.0f}"
    except (TypeError, ValueError):
        pass
    return str(val)


def render_movers_table(df: pd.DataFrame, *, selected_code: str, query_label: str = "") -> None:
    """可双击选股的 HTML 表格（与 Streamlit 深色主题接近）。"""
    cols = [c for c in _DISPLAY_COLS if c in df.columns]
    if not cols:
        show_df(df)
        return

    show = df[cols].head(80)
    header = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body_rows: list[str] = []
    sel = str(selected_code or "").strip()
    for _, row in show.iterrows():
        raw_code = row.get("代码", "")
        if pd.isna(raw_code):
            continue
        code = str(raw_code).strip()
        if "." in code and code.endswith(".0"):
            code = code.split(".")[0]
        code_esc = html.escape(code)
        cls = "selected" if code == sel or code.zfill(6) == sel.zfill(6) else ""
        cells_list: list[str] = []
        for c in cols:
            raw = row.get(c)
            text = html.escape(_fmt_cell(raw, c))
            if c in ("涨跌幅%", "涨跌额", "振幅%"):
                color = html_pct_color(raw)
                cells_list.append(f'<td style="color:{color};font-weight:600">{text}</td>')
            else:
                cells_list.append(f"<td>{text}</td>")
        cells = "".join(cells_list)
        body_rows.append(
            f'<tr class="mover-row {cls}" data-code="{code_esc}" '
            f'ondblclick="pickMover(\'{code_esc}\')" title="双击选中：{code_esc}">'
            f"{cells}</tr>"
        )

    n = len(show)
    height = min(560, 56 + n * 34)
    hint_prefix = (
        f"本次查询：{html.escape(query_label)} · " if query_label else ""
    )
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
    font-size: 14px;
    background: rgb(14, 17, 23);
    color: #fafafa;
  }}
  .hint {{
    padding: 6px 10px 10px;
    color: #9ca3af;
    font-size: 13px;
  }}
  .wrap {{ overflow: auto; max-height: {height - 40}px; }}
  table.movers {{
    width: 100%;
    border-collapse: collapse;
  }}
  table.movers th {{
    position: sticky;
    top: 0;
    background: #262730;
    color: #fafafa;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid #464855;
    white-space: nowrap;
  }}
  table.movers td {{
    padding: 7px 10px;
    border-bottom: 1px solid #31333f;
    white-space: nowrap;
    cursor: default;
  }}
  table.movers tr.mover-row:hover td {{
    background: #31333f;
  }}
  table.movers tr.mover-row.selected td {{
    background: #2d3139;
  }}
  table.movers tr.mover-row.selected td:first-child {{
    border-left: 3px solid #ff4b4b;
    padding-left: 7px;
  }}
  table.movers tr.mover-row:active td {{
    background: #4a4d57;
  }}
</style>
</head>
<body>
  <div class="hint">{hint_prefix}左侧红条表示当前已选中行（非锁定）；双击任意行可切换选中并同步下方下拉框。</div>
  <div class="wrap">
    <table class="movers">
      <thead><tr>{header}</tr></thead>
      <tbody>{"".join(body_rows)}</tbody>
    </table>
  </div>
  <script>
  function pickMover(code) {{
    try {{
      const top = window.top || window.parent;
      const u = new URL(top.location.href);
      u.searchParams.set("mover_pick", code);
      top.location.href = u.toString();
    }} catch (e) {{
      const u = new URL(window.location.href);
      u.searchParams.set("mover_pick", code);
      window.location.href = u.toString();
    }}
  }}
  </script>
</body>
</html>
"""
    components.html(table_html, height=height, scrolling=True)
