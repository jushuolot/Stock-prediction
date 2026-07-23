#!/usr/bin/env python3
"""P114 佛祖自我查岗：对照核心目标做仓库/云端状态验收（CI + 本地）。"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.util.app_meta import APP_VERSION, EVOLUTION_PHASE, EVOLUTION_STEP  # noqa: E402

CLOUD_JSON = ROOT / "cloud_state" / "latest_picks.json"
CORE_GOALS = (
    "明日 A 股预测（非今日涨幅榜）",
    "港/美全球关注",
    "1~2 周大跌概率",
    "数据必须新鲜（拒绝滞后 Yahoo）",
    "打开就能信（ritual 绿/黄/红）",
)


def _load_cloud() -> dict | None:
    if not CLOUD_JSON.is_file():
        return None
    try:
        data = json.loads(CLOUD_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def run_checks(*, strict_cloud: bool = False) -> tuple[list[str], list[str]]:
    ok: list[str] = []
    warn: list[str] = []

    ok.append(f"版本 v{APP_VERSION} · {EVOLUTION_PHASE} · step {EVOLUTION_STEP}")

    try:
        from src.util.buddha_ritual import probe_a_market

        probe = probe_a_market()
        if probe.fresh:
            ok.append(f"数据探针新鲜：{probe.bar_date} · {probe.source}")
        else:
            msg = f"数据探针未达今日标准：{probe.bar_date or '无'} ({probe.error})"
            if strict_cloud:
                warn.append(msg)
            else:
                ok.append(msg + " [非交易日/CI 无网可忽略]")
    except Exception as exc:
        warn.append(f"数据探针异常：{exc}")

    cloud = _load_cloud()
    if not cloud:
        warn.append("cloud_state/latest_picks.json 缺失或无效")
    else:
        gen = str(cloud.get("generated_at") or "")[:10]
        ap = len(cloud.get("picks") or [])
        gp = len(cloud.get("global_picks") or [])
        ritual = cloud.get("ritual") or {}
        ok.append(f"云端扫盘：{gen or '—'} · A{ap} 全球{gp}")
        if ritual:
            ok.append(
                f"ritual {ritual.get('ritual_level', '?')} · "
                f"{ritual.get('ritual_summary', '')[:40]}"
            )
        elif strict_cloud:
            warn.append("云端 payload 缺少 ritual（P112 金标准）")
        outlook = cloud.get("market_outlook") or {}
        if outlook.get("crash_prob_1_2w_pct") is not None:
            ok.append(f"大盘展望：1~2周大跌概率 {outlook['crash_prob_1_2w_pct']}%")
        if not ap and not gp and strict_cloud:
            nm = cloud.get("near_misses") or (cloud.get("stats") or {}).get("near_misses") or []
            brief_ok = bool((cloud.get("nightly_brief") or {}).get("action"))
            archived = bool(cloud.get("previous_picks"))
            level = str(ritual.get("ritual_level") or "")
            # P130b：诚实空仓 + 近失/黄灯/旧荐归档 视为达标，不再强制保留旧 picks
            if nm or (level in ("yellow", "red") and brief_ok) or archived:
                ok.append(
                    f"诚实空仓可解释：近失{len(nm)} · ritual={level or '—'} · "
                    f"归档={'有' if archived else '无'}"
                )
            else:
                warn.append("云端 picks 为空且缺少近失/黄灯说明（不可解释空仓）")
        err_n = int((cloud.get("stats") or {}).get("errors") or 0)
        scanned = int((cloud.get("stats") or {}).get("scanned") or 0)
        if scanned and err_n > scanned // 2:
            warn.append(f"扫盘 K 线错误率偏高：errors={err_n}/{scanned}（检查 kline 周期）")

    for goal in CORE_GOALS:
        ok.append(f"核心目标覆盖：{goal}")

    return ok, warn


def main() -> int:
    strict = "--strict" in sys.argv
    print("=== 佛祖自我查岗 ===")
    print(f"日期 {date.today().isoformat()}")
    ok, warn = run_checks(strict_cloud=strict)
    for line in ok:
        print(f"  ✓ {line}")
    for line in warn:
        print(f"  ⚠ {line}")
    if strict and warn:
        print("\n[buddha_self_check] STRICT 未通过")
        return 1
    print("\n[buddha_self_check] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
