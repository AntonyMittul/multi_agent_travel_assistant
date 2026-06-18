"""Currency conversion via open.er-api.com (free, no API key).

All internal cost math is in USD; we convert to the traveler's display currency
once, for presentation. Rates are fetched once per process and cached.
"""
from __future__ import annotations

from typing import Dict, Optional

import requests

URL = "https://open.er-api.com/v6/latest/USD"

_RATES: Optional[Dict[str, float]] = None

# common currency symbols (fallback to the ISO code when missing)
_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "INR": "₹",
    "THB": "฿", "AED": "د.إ", "AUD": "A$", "CAD": "C$", "NZD": "NZ$",
    "SGD": "S$", "KRW": "₩", "CHF": "CHF", "TRY": "₺", "BRL": "R$",
    "MXN": "$", "ZAR": "R", "IDR": "Rp", "VND": "₫", "RUB": "₽",
    "HKD": "HK$", "PHP": "₱", "MYR": "RM", "SEK": "kr", "NOK": "kr", "DKK": "kr",
}

# currency aliases / symbols a user might type in the query
SYMBOL_TO_CODE = {
    "$": "USD", "₹": "INR", "rs": "INR", "rs.": "INR", "inr": "INR",
    "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP",
    "¥": "JPY", "jpy": "JPY", "usd": "USD", "฿": "THB", "thb": "THB",
    "aed": "AED", "dirham": "AED", "aud": "AUD", "sgd": "SGD",
}


def _load() -> Dict[str, float]:
    global _RATES
    if _RATES is None:
        try:
            _RATES = requests.get(URL, timeout=12).json().get("rates", {}) or {}
        except Exception:
            _RATES = {}
    return _RATES


def usd_to(code: str) -> float:
    """Multiplier to convert a USD amount into `code` (1.0 if USD/unknown)."""
    if not code or code.upper() == "USD":
        return 1.0
    return _load().get(code.upper(), 1.0) or 1.0


def to_usd(amount: float, code: str) -> float:
    """Convert an amount given in `code` back to USD."""
    rate = usd_to(code)
    return amount / rate if rate else amount


def symbol(code: str) -> str:
    return _SYMBOLS.get((code or "USD").upper(), (code or "$").upper())
