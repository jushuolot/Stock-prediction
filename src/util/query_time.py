"""查询时间格式化（与 Streamlit 解耦）。"""

from __future__ import annotations

from datetime import date, datetime


def format_query_datetime(dt: datetime | None = None) -> str:
    t = dt or datetime.now()
    return t.strftime("%Y年%m月%d日 %H:%M:%S")


def format_query_date(d: date | None = None) -> str:
    day = d or date.today()
    return day.strftime("%Y年%m月%d日")


def format_data_range(start: date, end: date) -> str:
    return f"{start.isoformat()} ~ {end.isoformat()}"
