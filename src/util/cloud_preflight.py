"""Streamlit Cloud 部署前自检逻辑（P4）。"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_REQ = ("curl_cffi", "curl-cffi")
REQUIRED_REQ_HINTS = (
    ("numpy", r"<\s*2"),
    ("pandas", None),
    ("streamlit", None),
    ("yfinance", r"<\s*0\.3"),
)


def check_requirements_text(text: str) -> list[str]:
    errors: list[str] = []
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line.lower())
    body = "\n".join(lines)
    for bad in FORBIDDEN_REQ:
        if bad in body:
            errors.append(f"requirements.txt 含 {bad}（云端易编译失败，请移除）")
    for pkg, pattern in REQUIRED_REQ_HINTS:
        if pkg not in body:
            errors.append(f"requirements.txt 缺少 {pkg}")
            continue
        if pattern:
            pkg_line = next((ln for ln in lines if ln.startswith(pkg)), "")
            if not re.search(pattern, pkg_line.replace(" ", "")):
                errors.append(f"{pkg} 未满足云端约束（期望匹配 {pattern}）")
    return errors


def check_project_layout(root: Path | None = None) -> list[str]:
    base = root or ROOT
    errors: list[str] = []
    required = (
        base / "app.py",
        base / "requirements.txt",
        base / ".streamlit" / "config.toml",
        base / ".streamlit" / "secrets.toml.example",
    )
    for p in required:
        if not p.is_file():
            errors.append(f"缺少文件：{p.relative_to(base)}")
    return errors


def check_compile(root: Path | None = None) -> list[str]:
    base = root or ROOT
    targets = [base / "app.py", base / "src"]
    cmd = [
        sys.executable,
        "-m",
        "compileall",
        "-q",
        "-x",
        r"\.venv",
        *[str(t) for t in targets if t.exists()],
    ]
    r = subprocess.run(cmd, cwd=base, capture_output=True, text=True)
    if r.returncode != 0:
        return [f"py_compile 失败：{(r.stderr or r.stdout).strip()}"]
    return []


def check_imports(root: Path | None = None) -> list[str]:
    base = root or ROOT
    code = """
import numpy as np
import pandas as pd
import streamlit
import plotly
import yfinance
assert int(str(np.__version__).split(".")[0]) < 2, "numpy>=2 与 pandas 2.0 不兼容"
print("imports_ok")
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=base, capture_output=True, text=True)
    if r.returncode != 0:
        return [f"关键依赖导入失败：{(r.stderr or r.stdout).strip()}"]
    return []


def check_data_writable(root: Path | None = None) -> list[str]:
    base = root or ROOT
    data = base / "data"
    try:
        data.mkdir(parents=True, exist_ok=True)
        probe = data / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        return [f"data/ 不可写：{exc}"]
    return []


def run_preflight(*, skip_imports: bool = False, root: Path | None = None) -> list[str]:
    base = root or ROOT
    errors: list[str] = []
    req_path = base / "requirements.txt"
    if req_path.is_file():
        errors.extend(check_requirements_text(req_path.read_text(encoding="utf-8")))
    else:
        errors.append("缺少 requirements.txt")
    errors.extend(check_project_layout(base))
    errors.extend(check_data_writable(base))
    errors.extend(check_compile(base))
    if not skip_imports:
        errors.extend(check_imports(base))
    return errors
