"""Geocoding + country annotations via OpenCage.

One call yields coordinates AND the data the Logistics agent needs (currency,
timezone, flag, country) — so this single tool powers both Destination and
Logistics. Requires OPENCAGE_API_KEY; returns {available: False} without it.
"""
from __future__ import annotations

from typing import Any, Dict

import requests

from ..config import OPENCAGE_API_KEY

URL = "https://api.opencagedata.com/geocode/v1/json"


def geocode(place: str) -> Dict[str, Any]:
    """Forward-geocode a place name to coordinates + country annotations."""
    if not place:
        return {"available": False, "summary": "No place to geocode."}
    if not OPENCAGE_API_KEY:
        return {"available": False, "summary": "OpenCage key not configured (set OPENCAGE_API_KEY)."}

    try:
        r = requests.get(
            URL,
            params={"q": place, "key": OPENCAGE_API_KEY, "limit": 1, "no_annotations": 0, "language": "en"},
            timeout=12,
        )
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "summary": f"Geocoding failed: {exc}"}

    results = data.get("results") or []
    if not results:
        return {"available": False, "summary": f"Could not locate '{place}'."}

    res = results[0]
    geom = res.get("geometry", {})
    comp = res.get("components", {})
    ann = res.get("annotations", {})
    currency = ann.get("currency", {}) or {}
    timezone = ann.get("timezone", {}) or {}

    city = (
        comp.get("city") or comp.get("town") or comp.get("village")
        or comp.get("municipality") or comp.get("state") or place.split(",")[0]
    )

    return {
        "available": True,
        "lat": geom.get("lat"),
        "lon": geom.get("lng"),
        "formatted": res.get("formatted", place),
        "city": city,
        "country": comp.get("country", ""),
        "country_code": (comp.get("country_code") or "").upper(),
        "currency": currency.get("name", ""),
        "currency_code": currency.get("iso_code", ""),
        "currency_symbol": currency.get("symbol", ""),
        "timezone": timezone.get("name", ""),
        "flag": ann.get("flag", ""),
    }
