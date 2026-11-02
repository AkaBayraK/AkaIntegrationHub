from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aih_common.settings import Environment, RabbitSettings


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIH_", extra="ignore")

    environment: Environment = "local"
    worker_management_port: int = 28091
    log_format: str = "json"
    log_level: str = "INFO"
    rabbitmq: RabbitSettings = Field(default_factory=RabbitSettings)
