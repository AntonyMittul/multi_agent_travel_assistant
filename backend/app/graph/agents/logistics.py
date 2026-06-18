"""Logistics agent: currency, language, timezone, flag.

Currency/timezone/flag/country come from the OpenCage annotations captured by
the destination agent; languages come from the local country table.
"""
from __future__ import annotations

from typing import Any, Dict

from ...state import TravelState, event
from ...tools.countries_tool import get_languages


def logistics(state: TravelState) -> Dict[str, Any]:
    completed = state.get("completed_agents", []) + ["logistics"]
    geo = state.get("destination", {}).get("geo", {})

    if not geo:
        data = {"available": False, "summary": "No geo data for logistics (geocoding unavailable)."}
        return {
            "logistics": data,
            "completed_agents": completed,
            "messages": [event("logistics", "result", data["summary"], data)],
        }

    country = geo.get("country", "")
    languages = get_languages(country)
    currency = geo.get("currency", "")
    code = geo.get("currency_code", "")
    tz = geo.get("timezone", "")

    data = {
        "available": True,
        "country": country,
        "currency": f"{currency} ({code})".strip() if currency else code,
        "currency_code": code,
        "currency_symbol": geo.get("currency_symbol", ""),
        "languages": languages,
        "timezone": tz,
        "flag": geo.get("flag", ""),
        "summary": (
            f"Currency: {currency or code or 'n/a'}; "
            f"Language(s): {', '.join(languages[:3]) or 'n/a'}; "
            f"Timezone: {tz or 'n/a'}."
        ),
    }
    return {
        "logistics": data,
        "completed_agents": completed,
        "messages": [event("logistics", "result", data["summary"], data)],
    }
