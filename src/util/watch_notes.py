"""自选股笔记/标注（P28）：ticker -> note。"""

from __future__ import annotations

from typing import Any


def normalize_watch_notes(raw: Any) -> dict[str, str]:
    """ticker code -> note text"""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for ticker, note in raw.items():
        code = str(ticker or "").strip()
        text = str(note or "").strip()
        if code and text:
            out[code] = text
    return out


def get_note(notes: dict[str, str], ticker: str) -> str:
    return notes.get(str(ticker or "").strip(), "")


def set_note(notes: dict[str, str], ticker: str, note: str) -> dict[str, str]:
    code = str(ticker or "").strip()
    text = str(note or "").strip()
    out = dict(notes)
    if not code:
        return out
    if text:
        out[code] = text
    elif code in out:
        del out[code]
    return out


def remove_ticker_note(notes: dict[str, str], ticker: str) -> dict[str, str]:
    code = str(ticker or "").strip()
    if not code or code not in notes:
        return dict(notes)
    out = dict(notes)
    del out[code]
    return out


def remove_tickers_notes(notes: dict[str, str], tickers: list[str]) -> dict[str, str]:
    out = dict(notes)
    for t in tickers:
        code = str(t or "").strip()
        out.pop(code, None)
    return out
