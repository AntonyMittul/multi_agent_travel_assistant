"""Shared graph state — the single source of truth every agent reads and writes.

This is what makes the system *collaborative* rather than a chain of isolated
tool calls: the hotel agent can see the flight arrival, the budget agent sees
both, and the critic sees everything.
"""
from __future__ import annotations

from operator import add
from typing import Annotated, Any, Dict, List, TypedDict


class TravelState(TypedDict, total=False):
    # ---- input ----
    query: str                       # raw natural-language request
    preferences: Dict[str, Any]      # parsed: origin, destination, dates, budget, ...

    # ---- orchestration / control ----
    plan: List[str]                  # ordered agent names the orchestrator intends to run
    completed_agents: List[str]      # agents that have finished this pass
    next_agent: str                  # routing target chosen by the orchestrator
    constraints: Dict[str, Any]      # critic-imposed adjustments (e.g. cheaper hotel tier)
    revision_count: int              # how many replans have happened (loop fail-safe)

    # ---- shared memory: each specialist writes its slice ----
    destination: Dict[str, Any]
    weather: Dict[str, Any]
    flights: Dict[str, Any]
    hotels: Dict[str, Any]
    activities: Dict[str, Any]
    logistics: Dict[str, Any]
    budget: Dict[str, Any]

    # ---- review + output ----
    critic: Dict[str, Any]
    final_itinerary: Dict[str, Any]

    # ---- append-only logs (reducers) ----
    messages: Annotated[List[Dict[str, Any]], add]   # streamed to the UI
    errors: Annotated[List[str], add]


def event(agent: str, kind: str, text: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build a single timeline event for the `messages` log / SSE stream."""
    return {"agent": agent, "kind": kind, "text": text, "data": data or {}}
