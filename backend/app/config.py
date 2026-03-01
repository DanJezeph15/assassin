"""Application settings via Pydantic BaseSettings.

Reads from environment variables and .env file. DATABASE_URL defaults to a
local SQLite file for zero-config development.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the backend/ directory so the SQLite file lands in a predictable spot.
_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Central configuration consumed by the rest of the application."""

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database -----------------------------------------------------------------
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_BACKEND_DIR / 'games.db'}"

    # CORS ---------------------------------------------------------------------
    # Comma-separated origins or a JSON list.  Default allows the Vite dev server.
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # JWT ----------------------------------------------------------------------
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 43200  # 30 days

    # App metadata -------------------------------------------------------------
    APP_NAME: str = "Airbnb Games"
    DEBUG: bool = False


settings = Settings()
