"""Activities agent: builds a day-by-day plan from interests + weather."""
from __future__ import annotations

from typing import Any, Dict, List

from ...llm import llm_json
from ...state import TravelState, event

_PER_DAY_ACTIVITY_USD = 35  # rough estimate per person per day


def _fallback_plan(dest: str, nights: int, interests: List[str], rainy: bool) -> List[Dict[str, Any]]:
    pool_outdoor = ["Walking tour of the old town", "Visit a local market", "Scenic viewpoint hike",
                    "Botanical gardens", "Waterfront stroll", "Day trip to nearby nature"]
    pool_indoor = ["City history museum", "Art gallery", "Cooking class", "Local cafe crawl",
                   "Indoor cultural show", "Artisan workshop"]
    pool = (pool_indoor if rainy else pool_outdoor) + pool_outdoor
    plan = []
    for d in range(nights):
        plan.append({
            "day": d + 1,
            "morning": pool[(d * 2) % len(pool)],
            "afternoon": pool[(d * 2 + 1) % len(pool)],
            "evening": "Dinner at a recommended local restaurant",
        })
    return plan


def activities(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    dest = prefs.get("destination") or "your destination"
    nights = prefs.get("nights", 4)
    interests = prefs.get("interests", [])
    rainy = bool(state.get("weather", {}).get("rainy"))
    travelers = prefs.get("travelers", 1)
    completed = state.get("completed_agents", []) + ["activities"]

    plan = llm_json(
        f"Create a {nights}-day activity plan for {dest}. Traveler interests: {interests}. "
        f"Weather is {'rainy — prefer indoor options' if rainy else 'mostly dry'}. "
        "Return ONLY a JSON array; each item: "
        "{\"day\": int, \"morning\": str, \"afternoon\": str, \"evening\": str}.",
        fallback=_fallback_plan(dest, nights, interests, rainy),
    )
    if not isinstance(plan, list) or not plan:
        plan = _fallback_plan(dest, nights, interests, rainy)

    est_cost = round(_PER_DAY_ACTIVITY_USD * nights * travelers, 2)
    data = {"plan": plan, "estimated_cost": est_cost, "days": len(plan)}
    return {
        "activities": data,
        "completed_agents": completed,
        "messages": [event("activities", "result",
                           f"Built a {len(plan)}-day plan (~${est_cost:.0f} in activities).", data)],
    }
