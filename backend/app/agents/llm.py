from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from app.core.config import settings
import structlog

logger = structlog.get_logger()


def get_primary_llm(temperature: float = 0.0) -> ChatAnthropic:
    return ChatAnthropic(
        model=settings.PRIMARY_LLM,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        temperature=temperature,
        max_tokens=4096,
    )


def get_fallback_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.FALLBACK_LLM,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=temperature,
        max_tokens=4096,
    )


def get_llm(use_fallback: bool = False, temperature: float = 0.0):
    if use_fallback:
        logger.info("Using fallback LLM", model=settings.FALLBACK_LLM)
        return get_fallback_llm(temperature)
    return get_primary_llm(temperature)
