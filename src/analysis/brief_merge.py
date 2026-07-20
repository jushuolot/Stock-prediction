"""合并多份可读简报为单一 Markdown / HTML（P6）。"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Callable

from src.util.query_time import format_query_datetime


def collect_briefs_for_watchlist(
    watchlist: list[dict[str, Any]],
    get_brief: Callable[[str], str | None],
) -> dict[str, str]:
    """按自选股顺序收集已有简报。get_brief(code) -> markdown 或 None。"""
    out: dict[str, str] = {}
    for item in watchlist:
        code = str(item.get("代码") or "")
        if not code:
            continue
        md = get_brief(code)
        if md and str(md).strip():
            out[code] = str(md).strip()
    return out


def build_merged_briefs_markdown(
    watchlist: list[dict[str, Any]],
    briefs: dict[str, str],
    *,
    query_label: str = "",
) -> str:
    now = query_label or format_query_datetime(datetime.now())
    lines: list[str] = [
        "# 自选股分析合集",
        "",
        f"> 合并时间：{now}　|　含简报 {len(briefs)} 份 / 自选 {len(watchlist)} 只",
        "",
        "## 目录",
        "",
    ]
    for item in watchlist:
        code = str(item.get("代码") or "")
        name = str(item.get("名称") or code)
        if code in briefs:
            anchor = code.replace(".", "_")
            lines.append(f"- [{name}（{code}）](#brief-{anchor})")

    if not briefs:
        lines.extend(["", "_暂无已生成的单股简报。请在工作台对标的点击「⚡ 一键分析」。_", ""])
        return "\n".join(lines)

    lines.append("")
    for item in watchlist:
        code = str(item.get("代码") or "")
        md = briefs.get(code)
        if not md:
            continue
        anchor = code.replace(".", "_")
        lines.extend(["---", "", f"<a id=\"brief-{anchor}\"></a>", "", md, ""])

    lines.extend(
        [
            "",
            "---",
            "",
            "_合集由 Stock Assistant 自动生成，公开行情整理，非投资建议。_",
            "",
        ]
    )
    return "\n".join(lines)


def build_merged_briefs_html(
    watchlist: list[dict[str, Any]],
    briefs: dict[str, str],
    *,
    query_label: str = "",
) -> str:
    now = query_label or format_query_datetime(datetime.now())
    sections: list[str] = []
    for item in watchlist:
        code = str(item.get("代码") or "")
        name = str(item.get("名称") or code)
        md = briefs.get(code)
        if not md:
            continue
        body = html.escape(md)
        sections.append(
            f'<section class="brief" id="brief-{html.escape(code.replace(".", "_"))}">'
            f"<h2>{html.escape(name)}（{html.escape(code)}）</h2>"
            f"<pre class=\"brief-body\">{body}</pre></section>"
        )

    empty = (
        '<p class="empty">暂无简报。请在工作台对标的执行「一键分析」后再导出。</p>'
        if not sections
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>自选股分析合集 · Stock Assistant</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 920px;
    margin: 0 auto;
    padding: 16px 20px 48px;
    background: #0e1117;
    color: #fafafa;
    line-height: 1.5;
  }}
  .meta {{ color: #9ca3af; font-size: 14px; margin-bottom: 24px; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 8px; }}
  h2 {{ font-size: 1.15rem; color: #fbbf24; margin-top: 0; }}
  .brief {{
    border: 1px solid #31333f;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    page-break-inside: avoid;
  }}
  .brief-body {{
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 13px;
    margin: 0;
    background: #1a1d24;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
  }}
  .empty {{ color: #9ca3af; }}
  @media print {{
    body {{ background: #fff; color: #111; }}
    .brief {{ border-color: #ccc; }}
    .brief-body {{ background: #f5f5f5; }}
  }}
  @media (max-width: 640px) {{
    body {{ padding: 12px; }}
    h1 {{ font-size: 1.25rem; }}
  }}
</style>
</head>
<body>
  <h1>自选股分析合集</h1>
  <p class="meta">合并时间：{html.escape(now)}　|　简报 {len(briefs)} 份</p>
  {empty}
  {"".join(sections)}
  <p class="meta">非投资建议 · 浏览器「打印 → 另存为 PDF」可导出 PDF</p>
</body>
</html>"""
