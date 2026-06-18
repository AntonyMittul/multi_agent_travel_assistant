"""Activities agent.

Attraction selection (the part travelers judge first) uses Gemini's world
knowledge to pick the iconic must-sees for the destination, geocoded via
OpenCage for the map and illustrated via Wikipedia search. Falls back to
OpenStreetMap POIs (ranked by notability) when Gemini is unavailable.
Restaurants for the evening come from real OSM data.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ...llm import llm_json
from ...state import TravelState, event
from ...tools.geo_tool import geocode
from ...tools.image_tool import get_image
from ...tools.osm_tool import find_pois, find_restaurants

_PER_DAY_ACTIVITY_USD = 35  # per person per day
_MAX_PLACES = 6             # geocoded + photographed places (bounds API calls)


def _distribute(place_names: List[str], restaurants: List[Dict[str, Any]],
                nights: int, rainy: bool) -> List[Dict[str, Any]]:
    names = place_names or [
        "Old town walking tour", "Local market", "Scenic viewpoint",
        "City museum", "Waterfront promenade", "Cultural landmark",
    ]
    rest, plan, idx = restaurants or [], [], 0
    for d in range(nights):
        morning = names[idx % len(names)]; idx += 1
        afternoon = names[idx % len(names)]; idx += 1
        if rest:
            r = rest[d % len(rest)]
            evening = f"Dinner at {r['name']}" + (f" ({r['cuisine']})" if r.get("cuisine") else "")
        else:
            evening = "Dinner at a recommended local restaurant"
        plan.append({"day": d + 1, "morning": morning,
                     "afternoon": ("Indoor: " if rainy else "") + afternoon, "evening": evening})
    return plan


def activities(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    dest = prefs.get("destination") or ""
    nights = prefs.get("nights", 4)
    travelers = prefs.get("travelers", 1)
    interests = prefs.get("interests", [])
    rainy = bool(state.get("weather", {}).get("rainy"))
    completed = state.get("completed_agents", []) + ["activities"]

    geo = state.get("destination", {}).get("geo", {})
    lat, lon = geo.get("lat"), geo.get("lon")
    city = geo.get("city") or dest.split(",")[0].strip()
    restaurants = find_restaurants(lat, lon) if lat is not None else []
    rest_desc = [r["name"] + (f" ({r['cuisine']})" if r.get("cuisine") else "") for r in restaurants]

    # ---- Gemini: iconic attractions + day plan in one shot ----
    result = llm_json(
        f"Plan a {nights}-day trip to {dest}. Traveler interests: {interests}. "
        f"Weather: {'rainy, prefer indoor options' if rainy else 'mostly dry'}. "
        f"Real restaurants for dinners (use and vary these): {rest_desc[:12]}.\n"
        "Return ONLY JSON with two keys:\n"
        '1) "attractions": 6 of the most iconic, must-see, well-known attractions a '
        'first-time visitor would want (famous landmarks, not obscure spots), each '
        '{"name": str, "note": short str}.\n'
        '2) "plan": array of day objects {"day": int, "morning": str, "afternoon": str, '
        '"evening": str}, using those attractions for morning/afternoon and a specific '
        "real restaurant for the evening.",
        fallback=None,
    )

    places: List[Dict[str, Any]] = []
    plan: List[Dict[str, Any]] = []

    if isinstance(result, dict) and result.get("attractions"):
        for a in result["attractions"][:_MAX_PLACES]:
            name = a.get("name") if isinstance(a, dict) else str(a)
            if not name:
                continue
            g = geocode(f"{name}, {dest}")  # OpenCage → coords for the map
            places.append({
                "name": name,
                "category": "attraction",
                "note": a.get("note", "") if isinstance(a, dict) else "",
                "lat": g.get("lat"),
                "lon": g.get("lon"),
                "image": get_image(f"{name} {city}"),
            })
        plan = result.get("plan") if isinstance(result.get("plan"), list) else []

    # ---- fallback: OSM POIs ranked by notability ----
    if not places:
        pois = find_pois(lat, lon) if lat is not None else []
        for p in pois[:_MAX_PLACES]:
            p["image"] = get_image(f"{p['name']} {city}")
            places.append(p)
    if not plan:
        plan = _distribute([p["name"] for p in places], restaurants, nights, rainy)

    est_cost = round(_PER_DAY_ACTIVITY_USD * nights * travelers, 2)
    data = {
        "plan": plan,
        "estimated_cost": est_cost,
        "days": len(plan),
        "pois": places,                # famous places: name, coords, image
        "restaurants": restaurants[:12],
        "source": "Gemini picks + OpenStreetMap restaurants",
    }
    return {
        "activities": data,
        "completed_agents": completed,
        "messages": [event("activities", "result",
                           f"Built a {len(plan)}-day plan around {len(places)} top attractions "
                           f"and {len(restaurants)} restaurants.", data)],
    }
