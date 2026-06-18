"""Real hotels & points-of-interest from OpenStreetMap via the Overpass API.

Free, no key. Returns real, mappable places (name + coordinates). OSM has no
prices, so the hotel agent estimates nightly rates separately.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

# Overpass mirrors — tried in order for resilience against rate-limiting.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
# OSM services require a descriptive User-Agent or they return 406.
_HEADERS = {"User-Agent": "VoyageMind/1.0 (multi-agent travel assistant)"}

# POI categories we surface for the activities agent
_POI_FILTERS = [
    'node["tourism"~"attraction|museum|viewpoint|gallery|artwork|zoo|theme_park|aquarium"]',
    'node["historic"]',
    'node["leisure"="park"]',
]


def _overpass(query: str) -> List[Dict[str, Any]]:
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": query}, headers=_HEADERS, timeout=35)
            if r.status_code == 200:
                els = r.json().get("elements", [])
                if els:
                    return els
        except Exception:
            continue
    return []


def _coords(el: Dict[str, Any]):
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    center = el.get("center", {})
    return center.get("lat"), center.get("lon")


def find_hotels(lat: float, lon: float, radius_m: int = 9000, limit: int = 20) -> List[Dict[str, Any]]:
    if lat is None or lon is None:
        return []
    q = (
        f"[out:json][timeout:30];"
        f'(node["tourism"="hotel"](around:{radius_m},{lat},{lon});'
        f'way["tourism"="hotel"](around:{radius_m},{lat},{lon}););'
        f"out center {limit * 3};"
    )
    hotels = []
    for el in _overpass(q):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        la, lo = _coords(el)
        stars = tags.get("stars")
        try:
            stars = float(stars) if stars else None
        except ValueError:
            stars = None
        hotels.append({
            "name": name,
            "lat": la,
            "lon": lo,
            "stars": stars,
            "website": tags.get("website") or tags.get("contact:website", ""),
        })
        if len(hotels) >= limit:
            break
    return hotels


def find_restaurants(lat: float, lon: float, radius_m: int = 7000, limit: int = 12) -> List[Dict[str, Any]]:
    """Real restaurants/cafes near the destination (name + cuisine + coords)."""
    if lat is None or lon is None:
        return []
    q = (
        f"[out:json][timeout:30];"
        f'(node["amenity"~"restaurant|cafe"]["name"](around:{radius_m},{lat},{lon}););'
        f"out {limit * 3};"
    )
    out, seen = [], set()
    for el in _overpass(q):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        la, lo = _coords(el)
        out.append({
            "name": name,
            "cuisine": (tags.get("cuisine") or "").replace("_", " ").replace(";", ", "),
            "lat": la,
            "lon": lo,
        })
        if len(out) >= limit:
            break
    return out


def find_pois(lat: float, lon: float, radius_m: int = 9000, limit: int = 25) -> List[Dict[str, Any]]:
    if lat is None or lon is None:
        return []
    inner = "".join(f"{f}(around:{radius_m},{lat},{lon});" for f in _POI_FILTERS)
    q = f"[out:json][timeout:30];({inner});out center {limit * 3};"

    seen, pois = set(), []
    for el in _overpass(q):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        category = (
            tags.get("tourism") or tags.get("historic")
            or ("park" if tags.get("leisure") == "park" else "place")
        )
        la, lo = _coords(el)
        # famous landmarks almost always have a wikidata/wikipedia tag — use it
        # as a popularity proxy to rank them ahead of minor POIs.
        notable = bool(tags.get("wikidata") or tags.get("wikipedia"))
        pois.append({"name": name, "category": category, "lat": la, "lon": lo,
                     "notable": notable})

    pois.sort(key=lambda p: not p["notable"])  # notable first
    return pois[:limit]
