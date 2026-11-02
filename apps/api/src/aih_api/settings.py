from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from aih_common.settings import Environment, RabbitSettings


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIH_", extra="ignore")

    environment: Environment = "local"
    api_port: int = 28080
    api_management_port: int = 28081
    log_format: str = "json"
    log_level: str = "INFO"

    db_url: str = "postgresql+asyncpg://localhost:25432/aih"
    db_user: str = "aih"
    db_password: str = ""
    migrate_on_startup: bool = True

    valkey_host: str = "localhost"
    valkey_port: int = 26379
    valkey_password: str = ""

    rabbitmq: RabbitSettings = Field(default_factory=RabbitSettings)

    @field_validator("db_url")
    @classmethod
    def _normalize_db_url(cls, value: str) -> str:
        # Eski Spring ayarı (jdbc:postgresql://...) da kabul edilir.
        if value.startswith("jdbc:"):
            value = value.removeprefix("jdbc:")
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        return value


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()
