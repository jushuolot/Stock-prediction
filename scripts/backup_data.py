#!/usr/bin/env python3
"""备份 data/ 目录（P10）。"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "backups"


def main() -> int:
    if not DATA.is_dir():
        print("[backup_data] 无 data 目录")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = OUT / f"data_{stamp}"
    shutil.copytree(DATA, dest)
    print(f"[backup_data] OK → {dest}")
    # 保留最近 5 份
    dirs = sorted(OUT.glob("data_*"), reverse=True)
    for old in dirs[5:]:
        shutil.rmtree(old, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
