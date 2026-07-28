from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

     # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nifty_sentiment"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Pipeline
    RECENCY_MINUTES: int = 30
    FETCH_INTERVAL_MINUTES: int = 15

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

settings = Settings()