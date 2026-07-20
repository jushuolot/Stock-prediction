#!/usr/bin/env bash
# 一键验证：preflight + 单元测试 + 佛祖自我查岗（P14 / P114）
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
python3 scripts/cloud_preflight.py
python3 -m unittest discover -s tests -q
python3 scripts/buddha_self_check.py
if python3 scripts/data_freshness_check.py --strict 2>/dev/null; then
  echo "[evolve_verify] data freshness OK"
else
  echo "[evolve_verify] WARN: data freshness strict check skipped or failed (非交易日/无网可忽略)"
fi
echo "[evolve_verify] OK"
