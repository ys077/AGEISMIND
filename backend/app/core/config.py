"""
Core configuration — reads settings from environment variables / .env file.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Compute project root (4 levels up from backend/app/core/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/cybercrime_prediction"
    )
    PROJECT_NAME: str = "AI-Driven Cybercrime Cash Withdrawal Prediction System"
    PROJECT_VERSION: str = "0.2.0"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
