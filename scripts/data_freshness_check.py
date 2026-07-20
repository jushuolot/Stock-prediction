#!/usr/bin/env python3
"""各数据源新鲜度自检：样本股 600519 + A 股涨幅榜。"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.providers import eastmoney, fresh_fetch, sina, tencent, yahoo  # noqa: E402
from src.providers.ticker_util import yahoo_ticker_a  # noqa: E402
from src.util.data_date_label import format_trade_date_cn  # noqa: E402

PROBE = "600519"
BOARD = "涨幅榜"


def _print_kline_source(label: str, df, *, now) -> None:
    last = fresh_fetch.last_bar_date(df)
    fresh = fresh_fetch.is_bar_fresh(last, now=now)
    lo, hi = fresh_fetch.expected_latest_bar_date(now=now)
    status = "✅ 新鲜" if fresh else "❌ 滞后"
    print(
        f"  {label}: 最后K线 {format_trade_date_cn(last)} | "
        f"要求 {lo}~{hi} | {status}"
    )


def main() -> int:
    strict = "--strict" in sys.argv
    now = fresh_fetch.china_now()
    end = now.date()
    start = end - timedelta(days=30)
    lo, hi = fresh_fetch.expected_latest_bar_date(now=now)

    print(f"=== 数据新鲜度自检 ===")
    print(f"北京时间: {now.strftime('%Y-%m-%d %H:%M')} | 可接受交易日: {lo} ~ {hi}")
    print(f"\n--- K 线探针 {PROBE} ---")

    try:
        lines = eastmoney._fetch_kline_lines(PROBE, kline="日线", start=start, end=end)
        df_em = fresh_fetch._lines_to_df(lines, PROBE, "东方财富")
        _print_kline_source("东方财富", df_em, now=now)
    except Exception as exc:
        print(f"  东方财富: ❌ 失败 ({exc})")

    try:
        df_sn = sina.fetch_a_kline(PROBE, kline="日线", start=start, end=end)
        _print_kline_source("新浪财经", df_sn, now=now)
    except Exception as exc:
        print(f"  新浪财经: ❌ 失败 ({exc})")

    try:
        df_tx = tencent.fetch_a_kline(PROBE, kline="日线", start=start, end=end)
        _print_kline_source("腾讯财经", df_tx, now=now)
    except Exception as exc:
        print(f"  腾讯财经: ❌ 失败 ({exc})")

    try:
        yh = yahoo_ticker_a(PROBE)
        df_yh = yahoo.fetch_history(yh, start=start, end=end, interval="1d")
        _print_kline_source("Yahoo Finance", df_yh, now=now)
    except Exception as exc:
        print(f"  Yahoo Finance: ❌ 失败 ({exc})")

    kline_ok = False
    try:
        df_best, src = fresh_fetch.fetch_a_kline_fresh(
            PROBE, kline="日线", start=start, end=end, now=now
        )
        _print_kline_source(f"新鲜优选 → {src}", df_best, now=now)
        kline_ok = True
    except Exception as exc:
        print(f"  新鲜优选: ❌ 全部失败 ({exc})")

    print(f"\n--- 榜单 {BOARD} ---")
    for label, fn in (
        ("东方财富", eastmoney.fetch_a_ranking),
        ("新浪财经", sina.fetch_a_ranking),
    ):
        try:
            df = fn(board=BOARD, limit=20)
            ok = fresh_fetch.is_ranking_fresh(df, now=now)
            n = len(df) if df is not None else 0
            qd = tencent.fetch_quote_date(PROBE)
            print(
                f"  {label}: {n} 行 | 探针日 {format_trade_date_cn(qd)} | "
                f"{'✅ 新鲜' if ok else '❌ 滞后'}"
            )
        except Exception as exc:
            print(f"  {label}: ❌ 失败 ({exc})")

    rank_ok = False
    try:
        df_r, src_r = fresh_fetch.fetch_a_ranking_fresh(board=BOARD, limit=20, now=now)
        print(f"  新鲜优选 → {src_r}: {len(df_r)} 行 ✅")
        rank_ok = True
    except Exception as exc:
        print(f"  新鲜优选: ❌ 全部失败 ({exc})")

    if strict and not (kline_ok and rank_ok):
        print("\n[data_freshness_check] STRICT 未通过")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
