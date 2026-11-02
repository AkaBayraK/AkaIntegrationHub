"""Ortak Testcontainers fixture'ları (Docker gerekir). Image sürümleri .env.example ile aynıdır."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from mailpit_credentials import MAILPIT_PASSWORD, MAILPIT_USER  # type: ignore[import-not-found]
from testcontainers.community.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

POSTGRES_IMAGE = "postgres:17.6-alpine"
VALKEY_IMAGE = "valkey/valkey:8.1.4-alpine"
RABBITMQ_IMAGE = "rabbitmq:4.1.4-management-alpine"
MAILPIT_IMAGE = "axllent/mailpit:v1.27.10"


@dataclass
class Endpoint:
    host: str
    port: int
    http_port: int = 0


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer(POSTGRES_IMAGE, username="aih", password="test-only", dbname="aih", driver=None) as pg:
        yield pg


@pytest.fixture(scope="session")
def valkey() -> Iterator[Endpoint]:
    container = DockerContainer(VALKEY_IMAGE).with_exposed_ports(6379)
    container.waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
    with container:
        yield Endpoint(container.get_container_host_ip(), int(container.get_exposed_port(6379)))


@pytest.fixture(scope="session")
def rabbitmq() -> Iterator[Endpoint]:
    container = (
        DockerContainer(RABBITMQ_IMAGE)
        .with_exposed_ports(5672)
        .with_env("RABBITMQ_DEFAULT_USER", "aih")
        .with_env("RABBITMQ_DEFAULT_PASS", "test-only")
        .with_env("RABBITMQ_DEFAULT_VHOST", "aih")
    )
    container.waiting_for(LogMessageWaitStrategy("Server startup complete").with_startup_timeout(120))
    with container:
        yield Endpoint(container.get_container_host_ip(), int(container.get_exposed_port(5672)))


@pytest.fixture(scope="session")
def mailpit() -> Iterator[Endpoint]:
    container = (
        DockerContainer(MAILPIT_IMAGE)
        .with_exposed_ports(1025, 8025)
        .with_env("MP_SMTP_AUTH", f"{MAILPIT_USER}:{MAILPIT_PASSWORD}")
        .with_env("MP_SMTP_AUTH_ALLOW_INSECURE", "true")
    )
    container.waiting_for(LogMessageWaitStrategy("accessible via").with_startup_timeout(60))
    with container:
        yield Endpoint(
            container.get_container_host_ip(),
            int(container.get_exposed_port(1025)),
            int(container.get_exposed_port(8025)),
        )
