import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


def _cors_origins() -> list[str]:
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def _cors_origin_regex() -> str | None:
    # Vite may select another 51xx port when an earlier development server is open.
    # An explicit CORS_ORIGINS setting keeps production origins restricted.
    return None if os.getenv("CORS_ORIGINS") is not None else r"^http://(localhost|127\.0\.0\.1):51\d{2}$"


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "HealthAI Lab"
    api_prefix: str = "/api"
    cors_origins: list[str] = field(default_factory=_cors_origins)
    cors_origin_regex: str | None = field(default_factory=_cors_origin_regex)


settings = Settings()
