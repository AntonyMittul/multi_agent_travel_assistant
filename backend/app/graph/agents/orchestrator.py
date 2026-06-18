"""Orchestrator: decompose the goal, parse preferences, and route subtasks.

This is the 'manager' of the system. On the first pass it turns the raw query
into a structured preferences object and an ordered plan. On every pass it
picks the next un-run specialist (dynamic routing). When the plan is exhausted
it hands off to the critic.
"""
from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Dict

from ...llm import llm_json
from ...state import TravelState, event
from ...tools.fx_tool import SYMBOL_TO_CODE, to_usd

# Order matters: destination first (it may *choose* the place), budget last
# (it needs every other agent's costs), logistics after weather (reuses geo).
PLAN = ["destination", "weather", "flight", "hotel", "activities", "logistics", "budget"]

# travel style -> (hotel_tier, flight_tier). Drives a different plan for the
# same city. The critic can still downgrade tiers later to fit a budget.
STYLE_TIERS = {
    "budget": ("budget", "economy"),
    "luxury": ("luxury", "business"),
    "family": ("mid", "economy"),
    "adventure": ("budget", "economy"),
    "solo": ("budget", "economy"),
    "business": ("mid", "business"),
}

_INTEREST_WORDS = [
    "beach", "hiking", "history", "museum", "food", "nightlife", "nature",
    "adventure", "shopping", "art", "wildlife", "skiing", "diving", "culture",
    "temple", "wine", "photography", "relax", "spa", "family",
]


def _heuristic_parse(query: str) -> Dict[str, Any]:
    """Offline preference extraction when no LLM is available."""
    q = query.lower()
    origin = None
    dest = None

    m = re.search(r"\bfrom\s+([a-z][a-z\s]+?)(?:\s+to\b|,|\.|$)", q)
    if m:
        origin = m.group(1).strip().title()
    m = re.search(r"\bto\s+([a-z][a-z\s]+?)(?:\s+from\b|,|\.|for|on|with|$)", q)
    if m:
        dest = m.group(1).strip().title()
    if not dest:
        m = re.search(r"\b(?:visit|explore|trip to|holiday in|vacation in)\s+([a-z][a-z\s]+?)(?:,|\.|for|on|with|$)", q)
        if m:
            dest = m.group(1).strip().title()

    budget = None
    currency = None
    # amount possibly prefixed by a symbol ($/₹/€/£/¥) or suffixed by a code
    m = (
        re.search(r"([$₹€£¥])\s?(\d[\d,]{2,})", q)
        or re.search(r"(rs\.?|inr|usd|eur|gbp|jpy|thb|aed|aud|sgd)\s*(\d[\d,]{2,})", q)
        or re.search(r"(\d[\d,]{2,})\s*(usd|inr|eur|gbp|jpy|thb|aed|aud|sgd|rs\.?|dollars|rupees)", q)
        or re.search(r"budget\s*(?:of\s*|is\s*|around\s*|~\s*)?([$₹€£¥])?\s*(\d[\d,]{2,})", q)
    )
    if m:
        groups = m.groups()
        # find the numeric group and any currency token among the groups
        num = next((g for g in groups if g and g.replace(",", "").isdigit()), None)
        token = next((g for g in groups if g and not g.replace(",", "").isdigit()), None)
        if num:
            budget = int(num.replace(",", ""))
        if token:
            currency = SYMBOL_TO_CODE.get(token.strip().lower())

    travelers = 1
    m = (
        re.search(r"(\d+)\s*(?:people|persons?|travell?ers?|adults?|members?|guests?|pax|ppl|of us)", q)
        or re.search(r"(?:family|group|party)\s+of\s+(\d+)", q)
    )
    if m:
        travelers = int(m.group(1))
    elif "couple" in q or "two of us" in q or "my partner" in q or "my wife" in q or "my husband" in q:
        travelers = 2

    nights = None
    m = re.search(r"(\d+)[\s-]*(?:night|day)", q)
    if m:
        nights = int(m.group(1))

    interests = [w for w in _INTEREST_WORDS if w in q]

    return {
        "origin": origin,
        "destination": dest,
        "budget": budget,
        "budget_currency": currency,
        "travelers": travelers,
        "nights": nights,
        "interests": interests,
        "vibe": None,
    }


def _llm_parse(query: str) -> Dict[str, Any] | None:
    prompt = (
        "Extract structured travel preferences from this request. "
        "Return ONLY JSON with keys: origin (string or null), destination (string or null), "
        "budget (number or null), budget_currency (ISO code like USD/INR/EUR or null — "
        "infer from any symbol/word the user used), travelers (int), nights (int or null), "
        "interests (array of strings), vibe (short string or null).\n\n"
        f"Request: {query}"
    )
    result = llm_json(prompt, fallback=None)
    return result if isinstance(result, dict) else None


def _normalize(prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Fill defaults and derive dates so downstream agents have everything."""
    prefs = dict(prefs or {})
    prefs.setdefault("origin", None)
    prefs.setdefault("destination", None)

    # Normalize the budget to USD internally (estimates are USD); remember the
    # user-typed currency as a display hint. No currency typed → assume USD.
    cur = prefs.get("budget_currency")
    if isinstance(cur, str):
        cur = SYMBOL_TO_CODE.get(cur.strip().lower(), cur.strip().upper())
    amount = prefs.get("budget")
    if amount:
        prefs["budget_usd"] = round(to_usd(float(amount), cur) if cur else float(amount))
    else:
        prefs.setdefault("budget_usd", None)
    prefs["currency_hint"] = cur or None

    prefs["travelers"] = int(prefs.get("travelers") or 1)
    prefs["interests"] = prefs.get("interests") or []
    prefs.setdefault("vibe", None)

    nights = prefs.get("nights") or 4
    prefs["nights"] = int(nights)

    if not prefs.get("start_date"):
        start = _dt.date.today() + _dt.timedelta(days=30)
        prefs["start_date"] = start.isoformat()
        prefs["end_date"] = (start + _dt.timedelta(days=prefs["nights"])).isoformat()

    # travel style sets the default tiers (critic may downgrade later to fit budget)
    style = (prefs.get("style") or "").strip().lower()
    ht, ft = STYLE_TIERS.get(style, ("mid", "economy"))
    prefs.setdefault("hotel_tier", ht)
    prefs.setdefault("flight_tier", ft)
    prefs["style"] = style or None
    return prefs


def orchestrator(state: TravelState) -> Dict[str, Any]:
    updates: Dict[str, Any] = {}

    # ---- first pass: decompose the goal ----
    if not state.get("preferences"):
        parsed = _llm_parse(state["query"]) or _heuristic_parse(state["query"])
        prefs = _normalize(parsed)
        updates["preferences"] = prefs
        updates["plan"] = PLAN
        updates["completed_agents"] = []
        updates["constraints"] = {}
        updates["revision_count"] = state.get("revision_count", 0)
        updates["messages"] = [event(
            "orchestrator", "plan",
            f"Goal received. Decomposed into {len(PLAN)} subtasks: {', '.join(PLAN)}.",
            {"preferences": prefs, "plan": PLAN},
        )]

    # ---- apply any critic-imposed constraints to preferences ----
    constraints = updates.get("constraints", state.get("constraints", {})) or {}
    if constraints:
        prefs = dict(updates.get("preferences", state.get("preferences", {})))
        if "hotel_tier" in constraints:
            prefs["hotel_tier"] = constraints["hotel_tier"]
        if "flight_tier" in constraints:
            prefs["flight_tier"] = constraints["flight_tier"]
        updates["preferences"] = prefs

    # ---- route to the next un-run agent ----
    plan = updates.get("plan", state.get("plan", PLAN))
    completed = updates.get("completed_agents", state.get("completed_agents", []))
    next_agent = next((a for a in plan if a not in completed), "critic")
    updates["next_agent"] = next_agent

    if next_agent != "critic":
        updates.setdefault("messages", [])
        updates["messages"] = updates.get("messages", []) + [event(
            "orchestrator", "route", f"Delegating to the {next_agent} agent.", {"next": next_agent},
        )]

    return updates


def route_from_orchestrator(state: TravelState) -> str:
    """Conditional-edge function: where the orchestrator sends control next."""
    return state.get("next_agent", "critic")
