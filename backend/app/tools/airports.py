"""Compact major-airport table (public-domain coords) for IATA lookup and
great-circle distance. Used to query AviationStack by route and to estimate
fares by distance. Not exhaustive — unknown cities fall back to OpenCage
coordinates for distance and skip the live AviationStack schedule lookup.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

# city (lowercase) -> {iata, lat, lon, name}
AIRPORTS: Dict[str, Dict[str, Any]] = {
    "mumbai": {"iata": "BOM", "lat": 19.0887, "lon": 72.8679, "name": "Chhatrapati Shivaji Intl"},
    "delhi": {"iata": "DEL", "lat": 28.5562, "lon": 77.1000, "name": "Indira Gandhi Intl"},
    "new delhi": {"iata": "DEL", "lat": 28.5562, "lon": 77.1000, "name": "Indira Gandhi Intl"},
    "bangalore": {"iata": "BLR", "lat": 13.1986, "lon": 77.7066, "name": "Kempegowda Intl"},
    "bengaluru": {"iata": "BLR", "lat": 13.1986, "lon": 77.7066, "name": "Kempegowda Intl"},
    "chennai": {"iata": "MAA", "lat": 12.9941, "lon": 80.1709, "name": "Chennai Intl"},
    "kolkata": {"iata": "CCU", "lat": 22.6547, "lon": 88.4467, "name": "Netaji Subhas Chandra Bose Intl"},
    "hyderabad": {"iata": "HYD", "lat": 17.2403, "lon": 78.4294, "name": "Rajiv Gandhi Intl"},
    "goa": {"iata": "GOI", "lat": 15.3808, "lon": 73.8314, "name": "Goa Intl"},
    "kochi": {"iata": "COK", "lat": 10.1520, "lon": 76.4019, "name": "Cochin Intl"},
    "london": {"iata": "LHR", "lat": 51.4700, "lon": -0.4543, "name": "Heathrow"},
    "paris": {"iata": "CDG", "lat": 49.0097, "lon": 2.5479, "name": "Charles de Gaulle"},
    "amsterdam": {"iata": "AMS", "lat": 52.3105, "lon": 4.7683, "name": "Schiphol"},
    "frankfurt": {"iata": "FRA", "lat": 50.0379, "lon": 8.5622, "name": "Frankfurt"},
    "madrid": {"iata": "MAD", "lat": 40.4936, "lon": -3.5668, "name": "Adolfo Suárez Madrid–Barajas"},
    "barcelona": {"iata": "BCN", "lat": 41.2974, "lon": 2.0833, "name": "Barcelona–El Prat"},
    "rome": {"iata": "FCO", "lat": 41.8003, "lon": 12.2389, "name": "Fiumicino"},
    "lisbon": {"iata": "LIS", "lat": 38.7742, "lon": -9.1342, "name": "Humberto Delgado"},
    "athens": {"iata": "ATH", "lat": 37.9364, "lon": 23.9445, "name": "Athens Intl"},
    "istanbul": {"iata": "IST", "lat": 41.2753, "lon": 28.7519, "name": "Istanbul"},
    "zurich": {"iata": "ZRH", "lat": 47.4647, "lon": 8.5492, "name": "Zürich"},
    "munich": {"iata": "MUC", "lat": 48.3538, "lon": 11.7861, "name": "Munich"},
    "berlin": {"iata": "BER", "lat": 52.3667, "lon": 13.5033, "name": "Berlin Brandenburg"},
    "dublin": {"iata": "DUB", "lat": 53.4213, "lon": -6.2701, "name": "Dublin"},
    "new york": {"iata": "JFK", "lat": 40.6413, "lon": -73.7781, "name": "John F. Kennedy Intl"},
    "los angeles": {"iata": "LAX", "lat": 33.9416, "lon": -118.4085, "name": "Los Angeles Intl"},
    "san francisco": {"iata": "SFO", "lat": 37.6213, "lon": -122.3790, "name": "San Francisco Intl"},
    "chicago": {"iata": "ORD", "lat": 41.9742, "lon": -87.9073, "name": "O'Hare Intl"},
    "miami": {"iata": "MIA", "lat": 25.7959, "lon": -80.2870, "name": "Miami Intl"},
    "toronto": {"iata": "YYZ", "lat": 43.6777, "lon": -79.6248, "name": "Toronto Pearson"},
    "vancouver": {"iata": "YVR", "lat": 49.1967, "lon": -123.1815, "name": "Vancouver Intl"},
    "mexico city": {"iata": "MEX", "lat": 19.4361, "lon": -99.0719, "name": "Benito Juárez Intl"},
    "sao paulo": {"iata": "GRU", "lat": -23.4356, "lon": -46.4731, "name": "São Paulo–Guarulhos"},
    "dubai": {"iata": "DXB", "lat": 25.2532, "lon": 55.3657, "name": "Dubai Intl"},
    "abu dhabi": {"iata": "AUH", "lat": 24.4330, "lon": 54.6511, "name": "Zayed Intl"},
    "doha": {"iata": "DOH", "lat": 25.2731, "lon": 51.6080, "name": "Hamad Intl"},
    "singapore": {"iata": "SIN", "lat": 1.3644, "lon": 103.9915, "name": "Changi"},
    "bangkok": {"iata": "BKK", "lat": 13.6900, "lon": 100.7501, "name": "Suvarnabhumi"},
    "tokyo": {"iata": "HND", "lat": 35.5494, "lon": 139.7798, "name": "Haneda"},
    "osaka": {"iata": "KIX", "lat": 34.4347, "lon": 135.2441, "name": "Kansai Intl"},
    "seoul": {"iata": "ICN", "lat": 37.4602, "lon": 126.4407, "name": "Incheon Intl"},
    "hong kong": {"iata": "HKG", "lat": 22.3080, "lon": 113.9185, "name": "Hong Kong Intl"},
    "beijing": {"iata": "PEK", "lat": 40.0799, "lon": 116.6031, "name": "Beijing Capital Intl"},
    "shanghai": {"iata": "PVG", "lat": 31.1443, "lon": 121.8083, "name": "Pudong Intl"},
    "bali": {"iata": "DPS", "lat": -8.7482, "lon": 115.1675, "name": "Ngurah Rai Intl"},
    "denpasar": {"iata": "DPS", "lat": -8.7482, "lon": 115.1675, "name": "Ngurah Rai Intl"},
    "jakarta": {"iata": "CGK", "lat": -6.1256, "lon": 106.6559, "name": "Soekarno–Hatta Intl"},
    "kuala lumpur": {"iata": "KUL", "lat": 2.7456, "lon": 101.7099, "name": "Kuala Lumpur Intl"},
    "hanoi": {"iata": "HAN", "lat": 21.2212, "lon": 105.8072, "name": "Noi Bai Intl"},
    "sydney": {"iata": "SYD", "lat": -33.9399, "lon": 151.1753, "name": "Kingsford Smith"},
    "melbourne": {"iata": "MEL", "lat": -37.6690, "lon": 144.8410, "name": "Melbourne"},
    "auckland": {"iata": "AKL", "lat": -37.0082, "lon": 174.7850, "name": "Auckland"},
    "queenstown": {"iata": "ZQN", "lat": -45.0211, "lon": 168.7392, "name": "Queenstown"},
    "nairobi": {"iata": "NBO", "lat": -1.3192, "lon": 36.9278, "name": "Jomo Kenyatta Intl"},
    "cape town": {"iata": "CPT", "lat": -33.9690, "lon": 18.6017, "name": "Cape Town Intl"},
    "cairo": {"iata": "CAI", "lat": 30.1219, "lon": 31.4056, "name": "Cairo Intl"},
}

# alias -> canonical city key
_ALIASES = {"nyc": "new york", "sf": "san francisco", "kl": "kuala lumpur"}


def lookup(city: str) -> Optional[Dict[str, Any]]:
    if not city:
        return None
    key = city.strip().lower()
    # strip a trailing ", country" if present
    if "," in key:
        key = key.split(",")[0].strip()
    key = _ALIASES.get(key, key)
    return AIRPORTS.get(key)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 1)
