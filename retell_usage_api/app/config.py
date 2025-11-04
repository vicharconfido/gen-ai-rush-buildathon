from functools import lru_cache

from pydantic import BaseSettings, Field, HttpUrl


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    retell_api_key: str | None = Field(None, env="RETELL_API_KEY")
    retell_base_url: HttpUrl = Field(
        "https://api.retellai.com/v2", env="RETELL_BASE_URL"
    )
    request_timeout_seconds: float = Field(10.0, env="RETELL_TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
