"""Critic agent: validates the merged plan and triggers autonomous replans.

This is the system's self-correction loop. If the trip is over budget, the
critic downgrades tiers and sends the affected agents back to work — bounded by
MAX_REVISIONS so it can never loop forever (the key fail-safe).
"""
from __future__ import annotations

from typing import Any, Dict

from ...config import MAX_REVISIONS
from ...state import TravelState, event

# next-cheaper tier to fall back to when over budget
_HOTEL_DOWNGRADE = {"luxury": "mid", "mid": "budget"}
_FLIGHT_DOWNGRADE = {"business": "premium", "premium": "economy"}


def critic(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    budget = state.get("budget", {})
    revision = state.get("revision_count", 0)
    issues = []

    over = budget.get("over_budget")
    can_downgrade = (
        prefs.get("hotel_tier") in _HOTEL_DOWNGRADE
        or prefs.get("flight_tier") in _FLIGHT_DOWNGRADE
    )

    # ---- decide whether to replan ----
    if over and revision < MAX_REVISIONS and can_downgrade:
        constraints = dict(state.get("constraints", {}))
        actions = []
        if prefs.get("hotel_tier") in _HOTEL_DOWNGRADE:
            constraints["hotel_tier"] = _HOTEL_DOWNGRADE[prefs["hotel_tier"]]
            actions.append(f"hotel→{constraints['hotel_tier']}")
        if prefs.get("flight_tier") in _FLIGHT_DOWNGRADE:
            constraints["flight_tier"] = _FLIGHT_DOWNGRADE[prefs["flight_tier"]]
            actions.append(f"flight→{constraints['flight_tier']}")

        # send the cost-bearing agents back to re-run with new constraints
        rerun = {"flight", "hotel", "activities", "budget"}
        completed = [a for a in state.get("completed_agents", []) if a not in rerun]

        verdict = {
            "verdict": "revise",
            "issues": [f"Over budget by ${budget['total'] - budget['target']:.0f}."],
            "action": f"Replanning (downgrade {', '.join(actions)}).",
        }
        return {
            "critic": verdict,
            "constraints": constraints,
            "completed_agents": completed,
            "revision_count": revision + 1,
            "messages": [event("critic", "revise",
                               f"Plan over budget — auto-adjusting: {', '.join(actions)}.", verdict)],
        }

    # ---- approve (or accept best-effort after exhausting revisions) ----
    if over:
        issues.append("Still over budget after max revisions — flagged for the traveler.")
    if state.get("weather", {}).get("rainy"):
        issues.append("Rain likely — itinerary favors indoor options.")
    if not state.get("flights", {}).get("available"):
        issues.append("No flights found (check origin city).")

    verdict = {"verdict": "approved", "issues": issues, "action": "Finalizing itinerary."}
    return {
        "critic": verdict,
        "messages": [event("critic", "approve",
                           "Plan validated. " + (" ".join(issues) if issues else "All checks passed."),
                           verdict)],
    }


def route_from_critic(state: TravelState) -> str:
    """Conditional-edge function: replan or finalize."""
    return "orchestrator" if state.get("critic", {}).get("verdict") == "revise" else "finalize"
