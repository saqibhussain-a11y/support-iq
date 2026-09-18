from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

def _find_repo_root() -> Path:
    parents = list(Path(__file__).resolve().parents)
    for parent in parents:
        if (parent / "knowledge_base").is_dir():
            return parent
    return parents[min(3, len(parents) - 1)]


REPO_ROOT = _find_repo_root()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+asyncpg://supportiq:supportiq@localhost:5432/supportiq"

    cors_origins: list[str] = ["http://localhost:3000"]

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    llm_max_retries: int = 2
    llm_timeout_seconds: float = 30.0

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    knowledge_base_path: Path = REPO_ROOT / "knowledge_base"


@lru_cache
def get_settings() -> Settings:
    return Settings()
