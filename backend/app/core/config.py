from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"
    APP_DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:5173"

    DATABASE_URL: str
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    PRIMARY_LLM: str = "claude-sonnet-4-20250514"
    FALLBACK_LLM: str = "gpt-4o"

    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: str = "rag-knowledge-base"
    PINECONE_NAMESPACE: str = "sis-westlake"

    JWT_SECRET_KEY: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    REDIS_URL: Optional[str] = None

    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_NUMBER: Optional[str] = None

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@sis.datawebify.com"

    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
