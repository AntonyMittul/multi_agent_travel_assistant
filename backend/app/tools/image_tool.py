"""Place photos via the Wikipedia REST API (free, no key).

Returns a thumbnail image URL for a place/landmark name, or '' if none.
"""
from __future__ import annotations

from functools import lru_cache

import requests

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_HEADERS = {"User-Agent": "VoyageMind/1.0 (multi-agent travel assistant)"}


@lru_cache(maxsize=256)
def get_image(title: str) -> str:
    if not title:
        return ""
    # Wikipedia titles use underscores; the API also accepts spaces.
    name = title.split(",")[0].strip().replace(" ", "_")
    try:
        r = requests.get(SUMMARY_URL.format(title=name), headers=_HEADERS, timeout=10)
        if r.status_code != 200:
            return ""
        data = r.json()
        # prefer the larger original image, fall back to the thumbnail
        return (data.get("originalimage") or data.get("thumbnail") or {}).get("source", "")
    except Exception:
        return ""
