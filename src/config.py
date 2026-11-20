from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (the folder that contains app.py and .env)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Central place for application configuration.

    Values can come from:
    1. Environment variables
    2. A local .env file
    3. The defaults below
    """

    app_name: str = "Production Streaming LLM API"
    environment: str = "development"

    # Clients must send this API key.
    api_key: str = "course-secret"

    # Fake model name shown in responses.
    llm_model: str = "demo-model"

    # Simple rate limiter settings.
    rate_limit: int = 10
    rate_window_seconds: int = 60

    # Load variables from .env (absolute path, so it works from any folder).
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore"
    )


settings = Settings()
