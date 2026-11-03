from __future__ import annotations

import asyncio
import uuid
from typing import Any

import pytest
from conftest_api import ISSUER_B, Env  # type: ignore[import-not-found]
from sqlalchemy import text

pytestmark = pytest.mark.integration

ACL_USER = "hub-test"
ACL_PASSWORD = "acl-test-only-password"


def _base(env: Env, tenant: uuid.UUID | None = None) -> str:
    return f"/v1/tenants/{tenant or env.tenant_a}/cache-accounts"


def valkey_payload(valkey: Any, name: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "name": name,
        "providerType": "valkey",
        "host": valkey.host,
        "port": valkey.port,
        "environment": "test",
        "consoleUrl": "http://localhost:28030/admin/cache/providers",
    }
    payload.update(overrides)
    return payload


async def _create(env: Env, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = await env.api.post(_base(env), json=payload, headers=headers or env.auth())
    assert response.status_code == 201, response.text
    return dict(response.json())


@pytest.fixture(scope="module")
async def acl_user(valkey: Any) -> None:
    reader, writer = await asyncio.open_connection(valkey.host, valkey.port)
    command = ["ACL", "SETUSER", ACL_USER, "on", f">{ACL_PASSWORD}", "~*", "+@all"]
    writer.write(f"*{len(command)}\r\n".encode() + b"".join(b"$%d\r\n%s\r\n" % (len(c), c.encode()) for c in command))
    await writer.drain()
    assert (await reader.readline()).startswith(b"+OK")
    writer.close()
    await writer.wait_closed()


async def test_cache_provider_types(env: Env) -> None:
    response = await env.api.get("/v1/provider-types/cache", headers=env.auth())
    assert {c["type"] for c in response.json()} == {"valkey", "redis"}


async def test_connection_test_reports_server_summary(env: Env, valkey: Any) -> None:
    account = await _create(env, valkey_payload(valkey, "Yerel Valkey"))
    assert account["hasSecret"] is False
    assert account["consoleUrl"] == "http://localhost:28030/admin/cache/providers"

    response = await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())

    body = response.json()
    assert response.status_code == 200, response.text
    assert body["outcome"] == "passed"
    assert [s["step"] for s in body["steps"]] == ["dns", "tcp", "connect", "auth", "select", "ping", "info"]
    assert body["server"]["serverName"] == "valkey"
    assert body["server"]["version"].startswith("8.1")
    assert "config_file" not in response.text
    fetched = (await env.api.get(f"{_base(env)}/{account['id']}", headers=env.auth())).json()
    assert fetched["lastTestOutcome"] == "passed"
    assert fetched["serverVersion"].startswith("8.1")


@pytest.mark.usefixtures("acl_user")
async def test_acl_credentials_are_encrypted_and_verified(env: Env, valkey: Any) -> None:
    payload = valkey_payload(valkey, "ACL Valkey", authMode="acl", username=ACL_USER, password=ACL_PASSWORD)
    account = await _create(env, payload)
    assert account["hasSecret"] is True
    assert ACL_PASSWORD not in str(account)
    passed = await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())
    assert passed.json()["outcome"] == "passed"

    wrong = await _create(env, {**payload, "name": "ACL wrong", "password": "not-the-password"})
    failed = (await env.api.post(f"{_base(env)}/{wrong['id']}/test-connection", headers=env.auth())).json()
    assert failed["outcome"] == "failed"
    assert failed["errorCode"] == "CACHE_AUTH_FAILED"
    assert "not-the-password" not in str(failed)
    async with env.infra.engine.connect() as conn:
        ciphertexts = (await conn.execute(text("SELECT ciphertext FROM provider.secrets"))).scalars().all()
    assert all(ACL_PASSWORD.encode() not in bytes(c) for c in ciphertexts)


async def test_unreachable_server_fails_without_leaking_details(env: Env) -> None:
    account = await _create(env, {"name": "Kapalı", "host": "127.0.0.1", "port": 1, "environment": "test"})
    body = (await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())).json()
    assert body["outcome"] == "failed"
    assert body["errorCode"] == "CACHE_CONNECT_FAILED"
    assert body["server"] is None


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"environment": "production"}, "AIH-CACHE-001"),
        ({"authMode": "acl", "password": "x"}, "AIH-CACHE-002"),
        ({"authMode": "password"}, "AIH-CACHE-003"),
        ({"host": "metadata.google.internal"}, "AIH-CACHE-004"),
    ],
)
async def test_business_rules_are_enforced(env: Env, valkey: Any, overrides: dict[str, Any], code: str) -> None:
    payload = valkey_payload(valkey, f"rule-{uuid.uuid4().hex[:8]}", **overrides)
    response = await env.api.post(_base(env), json=payload, headers=env.auth())
    assert response.status_code == 422, response.text
    assert response.json()["code"] == code


@pytest.mark.parametrize(
    "console_url",
    ["javascript:alert(1)", "ftp://files.example.com", "http://user:pass@example.com", "http://exa mple.com"],
)
async def test_console_url_must_be_plain_http(env: Env, valkey: Any, console_url: str) -> None:
    payload = valkey_payload(valkey, f"url-{uuid.uuid4().hex[:8]}", consoleUrl=console_url)
    assert (await env.api.post(_base(env), json=payload, headers=env.auth())).status_code == 422


async def test_tenant_isolation_and_viewer_masking(env: Env, valkey: Any) -> None:
    account = await _create(env, valkey_payload(valkey, "İzole Valkey", host="cache.internal.example.com"))

    other = await env.api.get(f"{_base(env, env.tenant_b)}", headers=env.auth(ISSUER_B, ["SYSTEM_ADMIN"]))
    assert account["id"] not in other.text
    cross = await env.api.get(f"{_base(env)}/{account['id']}", headers=env.auth(ISSUER_B, ["SYSTEM_ADMIN"]))
    assert cross.status_code in (403, 404)

    viewer = env.auth(roles=["MANAGER"])
    seen = (await env.api.get(f"{_base(env)}/{account['id']}", headers=viewer)).json()
    assert seen["host"] == "***.example.com"
    denied = await env.api.post(_base(env), json=valkey_payload(valkey, "viewer"), headers=viewer)
    assert denied.status_code == 403
    assert (await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=viewer)).status_code == 403


async def test_update_requires_current_version_and_single_default(env: Env, valkey: Any) -> None:
    first = await _create(env, valkey_payload(valkey, "Varsayılan 1", makeDefault=True))
    second = await _create(env, valkey_payload(valkey, "Varsayılan 2"))

    stale = await env.api.patch(
        f"{_base(env)}/{second['id']}", json={"databaseIndex": 2}, headers={**env.auth(), "If-Match": 'W/"9"'}
    )
    assert stale.status_code == 412
    made = await env.api.post(f"{_base(env)}/{second['id']}/make-default", headers={**env.auth(), "If-Match": 'W/"1"'})
    assert made.json()["isDefault"] is True
    refreshed = (await env.api.get(f"{_base(env)}/{first['id']}", headers=env.auth())).json()
    assert refreshed["isDefault"] is False


def redis_payload(valkey: Any, name: str, license_: dict[str, Any] | None, **overrides: Any) -> dict[str, Any]:
    payload = valkey_payload(valkey, name, providerType="redis", **overrides)
    if license_ is not None:
        payload["license"] = license_
    return payload


@pytest.mark.parametrize(
    ("license_", "code"),
    [
        (None, "AIH-CACHE-007"),
        ({"type": "agpl-3.0"}, "AIH-CACHE-008"),
        ({"type": "redis-enterprise", "acknowledged": True, "key": "k"}, "AIH-CACHE-009"),
        ({"type": "agpl-3.0", "acknowledged": True, "key": "k"}, "AIH-CACHE-010"),
        ({"type": "redis-cloud", "holder": "Aka", "acknowledged": True}, "AIH-CACHE-011"),
    ],
)
async def test_redis_requires_a_declared_license(
    env: Env, valkey: Any, license_: dict[str, Any] | None, code: str
) -> None:
    payload = redis_payload(valkey, f"redis-{uuid.uuid4().hex[:8]}", license_)
    response = await env.api.post(_base(env), json=payload, headers=env.auth())
    assert response.status_code == 422, response.text
    assert response.json()["code"] == code


async def test_commercial_redis_license_key_is_encrypted_and_tracked(env: Env, valkey: Any) -> None:
    license_ = {
        "type": "redis-enterprise",
        "holder": "Aka Yazılım A.Ş.",
        "reference": "SUB-2026-001",
        "expiresOn": "2099-12-31",
        "key": "enterprise-license-key-test-only",
        "acknowledged": True,
    }
    account = await _create(env, redis_payload(valkey, "Kurumsal Redis", license_))

    assert account["licenseStatus"] == "valid"
    assert account["license"]["hasKey"] is True
    assert account["license"]["acknowledgedBy"] == "user-1"
    assert "enterprise-license-key" not in str(account)
    async with env.infra.engine.connect() as conn:
        ciphertexts = (await conn.execute(text("SELECT ciphertext FROM provider.secrets"))).scalars().all()
        audit = (
            (
                await conn.execute(
                    text("SELECT details::text FROM audit.audit_events WHERE resource_id = :id"), {"id": account["id"]}
                )
            )
            .scalars()
            .all()
        )
    assert all(b"enterprise-license-key" not in bytes(c) for c in ciphertexts)
    assert "redis-enterprise" in " ".join(audit)

    expired = {**license_, "key": None, "expiresOn": "2020-01-01"}
    updated = await env.api.patch(
        f"{_base(env)}/{account['id']}", json={"license": expired}, headers={**env.auth(), "If-Match": 'W/"1"'}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["licenseStatus"] == "expired"
    assert updated.json()["license"]["hasKey"] is True


async def test_valkey_never_carries_a_license(env: Env, valkey: Any) -> None:
    payload = valkey_payload(valkey, "Lisanssız Valkey", license={"type": "agpl-3.0", "acknowledged": True})
    account = await _create(env, payload)
    assert account["license"] is None
    assert account["licenseStatus"] == "not_required"
