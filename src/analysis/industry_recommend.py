"""
按行业聚合异动标的，给出「基础市场预期」下的参考观察名单（供人工判断，非买卖推荐）。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.analysis.context_analysis import infer_industry, macro_expectation_for_industry


def build_industry_clusters(analyses: list[dict[str, Any]]) -> pd.DataFrame:
    """analyses: global_anomaly 输出的 dict 列表。"""
    if not analyses:
        return pd.DataFrame()
    rows = []
    for a in analyses:
        rows.append(
            {
                "行业": a.get("行业") or "其他",
                "代码": a.get("代码"),
                "名称": a.get("名称"),
                "涨跌幅%": a.get("涨跌幅%"),
                "异动分": a.get("异动分"),
                "市场": a.get("市场"),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    out_rows: list[dict[str, Any]] = []
    for ind, grp in df.groupby("行业"):
        grp = grp.sort_values("异动分", ascending=False)
        macro = macro_expectation_for_industry(str(ind))
        top = grp.head(3)
        codes = "、".join(f"{r['名称']}({r['代码']})" for _, r in top.iterrows())
        out_rows.append(
            {
                "行业": ind,
                "标的数": len(grp),
                "平均涨跌%": round(float(grp["涨跌幅%"].mean()), 2) if grp["涨跌幅%"].notna().any() else None,
                "基础市场预期": macro,
                "参考观察（人工判断）": codes,
                "说明": "按异动分排序取前3，仅供研究跟踪，不构成投资建议",
            }
        )
    return pd.DataFrame(out_rows).sort_values("标的数", ascending=False)
