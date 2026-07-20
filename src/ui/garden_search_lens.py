"""花园搜索：单股全维档案 + 可读结论（P125）。"""

from __future__ import annotations

import streamlit as st

from src.ui.df_style import show_df

from src.analysis.prediction_calibration import load_calibration_adjustments, merge_pick_logs
from src.analysis.stock_dossier import StockDossier, build_stock_dossier
from src.providers import eastmoney, symbol_search
from src.providers.image_ticker_ocr import image_to_search_terms
from src.storage.cloud_pick_log import load_cloud_pick_log
from src.storage.history_store import mark_dirty
from src.util.readonly_mode import is_readonly_mode
from src.util.search_history import normalize_search_history, push_search
from src.util.watchlist_add import add_hit_to_watchlist, is_in_watchlist


def _gemini_key_from_secrets() -> str:
    try:
        v = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        return str(v or "").strip()
    except Exception:
        return ""


def _resolve_hit(keyword: str) -> eastmoney.SearchHit | None:
    kw = (keyword or "").strip()
    if not kw:
        return None
    hits = symbol_search.suggest(kw, limit=12)
    if not hits:
        return None
    kw_u = kw.upper()
    for h in hits:
        if h.code.upper() == kw_u or (h.yahoo or "").upper() == kw_u:
            return h
        if kw in (h.name or ""):
            return h
    return hits[0]


def _merged_pick_log(local_log: list) -> list:
    return merge_pick_logs(local_log, load_cloud_pick_log())


def _pattern_adj() -> dict[str, float]:
    rep = st.session_state.get("_calibration_report") or {}
    cal = load_calibration_adjustments(rep)
    return dict(cal.get("pattern") or {})


def _render_dossier(dossier: StockDossier, hit: eastmoney.SearchHit, *, readonly: bool) -> None:
    st.markdown(f"## {dossier.name} `{dossier.code}` · **{dossier.verdict}**")
    st.markdown("**核心结论（供参考，非投资建议）**")
    for b in dossier.bullets:
        st.markdown(f"- {b}")

    import pandas as pd

    show_df(pd.DataFrame(list(dossier.rows)), use_container_width=True, hide_index=True)

    st.download_button(
        "📥 下载该股一页纸 (.md)",
        data=dossier.markdown.encode("utf-8"),
        file_name=f"{dossier.code}_{dossier.name}.md",
        mime="text/markdown",
        key=f"garden_dossier_dl_{dossier.code}",
    )

    if not readonly:
        wl = list(st.session_state.get("watchlist") or [])
        if not is_in_watchlist(wl, dossier.code) and st.button(
            "➕ 加入自选", key=f"garden_dossier_add_{dossier.code}"
        ):
            wl, added = add_hit_to_watchlist(wl, hit)
            if added:
                st.session_state.watchlist = wl
                mark_dirty()
                st.success("已加入自选")


def render_garden_search_lens(pick_log: list, *, fetch_fn) -> None:
    """花园第一屏：搜索 → 全维档案 + 可读结论。"""
    st.markdown("### 🔍 搜一只，看全维结论")
    st.caption("输入框内 📷 可识图；右侧单独点「搜索」。")

    st.session_state.setdefault("garden_lens_kw", "茅台")
    history = normalize_search_history(st.session_state.get("search_history"))
    if history:
        chips = st.columns(min(len(history), 6))
        for i, term in enumerate(history[:6]):
            with chips[i % len(chips)]:
                if st.button(term, key=f"garden_lens_hist_{i}", use_container_width=True):
                    st.session_state.garden_lens_kw = term
                    st.session_state._garden_lens_pending_kw = term

    st.markdown(
        """
        <style>
        div[data-testid="column"]:has(input[placeholder*="600519"]) div[data-testid="stTextInput"] input {
            padding-right: 2.75rem !important;
        }
        div[data-testid="column"]:has(input[placeholder*="600519"]) > div[data-testid="stHorizontalBlock"] {
            position: relative;
        }
        div[data-testid="column"]:has(input[placeholder*="600519"]) > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
            position: absolute;
            right: 0.4rem;
            top: 0.35rem;
            width: auto !important;
            min-width: 0 !important;
            flex: 0 0 auto !important;
            z-index: 2;
        }
        div[data-testid="column"]:has(input[placeholder*="600519"]) > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) button {
            padding: 0.25rem 0.45rem !important;
            min-height: 0 !important;
            font-size: 1.05rem !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    uploaded = None
    do_search = False
    col_in, col_go = st.columns([6, 1], gap="small")
    with col_in:
        c_text, c_cam = st.columns([1, 0.001], gap="small")
        with c_text:
            kw = st.text_input(
                "股票",
                key="garden_lens_kw",
                placeholder="茅台 · 600519 · AAPL",
                label_visibility="collapsed",
            )
        with c_cam:
            popover = getattr(st, "popover", None)
            if popover is not None:
                with popover("📷", use_container_width=False, help="上传 K 线截图识股"):
                    uploaded = st.file_uploader(
                        "截图",
                        type=["png", "jpg", "jpeg", "webp"],
                        key="garden_lens_image",
                        label_visibility="collapsed",
                    )
            elif st.button("📷", key="garden_lens_img_toggle", use_container_width=True):
                st.session_state.garden_lens_show_img = True
    with col_go:
        do_search = st.button("搜索", type="primary", use_container_width=True, key="garden_lens_search")

    if uploaded is None and st.session_state.get("garden_lens_show_img"):
        uploaded = st.file_uploader(
            "上传截图识股",
            type=["png", "jpg", "jpeg", "webp"],
            key="garden_lens_image_fb",
        )

    pending = st.session_state.pop("_garden_lens_pending_kw", None)
    if pending:
        kw = pending
        do_search = True

    if uploaded is not None:
        sig = f"{uploaded.name}:{uploaded.size}"
        if st.session_state.get("_garden_lens_img_sig") != sig:
            st.session_state._garden_lens_img_sig = sig
            api_key = _gemini_key_from_secrets()
            with st.spinner("识图中…"):
                candidates, ocr_text = image_to_search_terms(
                    uploaded.getvalue(), gemini_api_key=api_key, mime=str(uploaded.type or "image/png")
                )
            if candidates:
                st.session_state.garden_lens_kw = candidates[0]
                st.session_state._garden_lens_pending_kw = candidates[0]
                st.rerun()

    merged_log = _merged_pick_log(pick_log)
    readonly = is_readonly_mode()
    if do_search and kw.strip():
        with st.spinner("汇总各维度数据…"):
            hit = _resolve_hit(kw)
            if not hit:
                st.warning("未找到匹配标的，请换关键词。")
            else:
                st.session_state.garden_lens_hit = {
                    "code": hit.code,
                    "name": hit.name,
                    "market": hit.market,
                    "kind": hit.kind,
                    "yahoo": hit.yahoo,
                }
                dossier = build_stock_dossier(
                    hit, fetch_fn, merged_log, pattern_adj=_pattern_adj()
                )
                st.session_state.garden_dossier = dossier.as_dict()
                st.session_state.search_history = push_search(
                    st.session_state.get("search_history"), kw.strip()
                )
                mark_dirty()

    cached = st.session_state.get("garden_dossier")
    hit_d = st.session_state.get("garden_lens_hit")
    if cached and hit_d:
        hit = eastmoney.SearchHit(
            code=str(hit_d.get("code") or ""),
            name=str(hit_d.get("name") or ""),
            market=str(hit_d.get("market") or ""),
            kind=str(hit_d.get("kind") or "A"),
            yahoo=str(hit_d.get("yahoo") or "") or None,
        )
        dossier = StockDossier(
            code=str(cached.get("code") or ""),
            name=str(cached.get("name") or ""),
            market=str(cached.get("market") or ""),
            verdict=str(cached.get("verdict") or ""),
            bullets=tuple(cached.get("bullets") or []),
            rows=tuple(cached.get("rows") or []),
            markdown=str(cached.get("markdown") or ""),
        )
        st.divider()
        _render_dossier(dossier, hit, readonly=readonly)
