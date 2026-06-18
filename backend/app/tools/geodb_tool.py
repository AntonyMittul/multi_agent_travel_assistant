"""City search / metadata via GeoDB Cities.

Uses the RapidAPI endpoint when GEODB_API_KEY is set, otherwise the free
no-key GeoDB service (rate-limited ~1 req/s). Powers the city autocomplete in
the UI and enriches the destination (population, region).
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

from ..config import GEODB_API_KEY

_RAPID_HOST = "wft-geo-db.p.rapidapi.com"
_RAPID_BASE = f"https://{_RAPID_HOST}/v1/geo/cities"
_FREE_BASE = "http://geodb-free-service.wirefreethought.com/v1/geo/cities"


def search_cities(name_prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
    if not name_prefix:
        return []

    params = {"namePrefix": name_prefix, "limit": limit, "sort": "-population",
              "types": "CITY"}
    try:
        if GEODB_API_KEY:
            r = requests.get(
                _RAPID_BASE,
                params=params,
                headers={"X-RapidAPI-Key": GEODB_API_KEY, "X-RapidAPI-Host": _RAPID_HOST},
                timeout=12,
            )
        else:
            r = requests.get(_FREE_BASE, params=params, timeout=12)
        rows = r.json().get("data", []) or []
    except Exception:
        return []

    return [{
        "city": c.get("city") or c.get("name"),
        "country": c.get("country"),
        "country_code": c.get("countryCode"),
        "region": c.get("region"),
        "lat": c.get("latitude"),
        "lon": c.get("longitude"),
        "population": c.get("population"),
    } for c in rows]


def city_facts(name: str) -> Dict[str, Any]:
    """Best single match for a city name (for destination enrichment)."""
    hits = search_cities(name.split(",")[0].strip(), limit=1)
    return hits[0] if hits else {}
