"""Logistics agent: currency, language, timezone via REST Countries."""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.countries_tool import get_country_info


def logistics(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    completed = state.get("completed_agents", []) + ["logistics"]

    # Prefer the country resolved by the weather agent's geocoding; fall back
    # to parsing the destination string ("City, Country").
    country = state.get("weather", {}).get("location", {}).get("country")
    if not country:
        dest = prefs.get("destination") or ""
        country = dest.split(",")[-1].strip() if "," in dest else dest

    data = get_country_info(country)
    return {
        "logistics": data,
        "completed_agents": completed,
        "messages": [event("logistics", "result", data.get("summary", "No logistics data."), data)],
    }
