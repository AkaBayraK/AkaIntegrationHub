from __future__ import annotations

import time

import jwt
import pytest
from conftest_api import CLIENT_ID, ISSUER_A, ISSUER_B, Env  # type: ignore[import-not-found]
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integration


async def test_me_requires_authentication(env: Env) -> None:
    response = await env.api.get("/v1/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["code"] == "AIH-COMMON-401"


async def test_me_derives_tenant_from_issuer_and_maps_roles(env: Env) -> None:
    response = await env.api.get("/v1/me", headers=env.auth(ISSUER_A, ["SITE_ADMIN", "RESIDENT"]))
    assert response.status_code == 200
    body = response.json()
    assert body["tenant"]["slug"] == "building"
    assert body["tenant"]["id"] == str(env.tenant_a)
    assert body["roles"] == ["TenantAdmin"]
    assert "smtp-account:write" in body["permissions"]


async def test_tenant_claim_in_token_is_ignored(env: Env) -> None:
    headers = env.auth(ISSUER_A, ["MANAGER"], tenant_id=str(env.tenant_b), tenant="trace")
    body = (await env.api.get("/v1/me", headers=headers)).json()
    assert body["tenant"]["id"] == str(env.tenant_a)
    assert body["roles"] == ["Viewer"]
    assert "smtp-account:write" not in body["permissions"]


async def test_untrusted_issuer_is_rejected(env: Env) -> None:
    headers = env.auth("https://evil.example/realms/x", ["SITE_ADMIN"])
    assert (await env.api.get("/v1/me", headers=headers)).status_code == 401


async def test_wrong_signature_is_rejected(env: Env) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = int(time.time())
    token = jwt.encode(
        {"iss": ISSUER_A, "sub": "x", "azp": CLIENT_ID, "iat": now, "exp": now + 60, "realm_access": {"roles": []}},
        other,
        algorithm="RS256",
    )
    assert (await env.api.get("/v1/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401


async def test_expired_token_is_rejected(env: Env) -> None:
    now = int(time.time())
    headers = env.auth(ISSUER_A, ["SITE_ADMIN"], iat=now - 600, exp=now - 300)
    assert (await env.api.get("/v1/me", headers=headers)).status_code == 401


async def test_foreign_client_is_rejected(env: Env) -> None:
    headers = env.auth(ISSUER_A, ["SITE_ADMIN"], azp="some-other-client")
    assert (await env.api.get("/v1/me", headers=headers)).status_code == 401


async def test_hs256_alg_confusion_is_rejected(env: Env) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"iss": ISSUER_A, "sub": "x", "azp": CLIENT_ID, "iat": now, "exp": now + 60},
        "shared-secret-guess-that-is-long-enough-32b",
        algorithm="HS256",
    )
    assert (await env.api.get("/v1/me", headers={"Authorization": f"Bearer {token}"})).status_code == 401


async def test_second_issuer_maps_to_second_tenant(env: Env) -> None:
    body = (await env.api.get("/v1/me", headers=env.auth(ISSUER_B, ["SYSTEM_ADMIN"]))).json()
    assert body["tenant"]["slug"] == "trace"


async def test_dev_header_works_only_when_enabled(env: Env) -> None:
    response = await env.api.get("/v1/me", headers={"X-AIH-Dev-User": "trace:Viewer"})
    assert response.status_code == 200
    assert response.json()["roles"] == ["Viewer"]
    env.app.state.settings = env.app.state.settings.model_copy(update={"auth_dev_mode": False})
    try:
        assert (await env.api.get("/v1/me", headers={"X-AIH-Dev-User": "trace:Viewer"})).status_code == 401
    finally:
        env.app.state.settings = env.app.state.settings.model_copy(update={"auth_dev_mode": True})


async def test_audit_events_are_append_only(env: Env) -> None:
    async with env.infra.engine.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO audit.audit_events (id, actor_subject, action, resource_type, outcome)"
                " VALUES (gen_random_uuid(), 't', 'test', 'test', 'success')"
            )
        )
        await conn.commit()
        with pytest.raises(DBAPIError, match="append-only"):
            await conn.execute(text("DELETE FROM audit.audit_events"))
        await conn.rollback()


def test_dev_mode_cannot_be_enabled_in_prod() -> None:
    from pydantic import ValidationError

    from aih_api.settings import ApiSettings

    with pytest.raises(ValidationError, match="AIH_AUTH_DEV_MODE"):
        ApiSettings(environment="prod", auth_dev_mode=True)
