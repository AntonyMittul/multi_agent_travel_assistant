"""Assemble the LangGraph state machine that coordinates all agents.

Topology:

    START → orchestrator ─(dynamic route)→ specialist ─┐
              ▲   │                                      │
              │   └────────────→ critic ←───────────────┘
              │                   │
        (replan loop)       (approve)→ finalize → END

* orchestrator routes to the next un-run specialist (conditional edges)
* every specialist returns to the orchestrator (shared-state hand-off)
* critic either loops back (bounded replan) or finalizes (fail-safe exit)
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..config import MAX_REVISIONS
from ..state import TravelState
from .agents.activities import activities
from .agents.budget import budget
from .agents.critic import critic, route_from_critic
from .agents.destination import destination
from .agents.finalize import finalize
from .agents.flight import flight
from .agents.hotel import hotel
from .agents.logistics import logistics
from .agents.orchestrator import orchestrator, route_from_orchestrator
from .agents.weather import weather

# specialist name -> node function
SPECIALISTS = {
    "destination": destination,
    "weather": weather,
    "flight": flight,
    "hotel": hotel,
    "activities": activities,
    "logistics": logistics,
    "budget": budget,
}


# LangGraph forbids node ids that collide with state keys (destination,
# weather, budget, critic, ...). We give nodes a "_agent" suffix but keep the
# logical names for routing / completed-agent tracking.
def _node_id(name: str) -> str:
    return f"{name}_agent"


def build_graph():
    g = StateGraph(TravelState)

    g.add_node("orchestrator", orchestrator)
    for name, fn in SPECIALISTS.items():
        g.add_node(_node_id(name), fn)
    g.add_node("critic_agent", critic)
    g.add_node("finalize", finalize)

    g.add_edge(START, "orchestrator")

    # orchestrator → one specialist OR critic (dynamic routing).
    # route function returns a *logical* name; map it to the node id.
    g.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {**{n: _node_id(n) for n in SPECIALISTS}, "critic": "critic_agent"},
    )

    # every specialist reports back to the orchestrator
    for name in SPECIALISTS:
        g.add_edge(_node_id(name), "orchestrator")

    # critic → replan (orchestrator) OR finalize
    g.add_conditional_edges(
        "critic_agent",
        route_from_critic,
        {"orchestrator": "orchestrator", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)

    return g.compile()


# compiled once at import; recursion_limit is an additional hard loop guard
GRAPH = build_graph()

# generous ceiling: ~7 specialists × (MAX_REVISIONS+1) passes + routing hops
RECURSION_LIMIT = (len(SPECIALISTS) + 3) * (MAX_REVISIONS + 1) + 10
