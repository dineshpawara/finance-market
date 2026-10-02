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
from sqlalchemy.engine import URL

# Root directory of the finance backend
BASE_DIR = Path(__file__).resolve().parent.parent


def read_secret_file(file_path: Optional[str]) -> Optional[str]:
    """Reads secret from a Docker secret file path if available."""
    if file_path:
        path = Path(file_path)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    return None


class Settings(BaseSettings):
    """
    Application Settings loaded dynamically from .env file or Docker secrets.
    """

    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "default-insecure-secret-key-change-in-production"

    # PostgreSQL Database settings (Values come from Docker Secrets or .env)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_USER_FILE: Optional[str] = None
    POSTGRES_PASSWORD_FILE: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = "finance_market_db"
    POSTGRES_SSLMODE: Optional[str] = None
    POSTGRES_SSLROOTCERT: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def effective_postgres_user(self) -> Optional[str]:
        if self.POSTGRES_USER_FILE:
            val = read_secret_file(self.POSTGRES_USER_FILE)
            if val:
                return val
        return self.POSTGRES_USER

    @computed_field
    @property
    def effective_postgres_password(self) -> Optional[str]:
        if self.POSTGRES_PASSWORD_FILE:
            val = read_secret_file(self.POSTGRES_PASSWORD_FILE)
            if val:
                return val
        return self.POSTGRES_PASSWORD

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """
        Returns validated database URL without hardcoding passwords in source code.
        Supports TLS encryption and Docker Secrets.
        """
        user = self.effective_postgres_user
        password = self.effective_postgres_password
        # Prioritize Docker secret files & environment over static DATABASE_URL
        if (self.POSTGRES_USER_FILE or self.POSTGRES_PASSWORD_FILE) and user and password and self.POSTGRES_DB:
            query = {}
            if self.POSTGRES_SSLMODE:
                query["sslmode"] = self.POSTGRES_SSLMODE
            if self.POSTGRES_SSLROOTCERT:
                query["sslrootcert"] = self.POSTGRES_SSLROOTCERT
            return URL.create(
                "postgresql+psycopg2",
                username=user,
                password=password,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                database=self.POSTGRES_DB,
                query=query,
            ).render_as_string(hide_password=False)

        if self.DATABASE_URL:
            return self.DATABASE_URL

        if user and password and self.POSTGRES_DB:
            query = {}
            if self.POSTGRES_SSLMODE:
                query["sslmode"] = self.POSTGRES_SSLMODE
            if self.POSTGRES_SSLROOTCERT:
                query["sslrootcert"] = self.POSTGRES_SSLROOTCERT
            return URL.create(
                "postgresql+psycopg2",
                username=user,
                password=password,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                database=self.POSTGRES_DB,
                query=query,
            ).render_as_string(hide_password=False)
        raise ValueError(
            "Database configuration missing! Please ensure POSTGRES_USER/POSTGRES_USER_FILE and POSTGRES_PASSWORD/POSTGRES_PASSWORD_FILE are defined."
        )

    # Redis settings (Supports Docker secrets and TLS)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_PASSWORD_FILE: Optional[str] = None
    REDIS_TLS_CA_CERT: Optional[str] = None

    @computed_field
    @property
    def effective_redis_password(self) -> Optional[str]:
        if self.REDIS_PASSWORD_FILE:
            val = read_secret_file(self.REDIS_PASSWORD_FILE)
            if val:
                return val
        return self.REDIS_PASSWORD

    # Virtual Paper Trading & Wallet
    DEFAULT_WALLET_BALANCE: float = 1000000.00
    CURRENCY: str = "INR"

    # AI News Sentiment
    NEWS_RECENCY_MINUTES: int = 600
    FINBERT_MODEL: str = "ProsusAI/finbert"
    ENABLE_HEURISTIC_FALLBACK: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")


# Global singleton instance of Settings
settings = Settings()
