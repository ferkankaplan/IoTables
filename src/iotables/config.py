from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENTS = {"local", "test", "staging", "production"}
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "IoTables"
    environment: str = Field(default="local", alias="IOTABLES_ENV")
    log_level: str = Field(default="INFO", alias="IOTABLES_LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/iotables",
        alias="IOTABLES_DATABASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="IOTABLES_CORS_ORIGINS",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in ENVIRONMENTS:
            expected = ", ".join(sorted(ENVIRONMENTS))
            raise ValueError(f"environment must be one of: {expected}")
        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in LOG_LEVELS:
            expected = ", ".join(sorted(LOG_LEVELS))
            raise ValueError(f"log_level must be one of: {expected}")
        return normalized

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("cors_origins must not be empty")
        if "*" in value:
            raise ValueError("wildcard CORS origin is not allowed")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
