"""Mock hotel search — deterministic. Swap for Amadeus/Booking later; keep shape."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

_NAMES = ["Grand", "Harbor", "Central", "Riverside", "Skyline", "Garden", "Plaza", "Heritage"]
_SUFFIX = ["Inn", "Hotel", "Suites", "Residency", "Boutique", "Resort"]
_TIER_RATE = {"budget": 35, "mid": 95, "luxury": 240}


def _seed(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def search_hotels(
    destination: str,
    nights: int = 3,
    travelers: int = 1,
    tier: str = "mid",
) -> Dict[str, Any]:
    if not destination:
        return {"available": False, "summary": "Missing destination for hotel search."}

    rooms = max(1, (travelers + 1) // 2)
    base_rate = _TIER_RATE.get(tier, 95)
    seed = _seed(f"{destination}|{tier}")

    options: List[Dict[str, Any]] = []
    for i in range(3):
        s = _seed(f"{seed}|{i}")
        nightly = round(base_rate * (0.8 + (s % 50) / 100), 2)
        rating = round(3.5 + (s % 16) / 10, 1)
        options.append({
            "name": f"{_NAMES[s % len(_NAMES)]} {_SUFFIX[(s >> 3) % len(_SUFFIX)]}",
            "tier": tier,
            "rating": min(rating, 5.0),
            "nightly_rate": nightly,
            "rooms": rooms,
            "nights": nights,
            "total_price": round(nightly * rooms * nights, 2),
        })

    options.sort(key=lambda o: o["total_price"])
    best = options[0]
    return {
        "available": True,
        "destination": destination,
        "tier": tier,
        "nights": nights,
        "options": options,
        "best_value": best,
        "summary": (
            f"{best['name']} ({best['rating']}★) at ${best['nightly_rate']:.0f}/night "
            f"— ${best['total_price']:.0f} for {nights} night(s)."
        ),
    }
