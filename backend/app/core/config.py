from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения (читаются из .env)."""

    # === Общие настройки приложения ===
    app_name: str = "udv-team-map"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # === Подключение к БД ===
    database_url: str = Field(..., env="DATABASE_URL")

    # === JWT / безопасность ===
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
