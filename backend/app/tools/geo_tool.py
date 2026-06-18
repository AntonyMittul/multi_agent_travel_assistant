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


def geocode(place: str, proximity: tuple | None = None,
            countrycode: str | None = None) -> Dict[str, Any]:
    """Forward-geocode a place name to coordinates + country annotations.

    `proximity` (lat, lon) biases results toward that point and `countrycode`
    restricts them to a country — both critical when geocoding an attraction
    name (e.g. a beach) that could match somewhere on the other side of the
    world.
    """
    if not place:
        return {"available": False, "summary": "No place to geocode."}
    if not OPENCAGE_API_KEY:
        return {"available": False, "summary": "OpenCage key not configured (set OPENCAGE_API_KEY)."}

    params = {"q": place, "key": OPENCAGE_API_KEY, "limit": 1,
              "no_annotations": 0, "language": "en"}
    if proximity and proximity[0] is not None and proximity[1] is not None:
        params["proximity"] = f"{proximity[0]},{proximity[1]}"
    if countrycode:
        params["countrycode"] = countrycode.lower()

    try:
        r = requests.get(URL, params=params, timeout=12)
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
