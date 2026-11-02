from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
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

    # Yalnız local/test: "X-AIH-Dev-User: <tenant-slug>:<Rol>" başlığıyla kimlik taklidi. Prod'da açılamaz.
    auth_dev_mode: bool = False
    # Admin web ve host uygulamaların (BuildingFlow, TraceFlow) tarayıcıdan erişeceği origin'ler (virgülle).
    cors_origins: str = "http://localhost:28030"

    # Secret şifreleme anahtarları: "kid:<fernet-key>[,kid:<eski-key>]" (ilk anahtar birincil).
    secret_keys: str = ""
    # SMTP hedef politikası (SSRF). Özel ağ yalnız local/dev/test'te açılabilir (Mailpit için).
    smtp_allow_private_hosts: bool = False
    smtp_allowed_ports: str = "25,465,587,2525"
    smtp_host_allowlist: str = ""

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

    @model_validator(mode="after")
    def _dev_mode_only_locally(self) -> ApiSettings:
        if self.auth_dev_mode and self.environment not in ("local", "test"):
            raise ValueError("AIH_AUTH_DEV_MODE yalnız local/test ortamında etkinleştirilebilir")
        if self.smtp_allow_private_hosts and self.environment in ("staging", "prod"):
            raise ValueError("AIH_SMTP_ALLOW_PRIVATE_HOSTS staging/prod ortamında etkinleştirilemez")
        if self.environment in ("staging", "prod") and not self.secret_keys:
            raise ValueError("AIH_SECRET_KEYS staging/prod ortamında zorunludur")
        return self

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> ApiSettings:
    return ApiSettings()
