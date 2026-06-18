"""Weather via Open-Meteo (free, no key). Takes coordinates from the geo tool."""
from __future__ import annotations

from typing import Any, Dict

import requests

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


def get_weather(lat: float, lon: float, label: str = "") -> Dict[str, Any]:
    """Return a 7-day forecast + a short summary for the given coordinates."""
    if lat is None or lon is None:
        return {"available": False, "summary": "No coordinates for weather lookup."}

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_mean,weather_code",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        daily = requests.get(FORECAST_URL, params=params, timeout=12).json().get("daily", {})
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
    rain_vals = [r for r in rain if r is not None]
    avg_rain = round(sum(rain_vals) / len(rain_vals)) if rain_vals else 0
    wet = avg_rain >= 50
    where = f"{label}: " if label else ""
    summary = (
        f"{where}avg high ~{avg_high}°C over the next 7 days, ~{avg_rain}% chance of rain. "
        f"{'Pack a rain jacket.' if wet else 'Mostly dry — pack light.'}"
    )

    return {
        "available": True,
        "avg_high_c": avg_high,
        "avg_rain_pct": avg_rain,
        "rainy": wet,
        "days": days,
        "summary": summary,
    }
