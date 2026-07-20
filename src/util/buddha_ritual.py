"""P112 佛祖金标准：数据新鲜 + 花园 ritual 元数据与验收。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from src.providers import fresh_fetch

PROBE_CODE = "600519"
MIN_A_PICKS_IDEAL = 1


@dataclass(frozen=True)
class MarketDataProbe:
    probe_code: str
    bar_date: str | None
    source: str
    fresh: bool
    expected_lo: str
    expected_hi: str
    ranking_source: str
    error: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def probe_a_market(*, probe_code: str = PROBE_CODE) -> MarketDataProbe:
    """探针股 K 线 + 涨幅榜，确认 A 股数据是否为可接受最新交易日。"""
    now = fresh_fetch.china_now()
    lo, hi = fresh_fetch.expected_latest_bar_date(now=now)
    end = now.date()
    start = end - timedelta(days=14)
    code = str(probe_code).strip().zfill(6)
    bar_date: str | None = None
    source = ""
    fresh = False
    err_parts: list[str] = []
    rank_src = ""

    try:
        df, source = fresh_fetch.fetch_a_kline_fresh(
            code, kline="日线", start=start, end=end, now=now
        )
        bd = fresh_fetch.last_bar_date(df)
        bar_date = bd.isoformat() if bd else None
        fresh = fresh_fetch.is_bar_fresh(bd, market="A", now=now)
    except Exception as exc:
        err_parts.append(f"K线:{exc}")

    try:
        _, rank_src = fresh_fetch.fetch_a_ranking_fresh(board="涨幅榜", limit=20, now=now)
    except Exception as exc:
        err_parts.append(f"榜单:{exc}")
        if not fresh:
            fresh = False

    return MarketDataProbe(
        probe_code=code,
        bar_date=bar_date,
        source=source or rank_src or "—",
        fresh=fresh and bool(rank_src),
        expected_lo=lo.isoformat(),
        expected_hi=hi.isoformat(),
        ranking_source=rank_src,
        error="；".join(err_parts),
    )


def build_ritual_meta(
    probe: MarketDataProbe,
    *,
    a_picks: int,
    global_picks: int,
    predict_for: str,
    scan_ok: bool = True,
) -> dict[str, Any]:
    """花园页顶栏 / cloud_state 共用的 ritual 状态。"""
    data_ok = probe.fresh
    picks_ok = a_picks >= MIN_A_PICKS_IDEAL or global_picks >= 1
    level = "green"
    if not data_ok:
        level = "red"
    elif not picks_ok:
        level = "yellow"

    if not data_ok:
        summary = "数据未达今日标准，请勿采信推荐"
    elif not picks_ok:
        summary = "数据新鲜，但今日暂无达标推荐"
    else:
        summary = "佛祖可查：数据新鲜，推荐已就绪"

    return {
        "phase": "P112",
        "data_bar_date": probe.bar_date,
        "data_source": probe.source,
        "ranking_source": probe.ranking_source,
        "data_fresh": data_ok,
        "expected_bar_lo": probe.expected_lo,
        "expected_bar_hi": probe.expected_hi,
        "a_picks": a_picks,
        "global_picks": global_picks,
        "predict_for": predict_for,
        "ritual_ok": data_ok and scan_ok,
        "ritual_level": level,
        "ritual_summary": summary,
        "probe_code": probe.probe_code,
        "probe_error": probe.error,
    }


def ritual_banner_lines(meta: dict[str, Any] | None) -> tuple[str, str]:
    """返回 (主文案, 级别 green|yellow|red)。"""
    if not meta:
        return "🪷 佛祖查岗：尚未完成数据自检，请点「预测明日」或等待云端扫盘", "yellow"
    bar = meta.get("data_bar_date") or "—"
    src = meta.get("data_source") or "—"
    ap = int(meta.get("a_picks") or 0)
    gp = int(meta.get("global_picks") or 0)
    pred = meta.get("predict_for") or "—"
    today = date.today().isoformat()
    fresh = "✅" if meta.get("data_fresh") else "❌"
    line = (
        f"🪷 **佛祖查岗** {fresh} · 今天 {today} · "
        f"行情截止 **{bar}** · 来源 **{src}** · "
        f"明日目标 **{pred}** · A股 **{ap}** · 全球 **{gp}**"
    )
    level = str(meta.get("ritual_level") or "yellow")
    return line, level
