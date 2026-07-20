"""截图识股：OCR 提文字 → 正则抽代码（可选 Gemini Vision）。"""

from __future__ import annotations

import base64
import re
from typing import Any

import requests

_TICKER_PATTERNS = (
    re.compile(r"\b([036]\d{5})\b"),  # A股6位
    re.compile(r"\b(\d{4,5})\.HK\b", re.I),
    re.compile(r"\b([A-Z]{1,5})\b"),  # 美股（弱匹配，后置过滤）
)
_US_STOP = frozenset(
    "THE AND FOR USD CNY HK US NYSE NASDAQ ETF API OCR JPG PNG".split()
)


def extract_ticker_candidates(text: str, *, limit: int = 8) -> list[str]:
    """从任意文本中提取可能的股票代码。"""
    raw = (text or "").strip()
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(c: str) -> None:
        c = c.strip().upper()
        if not c or c in seen:
            return
        seen.add(c)
        out.append(c)

    for m in re.finditer(r"\b([036]\d{5})\b", raw):
        add(m.group(1))
    for m in re.finditer(r"\b(\d{4,5})\s*\.?\s*HK\b", raw, re.I):
        add(f"{int(m.group(1)):04d}.HK")
    for m in re.finditer(r"\b([A-Z]{1,5})\b", raw):
        t = m.group(1)
        if t in _US_STOP or len(t) == 1:
            continue
        add(t)
    # 中文名常见无代码 — 保留整句给 suggest
    if not out and len(raw) <= 24 and re.search(r"[\u4e00-\u9fff]", raw):
        add(raw)
    return out[:limit]


def ocr_image_with_gemini(image_bytes: bytes, api_key: str, *, mime: str = "image/png") -> str:
    """用 Gemini Vision 从截图提取文字（需配置 API Key）。"""
    key = (api_key or "").strip()
    if not key or not image_bytes:
        return ""
    b64 = base64.b64encode(image_bytes).decode("ascii")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={key}"
    )
    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "这是股票软件截图。请只输出其中出现的股票代码或中文简称，"
                            "多个用空格分隔，不要解释。"
                        )
                    },
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ]
            }
        ]
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        parts = (
            (data.get("candidates") or [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        texts = [str(p.get("text") or "") for p in parts if isinstance(p, dict)]
        return " ".join(texts).strip()
    except Exception:
        return ""


def image_to_search_terms(
    image_bytes: bytes,
    *,
    gemini_api_key: str = "",
    mime: str = "image/png",
) -> tuple[list[str], str]:
    """图片 → 候选搜索词列表 + OCR 原文。"""
    text = ""
    if gemini_api_key:
        text = ocr_image_with_gemini(image_bytes, gemini_api_key, mime=mime)
    candidates = extract_ticker_candidates(text)
    return candidates, text
