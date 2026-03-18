from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Pydantic v2 / pydantic-settings v2 — model_config ile tanımla
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Docker env_file veya gerçek env var varsa .env'i override eder
        case_sensitive=True,
    )

    DATABASE_URL: str = "postgresql+asyncpg://aria:aria@db:5432/aria"
    REDIS_URL: str = "redis://redis:6379"
    ANTHROPIC_API_KEY: str = ""
    SECRET_KEY: str = "aria-super-secret-key-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 gün
    CORS_ORIGINS: List[str] = ["http://localhost:4000"]
    DEBUG: bool = False
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/v1/integrations/ga4/callback"
    GOOGLE_AUTH_REDIRECT_URI: str = "http://localhost:3000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:4000"


settings = Settings()
