"""Hotel agent: REAL hotels near the destination from OpenStreetMap, with
ESTIMATED nightly rates (OSM has no prices). Rates are flagged estimated."""
from __future__ import annotations

from typing import Any, Dict, List

from ...state import TravelState, event
from ...tools.osm_tool import find_hotels

# base nightly rate (USD) by tier; refined by OSM star rating when present
_TIER_BASE = {"budget": 38, "mid": 95, "luxury": 230}


def _estimate_rate(stars: float | None, tier: str) -> float:
    base = _TIER_BASE.get(tier, 95)
    if stars:
        # blend tier base with a star-driven rate
        return round((base + stars * 28) / 2 + base / 2, 2)
    return float(base)


def hotel(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    completed = state.get("completed_agents", []) + ["hotel"]
    nights = prefs.get("nights", 4)
    travelers = prefs.get("travelers", 1)
    tier = prefs.get("hotel_tier", "mid")
    rooms = max(1, (travelers + 1) // 2)

    geo = state.get("destination", {}).get("geo", {})
    lat, lon = geo.get("lat"), geo.get("lon")
    raw = find_hotels(lat, lon) if lat is not None else []

    options: List[Dict[str, Any]] = []
    for h in raw:
        rate = _estimate_rate(h.get("stars"), tier)
        options.append({
            "name": h["name"],
            "lat": h.get("lat"),
            "lon": h.get("lon"),
            "stars": h.get("stars"),
            "website": h.get("website", ""),
            "tier": tier,
            "nightly_rate": rate,
            "rooms": rooms,
            "nights": nights,
            "total_price": round(rate * rooms * nights, 2),
            "price_estimated": True,
        })

    if not options:
        data = {
            "available": False,
            "destination": prefs.get("destination"),
            "summary": "No hotels found via OpenStreetMap near this location.",
            "options": [],
        }
        return {
            "hotels": data,
            "completed_agents": completed,
            "messages": [event("hotel", "result", data["summary"], data)],
        }

    options.sort(key=lambda o: o["total_price"])
    best = options[0]
    data = {
        "available": True,
        "destination": prefs.get("destination"),
        "tier": tier,
        "nights": nights,
        "source": "OpenStreetMap (real listings, estimated rates)",
        "price_estimated": True,
        "options": options[:8],
        "best_value": best,
        "summary": (
            f"{best['name']}"
            f"{' (' + str(best['stars']) + '★)' if best['stars'] else ''} "
            f"~${best['nightly_rate']:.0f}/night est. — ${best['total_price']:.0f} for {nights} night(s). "
            f"{len(options)} real OSM listings found."
        ),
    }
    return {
        "hotels": data,
        "completed_agents": completed,
        "messages": [event("hotel", "result", data["summary"], data)],
    }
