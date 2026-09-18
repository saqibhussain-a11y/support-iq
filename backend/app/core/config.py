from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, populated from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+asyncpg://supportiq:supportiq@localhost:5432/supportiq"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Reserved for Module 2 (LLM Layer) — not used yet.
    groq_api_key: str | None = None
    groq_model: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
