"""Place photos (free, no key).

Two sources, tried in order:
1. Wikipedia search → article lead image (best for famous landmarks).
2. Openverse → CC-licensed photo search (covers smaller places like beaches,
   piers and parks that lack a Wikipedia article image).
"""
from __future__ import annotations

from functools import lru_cache

import requests

WIKI_API = "https://en.wikipedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
_HEADERS = {"User-Agent": "Navora/1.0 (multi-agent travel assistant)"}


def _wikipedia(query: str) -> str:
    try:
        r = requests.get(
            WIKI_API,
            params={
                "action": "query", "generator": "search", "gsrsearch": query,
                "gsrlimit": 1, "prop": "pageimages", "piprop": "original|thumbnail",
                "pithumbsize": 600, "format": "json",
            },
            headers=_HEADERS, timeout=10,
        )
        pages = (r.json().get("query", {}) or {}).get("pages", {})
        for p in pages.values():
            src = (p.get("original") or p.get("thumbnail") or {}).get("source", "")
            # skip SVGs — they're maps/diagrams/logos, not photos
            if src and ".svg" not in src.lower():
                return src
    except Exception:
        return ""
    return ""


def _openverse(query: str) -> str:
    try:
        r = requests.get(
            OPENVERSE_API,
            params={"q": query, "page_size": 1, "mature": "false"},
            headers=_HEADERS, timeout=10,
        )
        if r.status_code != 200:
            return ""
        results = r.json().get("results", [])
        if results:
            return results[0].get("thumbnail") or results[0].get("url") or ""
    except Exception:
        return ""
    return ""


@lru_cache(maxsize=512)
def get_image(query: str) -> str:
    """Return a photo URL for the place, or '' if none found."""
    if not query:
        return ""
    return _wikipedia(query) or _openverse(query)
