"""Finalize: assemble the merged itinerary + a natural-language summary."""
from __future__ import annotations

from typing import Any, Dict

from ...llm import llm_text
from ...state import TravelState, event


def finalize(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    dest = prefs.get("destination", "your destination")
    budget = state.get("budget", {})

    itinerary = {
        "preferences": prefs,
        "destination": state.get("destination", {}),
        "weather": state.get("weather", {}),
        "flights": state.get("flights", {}),
        "hotels": state.get("hotels", {}),
        "activities": state.get("activities", {}),
        "logistics": state.get("logistics", {}),
        "budget": budget,
        "critic": state.get("critic", {}),
    }

    fallback = (
        f"Your {prefs.get('nights')}-night trip to {dest} is ready. "
        f"Estimated cost ${budget.get('total', 0):.0f}"
        + (f" against a ${budget['target']:.0f} budget" if budget.get("target") else "")
        + ". See the breakdown and day-by-day plan below."
    )
    summary = llm_text(
        "Write a friendly 3-4 sentence summary of this trip plan for the traveler. "
        f"Destination: {dest}. Nights: {prefs.get('nights')}. "
        f"Total cost: ${budget.get('total')}. Target: {budget.get('target')}. "
        f"Highlights: {state.get('destination', {}).get('highlights')}. "
        f"Weather: {state.get('weather', {}).get('summary')}.",
        fallback=fallback,
    )
    itinerary["summary"] = summary

    return {
        "final_itinerary": itinerary,
        "messages": [event("finalize", "final", summary, {"itinerary": itinerary})],
    }
