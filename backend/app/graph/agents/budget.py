"""Budget agent: aggregates every cost and checks it against the target."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event

_FOOD_PER_DAY_USD = 40       # per person
_LOCAL_TRANSPORT_USD = 15    # per person per day


def budget(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    travelers = prefs.get("travelers", 1)
    nights = prefs.get("nights", 4)
    completed = state.get("completed_agents", []) + ["budget"]

    flights = state.get("flights", {})
    hotels = state.get("hotels", {})
    activities = state.get("activities", {})

    flight_cost = flights.get("cheapest", {}).get("total_price", 0) if flights.get("available") else 0
    hotel_cost = hotels.get("best_value", {}).get("total_price", 0) if hotels.get("available") else 0
    activity_cost = activities.get("estimated_cost", 0)
    food_cost = round(_FOOD_PER_DAY_USD * nights * travelers, 2)
    transport_cost = round(_LOCAL_TRANSPORT_USD * nights * travelers, 2)

    breakdown = {
        "flights": flight_cost,
        "hotels": hotel_cost,
        "activities": activity_cost,
        "food": food_cost,
        "local_transport": transport_cost,
    }
    total = round(sum(breakdown.values()), 2)
    target = prefs.get("budget_usd")
    over = bool(target) and total > target

    data = {
        "breakdown": breakdown,
        "total": total,
        "target": target,
        "over_budget": over,
        "remaining": round(target - total, 2) if target else None,
        "hotel_tier": prefs.get("hotel_tier"),
        "flight_tier": prefs.get("flight_tier"),
    }
    if target:
        status = f"over by ${total - target:.0f}" if over else f"${target - total:.0f} under budget"
        summary = f"Estimated total ${total:.0f} vs target ${target:.0f} — {status}."
    else:
        summary = f"Estimated total trip cost: ${total:.0f} (no target set)."

    return {
        "budget": data,
        "completed_agents": completed,
        "messages": [event("budget", "result", summary, data)],
    }
