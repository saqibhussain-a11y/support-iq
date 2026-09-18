from functools import lru_cache

from app.core.config import get_settings
from app.llm.groq_provider import GroqProvider
from app.llm.service import LLMService


@lru_cache
def get_llm_service() -> LLMService:
    settings = get_settings()
    provider = GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        max_retries=settings.llm_max_retries,
        timeout=settings.llm_timeout_seconds,
    )
    return LLMService(provider)
