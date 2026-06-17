"""Thin wrapper around Gemini with offline-safe fallbacks.

Every helper degrades gracefully: if no API key is configured (or the call
fails), `llm_json`/`llm_text` return the provided fallback so the whole graph
still runs in demo mode.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from .config import GEMINI_MODEL, GOOGLE_API_KEY, llm_available


@lru_cache(maxsize=1)
def get_llm():
    if not llm_available():
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.4,
    )


def _extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of an LLM response."""
    text = text.strip()
    # strip ```json ... ``` fences
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # find the outermost {...} or [...]
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text)


def llm_json(prompt: str, fallback: Any) -> Any:
    """Invoke Gemini expecting JSON. Returns `fallback` if unavailable/invalid."""
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        resp = llm.invoke(prompt)
        content = getattr(resp, "content", str(resp))
        return _extract_json(content)
    except Exception:
        return fallback


def llm_text(prompt: str, fallback: str = "") -> str:
    """Invoke Gemini expecting free text. Returns `fallback` if unavailable."""
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        resp = llm.invoke(prompt)
        return getattr(resp, "content", str(resp)).strip()
    except Exception:
        return fallback
