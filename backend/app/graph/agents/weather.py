"""Weather agent: real 7-day forecast via Open-Meteo."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.weather_tool import get_weather


def weather(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    dest = prefs.get("destination") or ""
    completed = state.get("completed_agents", []) + ["weather"]

    data = get_weather(dest)
    return {
        "weather": data,
        "completed_agents": completed,
        "messages": [event("weather", "result", data.get("summary", "No weather data."), data)],
    }
