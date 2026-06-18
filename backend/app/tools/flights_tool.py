"""Flights via AviationStack — REAL schedules/airlines, ESTIMATED fares.

AviationStack provides no pricing at any plan, so fares are estimated from
great-circle distance and clearly flagged `price_estimated: True`. The live
call returns real carriers and times on the route (free real-time endpoint).
Requires AVIATIONSTACK_API_KEY for the schedule lookup; the fare estimate
works without it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from ..config import AVIATIONSTACK_API_KEY
from .airports import haversine_km, lookup

# free plan is HTTP-only
API_URL = "http://api.aviationstack.com/v1/flights"

_TIER_MULT = {"economy": 1.0, "premium": 1.8, "business": 3.2}


def _estimate_fare(distance_km: Optional[float], tier: str, round_trip: bool) -> float:
    if not distance_km:
        base = 220.0  # generic fallback when distance is unknown
    else:
        base = max(55.0, 40 + distance_km * 0.11)
    fare = base * _TIER_MULT.get(tier, 1.0) * (1.9 if round_trip else 1.0)
    return round(fare, 2)


def _live_flights(dep_iata: str, arr_iata: str, limit: int = 12) -> List[Dict[str, Any]]:
    if not AVIATIONSTACK_API_KEY or not dep_iata or not arr_iata:
        return []
    try:
        r = requests.get(
            API_URL,
            params={"access_key": AVIATIONSTACK_API_KEY, "dep_iata": dep_iata,
                    "arr_iata": arr_iata, "limit": limit},
            timeout=15,
        )
        return r.json().get("data", []) or []
    except Exception:
        return []


def search_flights(
    origin_city: str,
    dest_city: str,
    depart_date: Optional[str] = None,
    return_date: Optional[str] = None,
    travelers: int = 1,
    tier: str = "economy",
    origin_coords: Optional[tuple] = None,
    dest_coords: Optional[tuple] = None,
) -> Dict[str, Any]:
    if not origin_city or not dest_city:
        return {"available": False, "summary": "Need both origin and destination for flights."}

    o_air = lookup(origin_city)
    d_air = lookup(dest_city)

    # distance: prefer airport coords, fall back to geocoded coords
    o = (o_air["lat"], o_air["lon"]) if o_air else origin_coords
    d = (d_air["lat"], d_air["lon"]) if d_air else dest_coords
    distance_km = haversine_km(o[0], o[1], d[0], d[1]) if o and d else None

    round_trip = bool(return_date)
    fare = _estimate_fare(distance_km, tier, round_trip)

    options: List[Dict[str, Any]] = []
    live = _live_flights(o_air["iata"] if o_air else "", d_air["iata"] if d_air else "")
    seen_airlines = set()
    for f in live:
        airline = (f.get("airline") or {}).get("name")
        if not airline or airline in seen_airlines:
            continue
        seen_airlines.add(airline)
        dep = (f.get("departure") or {})
        arr = (f.get("arrival") or {})
        # slight per-airline variation around the estimate
        jitter = 1 + (len(options) - 1) * 0.06
        options.append({
            "airline": airline,
            "flight_number": (f.get("flight") or {}).get("iata", ""),
            "depart_time": (dep.get("scheduled") or "")[11:16],
            "arrive_time": (arr.get("scheduled") or "")[11:16],
            "tier": tier,
            "total_price": round(fare * travelers * jitter, 2),
            "price_estimated": True,
        })
        if len(options) >= 3:
            break

    source = "AviationStack (live schedule)" if options else "estimate only"
    if not options:
        # no live data (no key / unknown route / quota) — synthesize estimate rows
        for i, label in enumerate(["Direct", "1-stop", "Flexible"]):
            options.append({
                "airline": f"Multiple carriers ({label})",
                "flight_number": "",
                "depart_time": "",
                "arrive_time": "",
                "tier": tier,
                "total_price": round(fare * travelers * (1 + i * 0.12), 2),
                "price_estimated": True,
            })

    options.sort(key=lambda x: x["total_price"])
    cheapest = options[0]
    route = f"{(o_air or {}).get('iata', origin_city)}→{(d_air or {}).get('iata', dest_city)}"
    return {
        "available": True,
        "origin": origin_city,
        "destination": dest_city,
        "route": route,
        "distance_km": distance_km,
        "source": source,
        "price_estimated": True,
        "options": options,
        "cheapest": cheapest,
        "summary": (
            f"{cheapest['airline']} {route} from ~${cheapest['total_price']:.0f} total "
            f"(est.{', ' + str(distance_km) + ' km' if distance_km else ''}). "
            f"Schedules: {source}."
        ),
    }
