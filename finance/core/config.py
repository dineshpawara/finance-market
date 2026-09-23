"""
Core Application Configuration
==============================
Centralized configuration management powered by Pydantic Settings.
Reads and validates environment variables from .env without hardcoding sensitive secrets.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

# Root directory of the finance backend
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application Settings loaded dynamically from .env file.
    """
    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production"

    # PostgreSQL Database settings (Values come strictly from .env)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """
        Returns validated database URL without hardcoding passwords in source code.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        raise ValueError(
            "Database configuration missing! Please ensure DATABASE_URL or POSTGRES_* are defined in .env"
        )

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Virtual Paper Trading & Wallet
    DEFAULT_WALLET_BALANCE: float = 1000000.00
    CURRENCY: str = "INR"

    # AI News Sentiment
    NEWS_RECENCY_MINUTES: int = 600
    FINBERT_MODEL: str = "ProsusAI/finbert"
    ENABLE_HEURISTIC_FALLBACK: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Global singleton instance of Settings
settings = Settings()
