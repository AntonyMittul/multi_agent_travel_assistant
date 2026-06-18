"""Destination agent: choose a place (if unspecified), geocode it (OpenCage),
enrich it (GeoDB + Gemini). Stores geo coords used by every downstream agent.
"""
from __future__ import annotations

from typing import Any, Dict

from ...llm import llm_json
from ...state import TravelState, event
from ...tools.geo_tool import geocode
from ...tools.image_tool import get_image

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
    why = ""

    if not dest:
        interests = prefs.get("interests", [])
        vibe = prefs.get("vibe") or ""
        suggestion = llm_json(
            "Suggest ONE travel destination as JSON {\"destination\": \"City, Country\", "
            "\"why\": \"one sentence\"} for someone interested in "
            f"{interests or 'general travel'} with vibe '{vibe}'.",
            fallback=None,
        )
        if isinstance(suggestion, dict) and suggestion.get("destination"):
            dest, why = suggestion["destination"], suggestion.get("why", "")
        else:
            key = next((i for i in interests if i in _FALLBACK_SUGGEST), None)
            dest = _FALLBACK_SUGGEST.get(key, "Lisbon, Portugal")
            why = "Great all-round destination matching your interests."
        prefs["destination"] = dest

    # ---- normalize to a real base city + descriptive profile (Gemini) ----
    # Critical: a broad region/state/island (e.g. "Kashmir") must resolve to the
    # gateway city ("Srinagar") or geocoding lands on an obscure same-named village.
    profile = llm_json(
        f"For a trip to '{dest}' (traveler interests: {prefs.get('interests')}), return JSON: "
        '{"place": "the single best \\"City, Country\\" to base this trip — if the '
        "destination is already a clear city keep it; if it is a broad region/state/"
        'island/country pick its main city or tourist gateway", '
        '"best_time": "...", "highlights": ["..","..",".."], "blurb": "2 sentences"}.',
        fallback={
            "place": dest,
            "best_time": "Spring and autumn for mild weather.",
            "highlights": ["Old town", "Local cuisine", "Scenic viewpoints"],
            "blurb": f"{dest} offers a memorable mix of sights, food, and culture.",
        },
    )
    canonical = (profile.get("place") if isinstance(profile, dict) else None) or dest
    canonical = str(canonical).strip()
    prefs["destination"] = canonical

    # ---- real geocoding + annotations (OpenCage) on the canonical city ----
    geo = geocode(canonical)

    # hero photo via Wikipedia search
    image = get_image((geo.get("city") if geo.get("available") else None) or canonical)

    data = {
        "name": canonical,
        "why_chosen": why,
        "geo": geo if geo.get("available") else {},
        "image": image,
        **({k: v for k, v in profile.items() if k != "place"} if isinstance(profile, dict) else {}),
    }
    note = "" if geo.get("available") else f" ({geo.get('summary', 'geocoding unavailable')})"
    return {
        "preferences": prefs,
        "destination": data,
        "completed_agents": completed,
        "messages": [event("destination", "result",
                           f"Destination: {canonical}.{note} {data.get('blurb', '')}", data)],
    }
