"""Ortak ayarlar. Ortam değişkenleri ``AIH_`` önekiyle okunur."""

from __future__ import annotations

from typing import Literal
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "test", "staging", "prod"]


class RabbitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIH_RABBITMQ_", extra="ignore")

    host: str = "localhost"
    port: int = 25672
    user: str = "aih"
    password: str = ""
    vhost: str = "aih"

    def url(self) -> str:
        return (
            f"amqp://{quote(self.user, safe='')}:{quote(self.password, safe='')}"
            f"@{self.host}:{self.port}/{quote(self.vhost, safe='')}"
        )
