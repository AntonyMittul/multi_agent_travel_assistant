"""Activities agent: REAL POIs + REAL restaurants near the destination
(OpenStreetMap), organized into a day-by-day plan by Gemini, with photos
(Wikipedia) attached to the headline places."""
from __future__ import annotations

from typing import Any, Dict, List

from ...llm import llm_json
from ...state import TravelState, event
from ...tools.image_tool import get_image
from ...tools.osm_tool import find_pois, find_restaurants

_PER_DAY_ACTIVITY_USD = 35  # per person per day


def _distribute(pois: List[Dict[str, Any]], restaurants: List[Dict[str, Any]],
                nights: int, rainy: bool) -> List[Dict[str, Any]]:
    names = [p["name"] for p in pois] or [
        "Walking tour of the old town", "Local market visit", "Scenic viewpoint",
        "City museum", "Waterfront stroll", "Local cuisine tasting",
    ]
    rest = restaurants or []
    plan, idx = [], 0
    for d in range(nights):
        morning = names[idx % len(names)]; idx += 1
        afternoon = names[idx % len(names)]; idx += 1
        if rest:
            r = rest[d % len(rest)]
            evening = f"Dinner at {r['name']}" + (f" ({r['cuisine']})" if r.get("cuisine") else "")
        else:
            evening = "Dinner at a recommended local restaurant"
        plan.append({
            "day": d + 1,
            "morning": morning,
            "afternoon": ("Indoor: " if rainy else "") + afternoon,
            "evening": evening,
        })
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
    pois = find_pois(lat, lon) if lat is not None else []
    restaurants = find_restaurants(lat, lon) if lat is not None else []

    poi_names = [p["name"] for p in pois]
    rest_desc = [f"{r['name']}" + (f" ({r['cuisine']})" if r.get("cuisine") else "") for r in restaurants]

    plan = llm_json(
        f"Create a {nights}-day itinerary for {dest}. Traveler interests: {interests}. "
        f"Weather: {'rainy, prefer indoor options' if rainy else 'mostly dry'}. "
        f"Use these REAL nearby attractions for morning/afternoon: {poi_names[:20]}. "
        f"Use these REAL restaurants for the evening (vary them): {rest_desc[:12]}. "
        "Return ONLY a JSON array; each item: "
        "{\"day\": int, \"morning\": str, \"afternoon\": str, \"evening\": str}. "
        "Make morning/afternoon specific real places and evening a specific real restaurant.",
        fallback=_distribute(pois, restaurants, nights, rainy),
    )
    if not isinstance(plan, list) or not plan:
        plan = _distribute(pois, restaurants, nights, rainy)

    # attach photos to the headline places (bounded to keep it fast)
    for p in pois[:6]:
        p["image"] = get_image(f"{p['name']}")

    est_cost = round(_PER_DAY_ACTIVITY_USD * nights * travelers, 2)
    data = {
        "plan": plan,
        "estimated_cost": est_cost,
        "days": len(plan),
        "pois": pois[:25],
        "restaurants": restaurants[:12],
        "source": "OpenStreetMap POIs & restaurants",
    }
    return {
        "activities": data,
        "completed_agents": completed,
        "messages": [event("activities", "result",
                           f"Built a {len(plan)}-day plan from {len(pois)} attractions and "
                           f"{len(restaurants)} restaurants.", data)],
    }
