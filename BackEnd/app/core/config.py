import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from BackEnd directory so the key is always found
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)


class Settings:
    PROJECT_NAME: str = "FootVision AI Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS Origins
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Storage Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "Data", "uploads")
    PROCESSED_DIR: str = os.path.join(BASE_DIR, "Data", "processed")

    # Football Data API Settings (football-data.org)
    # Loaded from BackEnd/.env — NEVER hardcoded here.
    FOOTBALL_DATA_API_KEY: str = os.getenv("FOOTBALL_DATA_API_KEY", "")
    FOOTBALL_DATA_BASE_URL: str = os.getenv("FOOTBALL_DATA_BASE_URL", "https://api.football-data.org/v4")

    # API-Football (API-Sports) Settings
    # Loaded from BackEnd/.env — NEVER hardcoded here.
    API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")
    API_FOOTBALL_BASE_URL: str = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
