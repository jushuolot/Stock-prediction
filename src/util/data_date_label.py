"""行情数据日期标注：区分「查询时间」与「K线/榜单所属交易日」。"""

from __future__ import annotations

from datetime import date, datetime

_WEEKDAY_CN = "一二三四五六日"


def parse_bar_date(raw: str | date | datetime | None) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, datetime):
        return raw.date()
    s = str(raw).strip()[:10]
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def format_trade_date_cn(d: date | None) -> str:
    if d is None:
        return "—"
    wd = _WEEKDAY_CN[d.weekday()]
    return f"{d.year}年{d.month:02d}月{d.day:02d}日（周{wd}）"


def short_trade_date(d: date | None) -> str:
    if d is None:
        return ""
    return d.strftime("%m-%d")


def metric_date_suffix(bar_date: date | None) -> str:
    s = short_trade_date(bar_date)
    return f" · {s}" if s else ""


def today_label_cn() -> str:
    return format_trade_date_cn(date.today())


def data_lag_hint(bar_date: date | None, *, today: date | None = None) -> str | None:
    """若 K 线最后交易日早于今天，给出白话说明。"""
    if bar_date is None:
        return None
    ref = today or date.today()
    if bar_date >= ref:
        return None
    gap = (ref - bar_date).days
    if gap == 1:
        return (
            f"⚠️ **数据说明：** 本图最后一根 K 线为 **{format_trade_date_cn(bar_date)}**，"
            f"今天为 **{format_trade_date_cn(ref)}**。涨跌幅为相对前一交易日，"
            "今日日线可能尚未入库或数据源滞后。"
        )
    return (
        f"⚠️ **数据说明：** 行情截止 **{format_trade_date_cn(bar_date)}**，"
        f"今天 **{format_trade_date_cn(ref)}**（落后 {gap} 天）。"
        "以下价格/涨跌**不是今天实时价**，请以标注交易日为准。"
    )


def build_kline_caption(
    stats: dict,
    *,
    ksrc: str,
    query_label: str,
    range_text: str,
    currency: str,
) -> str:
    bar = parse_bar_date(stats.get("日期"))
    bar_cn = format_trade_date_cn(bar)
    today_cn = today_label_cn()
    return (
        f"📅 **K线交易日：{bar_cn}**　|　今天：{today_cn}　|　"
        f"查询于：{query_label}　|　区间：{range_text}　|　"
        f"来源：{ksrc}　|　货币：{currency}"
    )


def build_listing_caption(*, data_day: str, query_day: str | None = None, extra: str = "") -> str:
    q = query_day or date.today().isoformat()
    tail = f"　|　{extra}" if extra else ""
    return f"📅 **榜单/涨跌所属日：{data_day}**　|　分析执行日：{q}{tail}"


def snapshot_time_label(updated_at: str | None) -> str:
    if not updated_at:
        return "—"
    s = str(updated_at).strip()
    if len(s) >= 10 and s[4] == "-":
        return s[:16].replace("T", " ")
    return s[:19]
