from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENTS = {"local", "test", "staging", "production"}
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
OTP_DELIVERY_MODES = {"fixed"}


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
        default="postgresql+asyncpg://iotables:iotables@localhost:5433/iotables",
        alias="IOTABLES_DATABASE_URL",
    )
    security_secret_key: str = Field(
        default="local-dev-insecure-secret-change-me",
        alias="IOTABLES_SECURITY_SECRET_KEY",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="IOTABLES_CORS_ORIGINS",
    )
    tenant_root_domains: list[str] = Field(
        default_factory=lambda: ["iotables.net"],
        alias="IOTABLES_TENANT_ROOT_DOMAINS",
    )
    otp_delivery_mode: str = Field(default="fixed", alias="IOTABLES_OTP_DELIVERY_MODE")
    otp_fixed_code: str = Field(default="000000", alias="IOTABLES_OTP_FIXED_CODE")

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

    @field_validator("tenant_root_domains")
    @classmethod
    def validate_tenant_root_domains(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in value:
            root_domain = item.strip().lower().removeprefix(".")
            if (
                not root_domain
                or root_domain == "*"
                or "://" in root_domain
                or "/" in root_domain
                or " " in root_domain
            ):
                raise ValueError("tenant_root_domains must contain bare domain names")
            if root_domain not in normalized:
                normalized.append(root_domain)
        if not normalized:
            raise ValueError("tenant_root_domains must not be empty")
        return normalized

    @field_validator("otp_delivery_mode")
    @classmethod
    def validate_otp_delivery_mode(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in OTP_DELIVERY_MODES:
            expected = ", ".join(sorted(OTP_DELIVERY_MODES))
            raise ValueError(f"otp_delivery_mode must be one of: {expected}")
        return normalized

    @field_validator("otp_fixed_code")
    @classmethod
    def validate_otp_fixed_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.isdigit() or len(normalized) != 6:
            raise ValueError("otp_fixed_code must be exactly 6 digits")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
