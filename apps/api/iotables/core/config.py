from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://iotables:iotables@localhost:5432/iotables"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="IOTABLES_")


settings = Settings()
