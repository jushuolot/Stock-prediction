#!/bin/bash
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

if ! command -v python3 &>/dev/null; then
  osascript -e 'display dialog "未找到 python3，请先从 python.org 安装 Python 后再试。" buttons {"好"} default button 1'
  exit 1
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv || exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

# 依赖自检：pandas 2.0.x 与 numpy 2.x 会二进制不兼容，表现为导入 pandas 直接崩溃。
_NUMPY_MAJOR="$(python3 - <<'PY'
try:
    import numpy as np
    print(str(np.__version__).split('.')[0])
except Exception:
    print("")
PY
)"
if [ "$_NUMPY_MAJOR" = "2" ]; then
  echo "[stock-assistant] 检测到 numpy>=2，自动降级到 numpy<2（避免 pandas 崩溃）..."
  pip install -q "numpy<2" || {
    osascript -e 'display dialog "检测到 numpy>=2 但自动修复失败。请检查网络后重试。" buttons {"好"} default button 1'
    exit 1
  }
fi

pip install -q -r requirements.txt || { osascript -e 'display dialog "依赖安装失败，请检查网络后重试。" buttons {"好"} default button 1'; exit 1; }

python3 scripts/cloud_preflight.py || {
  osascript -e 'display dialog "云端自检未通过，请终端运行: python3 scripts/cloud_preflight.py 查看详情。" buttons {"好"} default button 1'
  exit 1
}

exec streamlit run app.py

