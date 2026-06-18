"""Central configuration. Reads from environment / .env file.

Every external key is optional: each tool degrades gracefully when its key is
absent, so you can add keys incrementally. The minimum for a useful run is
OPENCAGE_API_KEY (geocoding) + GOOGLE_API_KEY (reasoning).
"""
import os

from dotenv import load_dotenv

load_dotenv()

# ---- LLM ----
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()

# ---- external data APIs ----
OPENCAGE_API_KEY: str = os.getenv("OPENCAGE_API_KEY", "").strip()
AVIATIONSTACK_API_KEY: str = os.getenv("AVIATIONSTACK_API_KEY", "").strip()
GEODB_API_KEY: str = os.getenv("GEODB_API_KEY", "").strip()  # RapidAPI key (optional)

# ---- behavior ----
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
MAX_REVISIONS: int = int(os.getenv("MAX_REVISIONS", "2"))


def llm_available() -> bool:
    """True when we have a usable Gemini key and demo mode is off."""
    return bool(GOOGLE_API_KEY) and not DEMO_MODE
