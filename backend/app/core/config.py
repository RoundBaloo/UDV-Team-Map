from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    app_name: str = "udv-team-map"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        60,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")

    s3_endpoint_url: str = Field(..., env="S3_ENDPOINT_URL")
    s3_region: str = Field("ru-central1", env="S3_REGION")
    s3_bucket: str = Field(..., env="S3_BUCKET")
    s3_access_key_id: str = Field(..., env="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field(..., env="S3_SECRET_ACCESS_KEY")
    s3_public_base: str | None = Field(
        default=None,
        env="S3_PUBLIC_BASE",
    )

    SYNC_USE_TEST_FILE: bool = Field(
        True,
        env="SYNC_USE_TEST_FILE",
    )
    SYNC_INGEST_FILE_PATH: str = Field(
        "data_source/employees_for_sync.json",
        env="SYNC_INGEST_FILE_PATH",
    )

    AD_LDAP_HOST: str = Field(..., env="AD_LDAP_HOST")
    AD_LDAP_PORT: int = Field(389, env="AD_LDAP_PORT")
    AD_USE_SSL: bool = Field(False, env="AD_USE_SSL")

    AD_BASE_DN: str = Field(..., env="AD_BASE_DN")
    AD_BIND_USER: str = Field(..., env="AD_BIND_USER")
    AD_BIND_PASSWORD: str = Field(..., env="AD_BIND_PASSWORD")

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings: Settings = Settings()
