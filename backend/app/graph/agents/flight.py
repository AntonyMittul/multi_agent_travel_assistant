"""Flight agent: searches routes/fares (mock provider, real-API-ready)."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.flights_tool import search_flights


def flight(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    completed = state.get("completed_agents", []) + ["flight"]

    data = search_flights(
        origin=prefs.get("origin") or "",
        destination=prefs.get("destination") or "",
        depart_date=prefs.get("start_date"),
        return_date=prefs.get("end_date"),
        travelers=prefs.get("travelers", 1),
        tier=prefs.get("flight_tier", "economy"),
    )
    return {
        "flights": data,
        "completed_agents": completed,
        "messages": [event("flight", "result", data.get("summary", "No flights."), data)],
    }
