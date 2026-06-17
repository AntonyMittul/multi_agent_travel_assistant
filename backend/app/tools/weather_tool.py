"""Real weather via Open-Meteo (free, no API key required)."""
from __future__ import annotations

from typing import Any, Dict

import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo WMO weather codes -> human label
_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers",
    81: "Rain showers", 82: "Violent rain showers", 95: "Thunderstorm",
    96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ hail",
}


def _format_hit(g: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "lat": g["latitude"],
        "lon": g["longitude"],
        "name": g["name"],
        "country": g.get("country", ""),
    }


def _query(name: str, count: int = 5):
    try:
        r = requests.get(GEO_URL, params={"name": name, "count": count}, timeout=10)
        return r.json().get("results") or []
    except Exception:
        return []


def geocode(name: str) -> Dict[str, Any] | None:
    """Geocode a place. Open-Meteo wants a bare city, so 'Bali, Indonesia' is
    queried as 'Bali' and the country hint ('Indonesia') disambiguates between
    same-named cities."""
    city = name
    country_hint = ""
    if "," in name:
        parts = [p.strip() for p in name.split(",") if p.strip()]
        city = parts[0]
        country_hint = parts[-1] if len(parts) > 1 else ""

    results = _query(city) or _query(name)
    if not results:
        return None

    if country_hint:
        hint = country_hint.lower()
        for g in results:
            if hint in g.get("country", "").lower():
                return _format_hit(g)
    return _format_hit(results[0])


def get_weather(destination: str) -> Dict[str, Any]:
    """Return a 7-day forecast + a short summary for the destination."""
    geo = geocode(destination)
    if not geo:
        return {"available": False, "summary": f"Could not locate '{destination}'."}

    params = {
        "latitude": geo["lat"],
        "longitude": geo["lon"],
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_mean,weather_code",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        daily = requests.get(FORECAST_URL, params=params, timeout=10).json().get("daily", {})
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "summary": f"Weather lookup failed: {exc}"}

    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    rain = daily.get("precipitation_probability_mean", [])
    codes = daily.get("weather_code", [])

    days = []
    for i, d in enumerate(dates):
        days.append({
            "date": d,
            "high_c": highs[i] if i < len(highs) else None,
            "low_c": lows[i] if i < len(lows) else None,
            "rain_pct": rain[i] if i < len(rain) else None,
            "condition": _CODES.get(codes[i] if i < len(codes) else -1, "Unknown"),
        })

    avg_high = round(sum(highs) / len(highs), 1) if highs else None
    avg_rain = round(sum(r for r in rain if r is not None) / max(len(rain), 1)) if rain else 0
    wet = avg_rain >= 50
    summary = (
        f"{geo['name']}, {geo['country']}: avg high ~{avg_high}°C over the next 7 days, "
        f"~{avg_rain}% chance of rain. {'Pack a rain jacket.' if wet else 'Mostly dry — pack light.'}"
    )

    return {
        "available": True,
        "location": geo,
        "avg_high_c": avg_high,
        "avg_rain_pct": avg_rain,
        "rainy": wet,
        "days": days,
        "summary": summary,
    }
