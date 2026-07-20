"""板块联动提醒 UI（P7）。"""

from __future__ import annotations

import streamlit as st

from src.analysis.sector_linkage import build_linkage_alerts, scan_watchlist_sector_linkage
from src.providers.eastmoney_stock_plates import fetch_stock_belong_plates


@st.cache_data(ttl=300, show_spinner=False)
def _cached_linkage(watchlist_json: str) -> list[dict]:
    import json

    wl = json.loads(watchlist_json)
    links = scan_watchlist_sector_linkage(wl, fetch_stock_belong_plates)
    return [
        {
            "plate_code": x.plate_code,
            "plate_name": x.plate_name,
            "stocks": list(x.stocks),
            "pct": x.pct,
            "count": x.count,
        }
        for x in links
    ]


def render_sector_linkage_panel(*, watchlist: list[dict], key_prefix: str = "sector") -> None:
    a_count = sum(
        1
        for x in watchlist
        if str(x.get("类型") or "A") == "A" and str(x.get("代码") or "").replace(".", "").isdigit()
    )
    with st.expander("🔗 板块联动扫描（A 股）", expanded=False):
        if a_count < 2:
            st.caption("至少 2 只 A 股自选才可扫描共用板块。")
            return
        if st.button("扫描联动板块", key=f"{key_prefix}_scan", use_container_width=True):
            st.session_state[f"{key_prefix}_done"] = True
        if not st.session_state.get(f"{key_prefix}_done"):
            st.caption("点击后分析自选是否集中在同一行业/概念（东财所属板块）。")
            return
        import json

        wl_key = json.dumps(watchlist, ensure_ascii=False, sort_keys=True, default=str)
        with st.spinner("正在扫描所属板块…"):
            raw = _cached_linkage(wl_key)
        if not raw:
            st.info("未发现多股共用板块，或接口暂不可用。")
            return
        from src.analysis.sector_linkage import SectorLink

        links = [
            SectorLink(
                plate_code=r["plate_code"],
                plate_name=r["plate_name"],
                stocks=tuple(r["stocks"]),
                pct=r.get("pct"),
            )
            for r in raw
        ]
        for msg in build_linkage_alerts(links)[:8]:
            st.markdown(msg)
        st.caption(f"共 {len(links)} 组联动；仅扫描前 10 只 A 股。")
