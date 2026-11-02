from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from aih_api.app import create_app, create_management_app
from aih_api.infrastructure import Infrastructure
from aih_api.settings import ApiSettings
from aih_api.tenancy import service as tenancy
from aih_api.tenancy.models import IdentityProvider
from aih_common.settings import RabbitSettings

ISSUER_A = "https://idp.example.test/realms/building"
ISSUER_B = "https://idp.example.test/realms/trace"
CLIENT_ID = "aih-admin-web"


@dataclass
class Keys:
    private: rsa.RSAPrivateKey

    def token(self, issuer: str, roles: list[str], *, sub: str = "user-1", **extra: Any) -> str:
        now = int(time.time())
        claims = {
            "iss": issuer,
            "sub": sub,
            "azp": CLIENT_ID,
            "iat": now,
            "exp": now + 300,
            "realm_access": {"roles": roles},
            "preferred_username": sub,
            **extra,
        }
        return jwt.encode(claims, self.private, algorithm="RS256", headers={"kid": "test"})


class StaticResolver:
    def __init__(self, keys: Keys) -> None:
        self.keys = keys

    async def signing_key(self, provider: IdentityProvider, token: str) -> Any:
        return self.keys.private.public_key()


@pytest.fixture(scope="session")
def keys() -> Keys:
    return Keys(rsa.generate_private_key(public_exponent=65537, key_size=2048))


@pytest.fixture(scope="session")
def settings(postgres: Any, valkey: Any, rabbitmq: Any) -> ApiSettings:
    return ApiSettings(
        environment="test",
        db_url=f"postgresql+asyncpg://{postgres.get_container_host_ip()}:{postgres.get_exposed_port(5432)}/aih",
        db_user="aih",
        db_password="test-only",
        valkey_host=valkey.host,
        valkey_port=valkey.port,
        auth_dev_mode=True,
        rabbitmq=RabbitSettings(host=rabbitmq.host, port=rabbitmq.port, user="aih", password="test-only", vhost="aih"),
    )


@dataclass
class Env:
    api: httpx.AsyncClient
    mgmt: httpx.AsyncClient
    infra: Infrastructure
    app: Any
    keys: Keys
    tenant_a: uuid.UUID
    tenant_b: uuid.UUID

    def auth(self, issuer: str = ISSUER_A, roles: list[str] | None = None, **extra: Any) -> dict[str, str]:
        token = self.keys.token(issuer, roles if roles is not None else ["SITE_ADMIN"], **extra)
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
async def env(settings: ApiSettings, keys: Keys) -> AsyncIterator[Env]:
    app = create_app(settings, token_verifier=_verifier(keys))
    infra: Infrastructure = app.state.infra
    async with app.router.lifespan_context(app):
        async with app.state.db.transaction() as session:
            a = await tenancy.upsert_tenant_with_issuer(
                session,
                slug="building",
                name="BuildingFlow",
                issuer=ISSUER_A,
                client_ids=[CLIENT_ID],
                tenant_admin_roles=["SITE_ADMIN"],
                viewer_roles=["MANAGER"],
                platform_admin_roles=["AIH_PLATFORM_ADMIN"],
            )
            b = await tenancy.upsert_tenant_with_issuer(
                session,
                slug="trace",
                name="TraceFlow",
                issuer=ISSUER_B,
                client_ids=[CLIENT_ID],
                tenant_admin_roles=["SYSTEM_ADMIN"],
                viewer_roles=[],
            )
        api = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://api")
        mgmt = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_management_app(infra)), base_url="http://mgmt"
        )
        async with api, mgmt:
            yield Env(api, mgmt, infra, app, keys, a.id, b.id)


def _verifier(keys: Keys) -> Any:
    from aih_api.identity.verifier import TokenVerifier

    return TokenVerifier(StaticResolver(keys))
