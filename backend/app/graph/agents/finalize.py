"""Finalize: convert costs to the traveler's local currency, assemble the
merged itinerary, and write a natural-language answer (the chatbot reply)."""
from __future__ import annotations

from typing import Any, Dict

from ...llm import llm_text
from ...state import TravelState, event
from ...tools.fx_tool import symbol as fx_symbol
from ...tools.fx_tool import usd_to


def _convert_money(it: Dict[str, Any], rate: float) -> None:
    """Multiply every USD cost field in-place by `rate` (rounded to integer).

    `cheapest`/`best_value` are the SAME object as options[0]; we dedupe by id
    so a shared option isn't converted twice (the ₹1.4M flight bug).
    """
    seen: set[int] = set()

    def cv(v):
        return round(v * rate) if isinstance(v, (int, float)) else v

    def conv(opt: Dict[str, Any], fields) -> None:
        if not isinstance(opt, dict) or id(opt) in seen:
            return
        seen.add(id(opt))
        for f in fields:
            if isinstance(opt.get(f), (int, float)):
                opt[f] = cv(opt[f])

    flights = it.get("flights") or {}
    for opt in flights.get("options", []) or []:
        conv(opt, ["total_price"])
    conv(flights.get("cheapest"), ["total_price"])

    hotels = it.get("hotels") or {}
    for opt in hotels.get("options", []) or []:
        conv(opt, ["total_price", "nightly_rate"])
    conv(hotels.get("best_value"), ["total_price", "nightly_rate"])

    acts = it.get("activities") or {}
    if "estimated_cost" in acts:
        acts["estimated_cost"] = cv(acts.get("estimated_cost"))

    b = it.get("budget") or {}
    if b.get("breakdown"):
        b["breakdown"] = {k: cv(v) for k, v in b["breakdown"].items()}
    for key in ("total", "target", "remaining"):
        if b.get(key) is not None:
            b[key] = cv(b[key])


def finalize(state: TravelState) -> Dict[str, Any]:
    prefs = state.get("preferences", {})
    dest = prefs.get("destination", "your destination")
    geo = state.get("destination", {}).get("geo", {})

    # ---- decide display currency: user hint > destination currency > USD ----
    code = (prefs.get("currency_hint") or geo.get("currency_code") or "USD").upper()
    sym = geo.get("currency_symbol") or fx_symbol(code)
    rate = usd_to(code)

    itinerary: Dict[str, Any] = {
        "preferences": prefs,
        "destination": state.get("destination", {}),
        "weather": state.get("weather", {}),
        "flights": state.get("flights", {}),
        "hotels": state.get("hotels", {}),
        "activities": state.get("activities", {}),
        "logistics": state.get("logistics", {}),
        "budget": state.get("budget", {}),
        "critic": state.get("critic", {}),
        "currency": {"code": code, "symbol": sym},
    }
    _convert_money(itinerary, rate)

    budget = itinerary.get("budget", {})
    total = budget.get("total", 0)
    target = budget.get("target")
    money = f"{sym}{total:,.0f}"
    target_str = f" against a {sym}{target:,.0f} budget" if target else ""

    fallback = (
        f"Here's your {prefs.get('nights')}-night trip to {dest}. "
        f"Estimated total cost is {money}{target_str}. "
        f"{state.get('weather', {}).get('summary', '')} "
        f"The plan below covers flights, where to stay, a day-by-day schedule, and local tips. "
        f"Flight fares and room rates are estimates."
    )

    summary = llm_text(
        "Write a warm, helpful 4-6 sentence trip summary for the traveler, like a "
        "concierge replying in chat. Use the local currency symbol provided. Cover: the "
        "destination's appeal, the weather to expect, the flight, where to stay, the kind "
        "of activities planned, and whether it fits the budget.\n"
        f"Destination: {dest}\n"
        f"Nights: {prefs.get('nights')}, Travelers: {prefs.get('travelers')}\n"
        f"Currency symbol: {sym} ({code})\n"
        f"Total cost: {sym}{total:,.0f}; Budget: {(sym + format(target, ',.0f')) if target else 'not specified'}\n"
        f"Over budget: {budget.get('over_budget')}\n"
        f"Highlights: {state.get('destination', {}).get('highlights')}\n"
        f"Weather: {state.get('weather', {}).get('summary')}\n"
        f"Flight: {state.get('flights', {}).get('summary')}\n"
        f"Hotel: {state.get('hotels', {}).get('summary')}\n"
        f"Logistics: {state.get('logistics', {}).get('summary')}\n"
        "Note that flight fares and hotel rates are estimates.",
        fallback=fallback,
    )
    itinerary["summary"] = summary
    itinerary["agent_log"] = _build_agent_log(state, sym, total)

    return {
        "final_itinerary": itinerary,
        "messages": [event("finalize", "final", summary, {"itinerary": itinerary})],
    }


def _build_agent_log(state: TravelState, sym: str, total: float):
    """A clean, human-readable record of what each agent did (for the UI panel)."""
    prefs = state.get("preferences", {})
    weather = state.get("weather", {})
    flights = state.get("flights", {})
    hotels = state.get("hotels", {})
    acts = state.get("activities", {})
    logi = state.get("logistics", {})
    rev = state.get("revision_count", 0)

    log = [{
        "label": "Orchestrator",
        "detail": "Decomposed your request and routed it to specialist agents",
    }, {
        "label": "Destination Agent",
        "detail": f"Selected {prefs.get('destination', 'your destination')}",
    }]
    if weather.get("available"):
        log.append({"label": "Weather Agent", "detail": weather.get("summary", "Analyzed the forecast")})
    if flights.get("available"):
        log.append({"label": "Flight Agent",
                    "detail": f"Searched flights {flights.get('route', '')} ({flights.get('source', '')})"})
    if hotels.get("available"):
        log.append({"label": "Hotel Agent",
                    "detail": f"Reviewed {len(hotels.get('options', []))} hotels and picked "
                              f"{hotels.get('best_value', {}).get('name', 'the best value')}"})
    log.append({"label": "Activities Agent",
                "detail": f"Curated {len(acts.get('pois', []))} attractions and "
                          f"{len(acts.get('restaurants', []))} restaurants into a "
                          f"{prefs.get('nights')}-night plan"})
    if logi.get("available"):
        log.append({"label": "Logistics Agent", "detail": logi.get("summary", "Gathered local info")})
    log.append({"label": "Budget Agent", "detail": f"Tallied the trip cost at {sym}{total:,.0f}"})
    log.append({"label": "Critic Agent",
                "detail": (f"Adjusted the plan {rev}× to fit the budget, then validated it"
                           if rev else "Validated the merged plan — all checks passed")})
    return log
