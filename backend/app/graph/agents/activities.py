"""Activities agent: REAL POIs near the destination (OpenStreetMap), organized
into a day-by-day plan by Gemini (templated distribution as fallback)."""
from __future__ import annotations

from typing import Any, Dict, List

from ...llm import llm_json
from ...state import TravelState, event
from ...tools.osm_tool import find_pois

_PER_DAY_ACTIVITY_USD = 35  # per person per day


def _distribute(pois: List[Dict[str, Any]], nights: int, rainy: bool) -> List[Dict[str, Any]]:
    names = [p["name"] for p in pois] or [
        "Walking tour of the old town", "Local market visit", "Scenic viewpoint",
        "City museum", "Waterfront stroll", "Local cuisine tasting",
    ]
    plan = []
    idx = 0
    for d in range(nights):
        morning = names[idx % len(names)]; idx += 1
        afternoon = names[idx % len(names)]; idx += 1
        plan.append({
            "day": d + 1,
            "morning": morning,
            "afternoon": ("Indoor: " if rainy else "") + afternoon,
            "evening": "Dinner at a recommended local restaurant",
        })
    return plan


def activities(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    nights = prefs.get("nights", 4)
    travelers = prefs.get("travelers", 1)
    interests = prefs.get("interests", [])
    rainy = bool(state.get("weather", {}).get("rainy"))
    completed = state.get("completed_agents", []) + ["activities"]

    geo = state.get("destination", {}).get("geo", {})
    lat, lon = geo.get("lat"), geo.get("lon")
    pois = find_pois(lat, lon) if lat is not None else []
    poi_names = [p["name"] for p in pois]

    plan = llm_json(
        f"Create a {nights}-day itinerary for {prefs.get('destination')}. "
        f"Traveler interests: {interests}. Weather: {'rainy, prefer indoor' if rainy else 'mostly dry'}. "
        f"Use these REAL nearby places where sensible: {poi_names[:20]}. "
        "Return ONLY a JSON array; each item: "
        "{\"day\": int, \"morning\": str, \"afternoon\": str, \"evening\": str}.",
        fallback=_distribute(pois, nights, rainy),
    )
    if not isinstance(plan, list) or not plan:
        plan = _distribute(pois, nights, rainy)

    est_cost = round(_PER_DAY_ACTIVITY_USD * nights * travelers, 2)
    data = {
        "plan": plan,
        "estimated_cost": est_cost,
        "days": len(plan),
        "pois": pois[:25],
        "source": "OpenStreetMap POIs",
    }
    return {
        "activities": data,
        "completed_agents": completed,
        "messages": [event("activities", "result",
                           f"Built a {len(plan)}-day plan from {len(pois)} real OSM places "
                           f"(~${est_cost:.0f} in activities).", data)],
    }
