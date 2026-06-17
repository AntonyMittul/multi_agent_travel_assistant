"""Central configuration. Reads from environment / .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
MAX_REVISIONS: int = int(os.getenv("MAX_REVISIONS", "2"))


def llm_available() -> bool:
    """True when we have a usable Gemini key and demo mode is off."""
    return bool(GOOGLE_API_KEY) and not DEMO_MODE
