"""Mock flight search — deterministic so the same trip always prices the same.

Swap this module for a real provider (Amadeus / Kiwi / Skyscanner) without
touching the agent: keep the `search_flights(...)` signature and return shape.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

_AIRLINES = ["IndiGo", "Emirates", "Lufthansa", "Singapore Air", "Qatar Airways", "Delta"]
_TIER_MULT = {"economy": 1.0, "premium": 1.8, "business": 3.2}


def _seed(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str | None = None,
    travelers: int = 1,
    tier: str = "economy",
) -> Dict[str, Any]:
    if not origin or not destination:
        return {"available": False, "summary": "Missing origin or destination for flight search."}

    seed = _seed(f"{origin}|{destination}|{depart_date}")
    base = 90 + seed % 420  # one-way base fare in USD
    mult = _TIER_MULT.get(tier, 1.0)
    round_trip = 1.9 if return_date else 1.0

    options: List[Dict[str, Any]] = []
    for i in range(3):
        s = _seed(f"{seed}|{i}")
        price = round(base * mult * round_trip * (0.85 + (s % 30) / 100), 2)
        stops = s % 3  # 0, 1, or 2 stops
        duration_h = 3 + (s % 14) + stops * 2
        dep_hour = 6 + (s % 16)
        options.append({
            "airline": _AIRLINES[s % len(_AIRLINES)],
            "tier": tier,
            "stops": stops,
            "depart_time": f"{dep_hour:02d}:{(s % 6) * 10:02d}",
            "duration_h": duration_h,
            "price_per_person": price,
            "total_price": round(price * travelers, 2),
        })

    options.sort(key=lambda o: o["total_price"])
    cheapest = options[0]
    return {
        "available": True,
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date,
        "return_date": return_date,
        "travelers": travelers,
        "options": options,
        "cheapest": cheapest,
        "summary": (
            f"{cheapest['airline']} {origin}→{destination} from "
            f"${cheapest['total_price']:.0f} total ({cheapest['stops']} stop(s), "
            f"{cheapest['duration_h']}h)."
        ),
    }
