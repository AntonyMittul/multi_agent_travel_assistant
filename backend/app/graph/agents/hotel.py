"""Hotel agent: lodging matched to the (possibly downgraded) tier."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.hotels_tool import search_hotels


def hotel(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    completed = state.get("completed_agents", []) + ["hotel"]

    data = search_hotels(
        destination=prefs.get("destination") or "",
        nights=prefs.get("nights", 4),
        travelers=prefs.get("travelers", 1),
        tier=prefs.get("hotel_tier", "mid"),
    )
    return {
        "hotels": data,
        "completed_agents": completed,
        "messages": [event("hotel", "result", data.get("summary", "No hotels."), data)],
    }
