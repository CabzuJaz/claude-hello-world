"""
config.py — Single source of truth for all environment config.
All other files import from here. Never hardcode values elsewhere.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# ─────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────

# Default: google_credentials.json in same directory as this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GOOGLE_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    os.path.join(_BASE_DIR, "google_credentials.json")
)
SHEET_NAME = os.getenv("SHEET_NAME", "STR Leads")

# ─────────────────────────────────────────
# FLASK
# ─────────────────────────────────────────

FLASK_PORT  = int(os.getenv("FLASK_PORT", 5002))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# ─────────────────────────────────────────
# AGENT LIMITS
# ─────────────────────────────────────────

MAX_RESULTS_LIMIT = int(os.getenv("MAX_RESULTS_LIMIT", 10))
REQUEST_TIMEOUT   = int(os.getenv("REQUEST_TIMEOUT", 10))

# ─────────────────────────────────────────
# STARTUP VALIDATION
# ─────────────────────────────────────────

def validate_config() -> None:
    """Raise EnvironmentError early if required config is missing."""
    missing = []

    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")

    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        missing.append(
            f"GOOGLE_CREDENTIALS_FILE — file not found: {GOOGLE_CREDENTIALS_FILE}"
        )

    if missing:
        raise EnvironmentError(
            f"[Config] Missing required config:\n" +
            "\n".join(f"  - {m}" for m in missing)
        )

    print(f"[Config] OK — API key loaded, credentials file found")
    print(f"[Config] Sheet: '{SHEET_NAME}' | Port: {FLASK_PORT} | Debug: {FLASK_DEBUG}")