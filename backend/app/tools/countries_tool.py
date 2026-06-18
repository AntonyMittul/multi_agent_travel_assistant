"""Local country reference data for the logistics agent.

REST Countries' public API was deprecated/gated, so we ship a small offline
table (no key, always works) covering common travel destinations. For anything
not in the table we fall back to Gemini (live mode) or a generic message.
"""
from __future__ import annotations

from typing import Any, Dict

from ..llm import llm_json

# country (lowercase) -> facts
_DATA: Dict[str, Dict[str, Any]] = {
    "japan": {"capital": "Tokyo", "currency": "Japanese Yen (JPY)", "currency_code": "JPY",
              "languages": ["Japanese"], "timezone": "Asia/Tokyo", "flag": "🇯🇵"},
    "france": {"capital": "Paris", "currency": "Euro (EUR)", "currency_code": "EUR",
               "languages": ["French"], "timezone": "Europe/Paris", "flag": "🇫🇷"},
    "italy": {"capital": "Rome", "currency": "Euro (EUR)", "currency_code": "EUR",
              "languages": ["Italian"], "timezone": "Europe/Rome", "flag": "🇮🇹"},
    "spain": {"capital": "Madrid", "currency": "Euro (EUR)", "currency_code": "EUR",
              "languages": ["Spanish"], "timezone": "Europe/Madrid", "flag": "🇪🇸"},
    "portugal": {"capital": "Lisbon", "currency": "Euro (EUR)", "currency_code": "EUR",
                 "languages": ["Portuguese"], "timezone": "Europe/Lisbon", "flag": "🇵🇹"},
    "germany": {"capital": "Berlin", "currency": "Euro (EUR)", "currency_code": "EUR",
                "languages": ["German"], "timezone": "Europe/Berlin", "flag": "🇩🇪"},
    "united kingdom": {"capital": "London", "currency": "Pound Sterling (GBP)", "currency_code": "GBP",
                       "languages": ["English"], "timezone": "Europe/London", "flag": "🇬🇧"},
    "united states": {"capital": "Washington, D.C.", "currency": "US Dollar (USD)", "currency_code": "USD",
                      "languages": ["English"], "timezone": "America/New_York", "flag": "🇺🇸"},
    "thailand": {"capital": "Bangkok", "currency": "Thai Baht (THB)", "currency_code": "THB",
                 "languages": ["Thai"], "timezone": "Asia/Bangkok", "flag": "🇹🇭"},
    "indonesia": {"capital": "Jakarta", "currency": "Indonesian Rupiah (IDR)", "currency_code": "IDR",
                  "languages": ["Indonesian"], "timezone": "Asia/Jakarta", "flag": "🇮🇩"},
    "india": {"capital": "New Delhi", "currency": "Indian Rupee (INR)", "currency_code": "INR",
              "languages": ["Hindi", "English"], "timezone": "Asia/Kolkata", "flag": "🇮🇳"},
    "singapore": {"capital": "Singapore", "currency": "Singapore Dollar (SGD)", "currency_code": "SGD",
                  "languages": ["English", "Malay", "Mandarin", "Tamil"], "timezone": "Asia/Singapore", "flag": "🇸🇬"},
    "united arab emirates": {"capital": "Abu Dhabi", "currency": "UAE Dirham (AED)", "currency_code": "AED",
                             "languages": ["Arabic"], "timezone": "Asia/Dubai", "flag": "🇦🇪"},
    "australia": {"capital": "Canberra", "currency": "Australian Dollar (AUD)", "currency_code": "AUD",
                  "languages": ["English"], "timezone": "Australia/Sydney", "flag": "🇦🇺"},
    "new zealand": {"capital": "Wellington", "currency": "NZ Dollar (NZD)", "currency_code": "NZD",
                    "languages": ["English", "Māori"], "timezone": "Pacific/Auckland", "flag": "🇳🇿"},
    "canada": {"capital": "Ottawa", "currency": "Canadian Dollar (CAD)", "currency_code": "CAD",
               "languages": ["English", "French"], "timezone": "America/Toronto", "flag": "🇨🇦"},
    "kenya": {"capital": "Nairobi", "currency": "Kenyan Shilling (KES)", "currency_code": "KES",
              "languages": ["Swahili", "English"], "timezone": "Africa/Nairobi", "flag": "🇰🇪"},
    "greece": {"capital": "Athens", "currency": "Euro (EUR)", "currency_code": "EUR",
               "languages": ["Greek"], "timezone": "Europe/Athens", "flag": "🇬🇷"},
    "turkey": {"capital": "Ankara", "currency": "Turkish Lira (TRY)", "currency_code": "TRY",
               "languages": ["Turkish"], "timezone": "Europe/Istanbul", "flag": "🇹🇷"},
    "mexico": {"capital": "Mexico City", "currency": "Mexican Peso (MXN)", "currency_code": "MXN",
               "languages": ["Spanish"], "timezone": "America/Mexico_City", "flag": "🇲🇽"},
    "brazil": {"capital": "Brasília", "currency": "Brazilian Real (BRL)", "currency_code": "BRL",
               "languages": ["Portuguese"], "timezone": "America/Sao_Paulo", "flag": "🇧🇷"},
    "south korea": {"capital": "Seoul", "currency": "South Korean Won (KRW)", "currency_code": "KRW",
                    "languages": ["Korean"], "timezone": "Asia/Seoul", "flag": "🇰🇷"},
    "vietnam": {"capital": "Hanoi", "currency": "Vietnamese Dong (VND)", "currency_code": "VND",
                "languages": ["Vietnamese"], "timezone": "Asia/Ho_Chi_Minh", "flag": "🇻🇳"},
    "switzerland": {"capital": "Bern", "currency": "Swiss Franc (CHF)", "currency_code": "CHF",
                    "languages": ["German", "French", "Italian"], "timezone": "Europe/Zurich", "flag": "🇨🇭"},
}

# common aliases -> canonical key
_ALIASES = {
    "usa": "united states", "us": "united states", "u.s.": "united states",
    "uk": "united kingdom", "u.k.": "united kingdom", "england": "united kingdom",
    "uae": "united arab emirates", "korea": "south korea",
}


def _format(country: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "available": True,
        "country": country.title(),
        "capital": facts.get("capital", ""),
        "currency": facts.get("currency", ""),
        "currency_code": facts.get("currency_code", ""),
        "languages": facts.get("languages", []),
        "timezones": [facts.get("timezone", "")],
        "flag": facts.get("flag", ""),
        "summary": (
            f"Currency: {facts.get('currency', 'n/a')}; "
            f"Language(s): {', '.join(facts.get('languages', [])[:3]) or 'n/a'}; "
            f"Timezone: {facts.get('timezone', 'n/a')}."
        ),
    }


def get_country_info(country_or_city: str) -> Dict[str, Any]:
    if not country_or_city:
        return {"available": False, "summary": "No destination country to look up."}

    key = country_or_city.strip().lower()
    key = _ALIASES.get(key, key)
    if key in _DATA:
        return _format(key, _DATA[key])

    # not in the table — ask Gemini (returns generic text in offline mode)
    facts = llm_json(
        f"Return ONLY JSON for the country '{country_or_city}': "
        "{\"capital\": str, \"currency\": str, \"currency_code\": str, "
        "\"languages\": [str], \"timezone\": str, \"flag\": str (emoji)}.",
        fallback=None,
    )
    if isinstance(facts, dict) and facts.get("currency"):
        return _format(country_or_city, facts)

    return {
        "available": False,
        "country": country_or_city.title(),
        "summary": f"Reference data for {country_or_city.title()} isn't in the local table.",
    }


def get_languages(country: str) -> list:
    """Languages for a country (OpenCage doesn't provide this). [] if unknown."""
    if not country:
        return []
    key = _ALIASES.get(country.strip().lower(), country.strip().lower())
    return _DATA.get(key, {}).get("languages", [])
