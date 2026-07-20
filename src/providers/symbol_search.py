"""全球证券搜索：东财（沪深京 + 部分港股）与 Yahoo（美股/港股/全球英文名）并行。"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.providers.eastmoney import SearchHit, suggest as em_suggest
from src.providers.yahoo_search import search_yahoo

# 常见中文名 → 同时触发 Yahoo 精确查
_CN_ALIASES_FOR_YAHOO: dict[str, str] = {
    "苹果": "AAPL",
    "英伟达": "NVDA",
    "特斯拉": "TSLA",
    "微软": "MSFT",
    "亚马逊": "AMZN",
    "谷歌": "GOOGL",
    "腾讯": "0700.HK",
    "阿里巴巴": "BABA",
    "美团": "3690.HK",
    "台积电": "TSM",
}


def _is_mostly_latin(kw: str) -> bool:
    letters = re.findall(r"[A-Za-z]", kw)
    han = re.findall(r"[\u4e00-\u9fff]", kw)
    return len(letters) >= 2 and len(letters) >= len(han)


def _dedupe_key(h: SearchHit) -> str:
    return (h.yahoo or h.code).upper()


def _relevance_score(h: SearchHit, kw: str, *, latin_bias: bool) -> float:
    k = kw.lower()
    code = h.code.lower()
    name = h.name.lower()
    score = 0.0
    if code == k or (h.yahoo or "").lower() == k:
        score += 100
    if k in name or k in code:
        score += 50
    if h.kind == "US" and latin_bias:
        score += 30
    if h.kind == "A" and not latin_bias:
        score += 30
    if h.kind == "HK":
        score += 15
    return score


def _merge_hits(em: list[SearchHit], yh: list[SearchHit], kw: str, *, limit: int) -> list[SearchHit]:
    latin = _is_mostly_latin(kw)
    seen: set[str] = set()
    pool: list[SearchHit] = []

    for h in yh + em if latin else em + yh:
        key = _dedupe_key(h)
        if key in seen:
            continue
        seen.add(key)
        pool.append(h)

    pool.sort(key=lambda h: _relevance_score(h, kw, latin_bias=latin), reverse=True)
    return pool[:limit]


def suggest(keyword: str, limit: int = 40) -> list[SearchHit]:
    """
    全球并行搜索（默认每次同时查东财 + Yahoo，不再「只有 A 股」）。
    """
    kw = (keyword or "").strip()
    if not kw:
        return []

    half = max(limit // 2, 15)
    em_hits: list[SearchHit] = []
    yh_hits: list[SearchHit] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        f_em = pool.submit(em_suggest, kw, limit=half)
        f_yh = pool.submit(search_yahoo, kw, limit=half)
        for fut in as_completed([f_em, f_yh]):
            try:
                if fut is f_em:
                    em_hits = fut.result()
                else:
                    yh_hits = fut.result()
            except Exception:
                pass

    return _merge_hits(em_hits, yh_hits, kw, limit=limit)


def count_by_kind(hits: list[SearchHit]) -> dict[str, int]:
    c = {"A": 0, "HK": 0, "US": 0, "OTHER": 0}
    for h in hits:
        k = h.kind if h.kind in c else "OTHER"
        c[k] += 1
    return c
