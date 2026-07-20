"""
时事 / 经营 / 上下游 / 行业 —— 基于新闻关键词与行业的规则化解读（非实时研报）。
"""

from __future__ import annotations

from typing import Any

# 行业 → 基础宏观/产业周期预期（非个股股价预期）
_INDUSTRY_MACRO: dict[str, str] = {
    "半导体": "全球资本开支周期与国产替代逻辑并存，波动大、政策敏感。",
    "软件": "数字化投入具韧性，订单与现金流是核心验证点。",
    "银行": "息差与资产质量主导，经济修复节奏影响盈利预期。",
    "新能源": "渗透率提升长期确定，价格战与产能出清压制短期利润。",
    "医药": "创新药与集采博弈，研发管线决定分化。",
    "消费": "复苏斜率依赖居民信心，品牌力强者占优。",
    "制造": "出口与库存周期共振，自动化与供应链安全是主线。",
    "通信": "算力与运营商资本开支驱动，关注 5G/6G 与光模块。",
    "房地产": "政策托底与销售回暖节奏决定板块 beta。",
    "能源": "油价与地缘影响短期，能源安全影响中长期投资。",
    "默认": "结合宏观利率、行业景气与个股基本面三重验证，避免单看股价。",
}

_EVENT_KW = {
    "时事": ("政策", "监管", "央行", "国务院", "关税", "地缘", "战争", "选举", "补贴"),
    "经营": ("业绩", "预增", "亏损", "回购", "增持", "减持", "分红", "并购", "重组", "中标", "合同"),
    "上下游": ("涨价", "降价", "供应链", "芯片", "原材料", "客户", "订单", "出货", "产能", "扩产"),
    "行业": ("行业", "板块", "景气", "龙头", "市占率", "渗透率", "产能过剩"),
}


def infer_industry(*, name: str, sector: str = "", industry: str = "") -> str:
    s = (sector or industry or "").strip()
    if s:
        return s
    name_l = (name or "").lower()
    mapping = (
        ("半导体|芯片|存储|兆易|中际", "半导体"),
        ("银行|金融", "银行"),
        ("药|生物|医疗", "医药"),
        ("酒|食品|消费|零售", "消费"),
        ("光|通信|电信", "通信"),
        ("锂|光伏|电池|新能源", "新能源"),
        ("房|地产", "房地产"),
        ("油|煤|能源", "能源"),
        ("软件|科技|信息", "软件"),
    )
    for pat, ind in mapping:
        import re

        if re.search(pat, name, re.I):
            return ind
    return "制造"


def macro_expectation_for_industry(industry: str) -> str:
    for key, text in _INDUSTRY_MACRO.items():
        if key in industry or industry in key:
            return text
    return _INDUSTRY_MACRO["默认"]


def analyze_context(
    *,
    name: str,
    news: list[dict[str, Any]],
    sector: str = "",
    industry: str = "",
) -> dict[str, Any]:
    ind = infer_industry(name=name, sector=sector, industry=industry)
    macro = macro_expectation_for_industry(ind)
    hits: dict[str, list[str]] = {k: [] for k in _EVENT_KW}
    for n in news[:15]:
        t = (n.get("标题") or "") + (n.get("摘要") or "")
        for cat, kws in _EVENT_KW.items():
            for kw in kws:
                if kw in t and kw not in hits[cat]:
                    hits[cat].append(kw)

    lines: list[str] = []
    lines.append(f"**行业归类**：{ind}")
    lines.append(f"**基础市场预期（产业层面，非股价）**：{macro}")
    for cat in ("时事", "经营", "上下游", "行业"):
        if hits[cat]:
            lines.append(f"**{cat}线索**（新闻关键词）：{', '.join(hits[cat])}")
        else:
            lines.append(f"**{cat}线索**：暂未从新闻标题命中，建议人工查阅公告与行业数据。")

    supply = (
        "上游：原材料/核心零部件供给与价格；下游：订单、渠道与库存。"
        "若新闻命中「涨价/订单/产能」，可对照毛利率与存货周转。"
    )
    return {
        "行业": ind,
        "宏观预期": macro,
        "摘要": lines,
        "供应链提示": supply,
        "新闻命中": hits,
    }
