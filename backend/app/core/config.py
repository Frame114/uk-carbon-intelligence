from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "UK Carbon Intelligence API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://carbon:carbon@localhost:5432/carbon_intelligence"
    neso_api_base_url: str = "https://api.carbonintensity.org.uk"
    neso_timeout_seconds: float = Field(default=12.0, gt=0, le=60)
    collection_interval_seconds: int = Field(default=1800, ge=300, le=86400)
    scheduler_enabled: bool = True
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8080"]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
