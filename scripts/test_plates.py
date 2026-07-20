#!/usr/bin/env python3
"""本地验证板块接口：在 stock-assistant 目录执行 PYTHONPATH=. python3 scripts/test_plates.py"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.providers.eastmoney_plates import fetch_flow_board, fetch_plate_board  # noqa: E402


def main() -> int:
    ok = True
    for cat in ("行业板块", "概念板块", "地区板块"):
        df = fetch_plate_board(category=cat, board="涨幅榜", limit=5)
        print(f"{cat}: {len(df)} rows")
        if df.empty:
            ok = False
        else:
            print(df[["板块名称", "涨跌幅", "主力净流入", "领涨股", "相关链接"]].head(2).to_string())
    flow = fetch_flow_board(limit=5)
    print(f"资金流向: {len(flow)} rows")
    if flow.empty:
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
