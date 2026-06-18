"""Flight agent: real schedules/airlines via AviationStack + estimated fares."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.flights_tool import search_flights
from ...tools.geo_tool import geocode


def flight(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    completed = state.get("completed_agents", []) + ["flight"]
    origin = prefs.get("origin") or ""

    if not origin:
        data = {"available": False, "summary": "No origin city given — skipping flights."}
        return {
            "flights": data,
            "completed_agents": completed,
            "messages": [event("flight", "result", data["summary"], data)],
        }

    dest_geo = state.get("destination", {}).get("geo", {})
    dest_coords = (dest_geo.get("lat"), dest_geo.get("lon")) if dest_geo.get("lat") else None
    o_geo = geocode(origin)
    origin_coords = (o_geo.get("lat"), o_geo.get("lon")) if o_geo.get("available") else None

    data = search_flights(
        origin_city=origin,
        dest_city=prefs.get("destination") or "",
        depart_date=prefs.get("start_date"),
        return_date=prefs.get("end_date"),
        travelers=prefs.get("travelers", 1),
        tier=prefs.get("flight_tier", "economy"),
        origin_coords=origin_coords,
        dest_coords=dest_coords,
    )
    return {
        "flights": data,
        "completed_agents": completed,
        "messages": [event("flight", "result", data.get("summary", "No flights."), data)],
    }
