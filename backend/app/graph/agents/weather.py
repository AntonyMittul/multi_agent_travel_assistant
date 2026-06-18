"""Weather agent: real 7-day forecast via Open-Meteo, using the destination's
OpenCage coordinates (no second geocode)."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.weather_tool import get_weather


def weather(state: TravelState) -> Dict[str, Any]:
    completed = state.get("completed_agents", []) + ["weather"]
    geo = state.get("destination", {}).get("geo", {})
    lat, lon = geo.get("lat"), geo.get("lon")
    label = geo.get("formatted") or state.get("destination", {}).get("name", "")

    if lat is None or lon is None:
        data = {"available": False, "summary": "No coordinates available for weather."}
    else:
        data = get_weather(lat, lon, label)

    return {
        "weather": data,
        "completed_agents": completed,
        "messages": [event("weather", "result", data.get("summary", "No weather data."), data)],
    }
