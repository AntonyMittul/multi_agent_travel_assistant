"""Destination agent: choose a place (if unspecified) and describe it."""
from __future__ import annotations

from typing import Any, Dict

from ...llm import llm_json
from ...state import TravelState, event

_FALLBACK_SUGGEST = {
    "beach": "Bali, Indonesia", "hiking": "Queenstown, New Zealand",
    "history": "Rome, Italy", "food": "Bangkok, Thailand",
    "nightlife": "Barcelona, Spain", "nature": "Banff, Canada",
    "culture": "Kyoto, Japan", "wildlife": "Nairobi, Kenya",
}


def destination(state: TravelState) -> Dict[str, Any]:
    prefs = dict(state.get("preferences", {}))
    completed = state.get("completed_agents", []) + ["destination"]
    dest = prefs.get("destination")

    if not dest:
        # autonomously pick a destination from interests / vibe
        interests = prefs.get("interests", [])
        vibe = prefs.get("vibe") or ""
        suggestion = llm_json(
            "Suggest ONE travel destination as JSON {\"destination\": \"City, Country\", "
            "\"why\": \"one sentence\"} for someone interested in "
            f"{interests or 'general travel'} with vibe '{vibe}'.",
            fallback=None,
        )
        if isinstance(suggestion, dict) and suggestion.get("destination"):
            dest = suggestion["destination"]
            why = suggestion.get("why", "")
        else:
            key = next((i for i in interests if i in _FALLBACK_SUGGEST), None)
            dest = _FALLBACK_SUGGEST.get(key, "Lisbon, Portugal")
            why = "Great all-round destination matching your interests."
        prefs["destination"] = dest
    else:
        why = ""

    profile = llm_json(
        f"Return JSON about {dest} for a traveler interested in {prefs.get('interests')}: "
        "{\"best_time\": \"...\", \"highlights\": [\"..\",\"..\",\"..\"], \"blurb\": \"2 sentences\"}.",
        fallback={
            "best_time": "Spring and autumn for mild weather.",
            "highlights": ["Old town", "Local cuisine", "Scenic viewpoints"],
            "blurb": f"{dest} offers a memorable mix of sights, food, and culture.",
        },
    )

    data = {"name": dest, "why_chosen": why, **(profile if isinstance(profile, dict) else {})}
    return {
        "preferences": prefs,
        "destination": data,
        "completed_agents": completed,
        "messages": [event("destination", "result",
                           f"Destination: {dest}. {data.get('blurb', '')}", data)],
    }
