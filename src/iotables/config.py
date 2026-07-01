from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "IoTables"
    environment: str = Field(default="local", alias="IOTABLES_ENV")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/iotables",
        alias="IOTABLES_DATABASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="IOTABLES_CORS_ORIGINS",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
