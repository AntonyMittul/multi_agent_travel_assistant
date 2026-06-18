"""Place photos via the Wikipedia search API (free, no key).

Uses a full-text search (generator=search) so a query like
"Gateway of India Mumbai" resolves to the correct article and its lead image —
much more reliable than guessing the exact page title.
"""
from __future__ import annotations

from functools import lru_cache

import requests

API = "https://en.wikipedia.org/w/api.php"
_HEADERS = {"User-Agent": "VoyageMind/1.0 (multi-agent travel assistant)"}


@lru_cache(maxsize=512)
def get_image(query: str) -> str:
    """Return the lead image URL for the best-matching Wikipedia article, or ''."""
    if not query:
        return ""
    try:
        r = requests.get(
            API,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": 1,
                "prop": "pageimages",
                "piprop": "original|thumbnail",
                "pithumbsize": 600,
                "format": "json",
            },
            headers=_HEADERS,
            timeout=10,
        )
        pages = (r.json().get("query", {}) or {}).get("pages", {})
        for p in pages.values():
            src = (p.get("original") or p.get("thumbnail") or {}).get("source", "")
            if src:
                return src
    except Exception:
        return ""
    return ""
