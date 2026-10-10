"""App settings, read from environment variables (or the .env file).

Keeping every setting in one place means the rest of the code never
calls os.getenv() directly, and secrets never live in the source code.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database (PostgreSQL by default, MySQL also works)
    database_url: str

    # JWT authentication
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # AI integration
    ai_provider: str = "gemini"  # gemini | openai | anthropic | mock
    ai_api_key: str = ""
    ai_model: str = ""  # empty = use the provider's default model
    ai_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    """Create the settings once and reuse them."""
    return Settings()
