from __future__ import annotations

import uuid
from typing import Any

import pytest
from conftest_api import ISSUER_A, ISSUER_B, Env  # type: ignore[import-not-found]
from mailpit_credentials import MAILPIT_PASSWORD, MAILPIT_USER  # type: ignore[import-not-found]
from sqlalchemy import text

pytestmark = pytest.mark.integration


def _base(env: Env, tenant: uuid.UUID | None = None) -> str:
    return f"/v1/tenants/{tenant or env.tenant_a}/smtp-accounts"


def mailpit_payload(mailpit: Any, name: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "name": name,
        "providerType": "mailpit_test",
        "host": mailpit.host,
        "port": mailpit.port,
        "tlsMode": "none",
        "authMode": "smtp_auth",
        "username": MAILPIT_USER,
        "password": MAILPIT_PASSWORD,
        "senderAddress": "noreply@building.example",
        "senderName": "BuildingFlow",
        "environment": "test",
    }
    payload.update(overrides)
    return payload


def custom_payload(name: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "name": name,
        "providerType": "custom_smtp",
        "host": "smtp.example.com",
        "port": 587,
        "tlsMode": "starttls",
        "authMode": "smtp_auth",
        "username": "mailer@example.com",
        "password": "super-secret-value-123",
        "senderAddress": "noreply@example.com",
        "environment": "production",
    }
    payload.update(overrides)
    return payload


async def _create(env: Env, payload: dict[str, Any], **kw: Any) -> dict[str, Any]:
    response = await env.api.post(_base(env, kw.get("tenant")), json=payload, headers=kw.get("headers") or env.auth())
    assert response.status_code == 201, response.text
    return dict(response.json())


async def test_capabilities_list_provider_types(env: Env) -> None:
    response = await env.api.get("/v1/provider-types/smtp", headers=env.auth())
    types = {c["type"]: c for c in response.json()}
    assert set(types) == {"custom_smtp", "microsoft_365", "google_workspace", "amazon_ses", "mailpit_test"}
    assert types["microsoft_365"]["plannedAuthModes"] == ["oauth2"]
    assert types["mailpit_test"]["environments"] == ["test"]


async def test_create_stores_secret_encrypted_and_never_returns_it(env: Env) -> None:
    response = await env.api.post(_base(env), json=custom_payload("Prod relay"), headers=env.auth())
    assert response.status_code == 201
    body = response.json()
    assert body["hasSecret"] is True
    assert "password" not in body
    assert "super-secret-value-123" not in response.text
    assert response.headers["ETag"] == 'W/"1"'
    assert response.headers["Location"].endswith(body["id"])
    async with env.infra.engine.connect() as conn:
        ciphertext = (await conn.execute(text("SELECT ciphertext FROM provider.secrets"))).scalars().all()
        audit_rows = (
            await conn.execute(
                text("SELECT action, details::text FROM audit.audit_events WHERE resource_id = :id"),
                {"id": body["id"]},
            )
        ).all()
        audit_text = " ".join(r[1] for r in audit_rows)
    assert ciphertext
    assert all(b"super-secret-value-123" not in bytes(c) for c in ciphertext)
    assert [r[0] for r in audit_rows] == ["smtp-account.create"]
    assert "super-secret" not in audit_text
    fetched = await env.api.get(f"{_base(env)}/{body['id']}", headers=env.auth())
    assert "super-secret" not in fetched.text


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"tlsMode": "none", "providerType": "custom_smtp", "authMode": "none"}, "AIH-SMTP-006"),
        ({"providerType": "microsoft_365", "authMode": "oauth2", "host": "smtp.office365.com"}, "AIH-SMTP-004"),
        ({"providerType": "mailpit_test", "tlsMode": "none", "authMode": "none"}, "AIH-SMTP-001"),
        ({"tlsMode": "implicit", "port": 587}, "AIH-SMTP-010"),
        ({"password": None}, "AIH-SMTP-009"),
        ({"username": None}, "AIH-SMTP-008"),
        ({"environment": "test", "tlsMode": "none"}, "AIH-SMTP-007"),
    ],
)
async def test_business_rules_are_enforced(env: Env, overrides: dict[str, Any], code: str) -> None:
    payload = custom_payload(f"rule-{uuid.uuid4().hex[:8]}", **overrides)
    response = await env.api.post(_base(env), json=payload, headers=env.auth())
    assert response.status_code == 422, response.text
    assert response.json()["code"] == code


@pytest.mark.parametrize(
    "host", ["http://smtp.example.com", "smtp.example.com/path", "user@smtp.example.com", "smtp example.com", ""]
)
async def test_host_must_be_plain_hostname(env: Env, host: str) -> None:
    response = await env.api.post(_base(env), json=custom_payload("bad-host", host=host), headers=env.auth())
    assert response.status_code == 422


async def test_header_injection_in_sender_name_is_rejected(env: Env) -> None:
    payload = custom_payload("inject", senderName="Ops\r\nBcc: evil@example.com")
    assert (await env.api.post(_base(env), json=payload, headers=env.auth())).status_code == 422


async def test_unknown_fields_are_rejected(env: Env) -> None:
    payload = custom_payload("extra", tenantId=str(env.tenant_b))
    assert (await env.api.post(_base(env), json=payload, headers=env.auth())).status_code == 422


async def test_duplicate_name_conflicts(env: Env) -> None:
    await _create(env, custom_payload("Duplicate"))
    response = await env.api.post(_base(env), json=custom_payload("duplicate"), headers=env.auth())
    assert response.status_code == 409
    assert response.json()["code"] == "AIH-SMTP-012"


async def test_single_default_per_environment(env: Env) -> None:
    first = await _create(env, custom_payload("Default 1", makeDefault=True))
    second = await _create(env, custom_payload("Default 2"))
    assert first["isDefault"] is True
    response = await env.api.post(
        f"{_base(env)}/{second['id']}/make-default", headers={**env.auth(), "If-Match": 'W/"1"'}
    )
    assert response.status_code == 200, response.text
    assert response.json()["isDefault"] is True
    refreshed = (await env.api.get(f"{_base(env)}/{first['id']}", headers=env.auth())).json()
    assert refreshed["isDefault"] is False
    async with env.infra.engine.connect() as conn:
        count = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM provider.smtp_accounts WHERE tenant_id = :t AND environment = 'production'"
                    " AND is_default"
                ),
                {"t": env.tenant_a},
            )
        ).scalar_one()
    assert count == 1


async def test_optimistic_locking(env: Env) -> None:
    account = await _create(env, custom_payload("Locking"))
    url = f"{_base(env)}/{account['id']}"
    missing = await env.api.patch(url, json={"priority": 5}, headers=env.auth())
    assert missing.status_code == 428
    ok = await env.api.patch(url, json={"priority": 5}, headers={**env.auth(), "If-Match": 'W/"1"'})
    assert ok.status_code == 200, ok.text
    assert ok.json()["version"] == 2
    stale = await env.api.patch(url, json={"priority": 6}, headers={**env.auth(), "If-Match": 'W/"1"'})
    assert stale.status_code == 412


async def test_secret_rotation(env: Env) -> None:
    account = await _create(env, custom_payload("Rotate"))
    url = f"{_base(env)}/{account['id']}/secret"
    response = await env.api.post(
        url, json={"password": "rotated-pass-456"}, headers={**env.auth(), "If-Match": 'W/"1"'}
    )
    assert response.status_code == 200
    assert "rotated-pass" not in response.text


async def test_cross_tenant_access_returns_404(env: Env) -> None:
    account = await _create(env, custom_payload("Tenant A only"))
    b_admin = env.auth(ISSUER_B, ["SYSTEM_ADMIN"])
    # B, A'nın path'ini kullanamaz
    assert (await env.api.get(_base(env), headers=b_admin)).status_code == 404
    assert (await env.api.get(f"{_base(env)}/{account['id']}", headers=b_admin)).status_code == 404
    # B kendi path'inde A'nın hesap id'sini göremez (RLS)
    own = f"{_base(env, env.tenant_b)}/{account['id']}"
    assert (await env.api.get(own, headers=b_admin)).status_code == 404
    patch = await env.api.patch(own, json={"priority": 1}, headers={**b_admin, "If-Match": 'W/"1"'})
    assert patch.status_code == 404
    listing = (await env.api.get(_base(env, env.tenant_b), headers=b_admin)).json()
    assert all(item["tenantId"] == str(env.tenant_b) for item in listing["items"])


async def test_rls_hides_other_tenant_rows_even_without_where(env: Env) -> None:
    await _create(env, custom_payload("RLS probe"))
    async with env.app.state.db.transaction(env.tenant_b) as session:
        visible = (await session.execute(text("SELECT count(*) FROM provider.smtp_accounts"))).scalar_one()
        secrets = (await session.execute(text("SELECT count(*) FROM provider.secrets"))).scalar_one()
    assert visible == 0
    assert secrets == 0


async def test_viewer_reads_masked_and_cannot_write(env: Env) -> None:
    await _create(env, custom_payload("Masked"))
    viewer = env.auth(ISSUER_A, ["MANAGER"])
    listing = await env.api.get(_base(env), headers=viewer, params={"q": "Masked"})
    item = listing.json()["items"][0]
    assert item["host"] == "***.example.com"
    assert item["username"] == "m***@example.com"
    assert (await env.api.post(_base(env), json=custom_payload("Nope"), headers=viewer)).status_code == 403


async def test_list_filters_and_pagination(env: Env) -> None:
    for i in range(3):
        await _create(env, custom_payload(f"Page {i}", priority=900 + i))
    first = (await env.api.get(_base(env), headers=env.auth(), params={"q": "Page", "limit": 2})).json()
    assert len(first["items"]) == 2
    assert first["nextCursor"]
    second = (
        await env.api.get(
            _base(env), headers=env.auth(), params={"q": "Page", "limit": 2, "cursor": first["nextCursor"]}
        )
    ).json()
    assert len(second["items"]) == 1
    assert second["nextCursor"] is None
    bad = await env.api.get(_base(env), headers=env.auth(), params={"cursor": "%%%"})
    assert bad.status_code == 400


async def test_connection_test_against_mailpit_passes(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit OK"))
    response = await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["outcome"] == "passed"
    assert [s["step"] for s in body["steps"]] == ["dns", "tcp", "greeting", "auth"]
    refreshed = (await env.api.get(f"{_base(env)}/{account['id']}", headers=env.auth())).json()
    assert refreshed["lastTestOutcome"] == "passed"
    assert refreshed["version"] == account["version"]
    history = (await env.api.get(f"{_base(env)}/{account['id']}/connection-tests", headers=env.auth())).json()
    assert history[0]["id"] == body["id"]


async def test_connection_test_reports_auth_failure_without_raw_response(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit bad pass", password="wrong-password"))
    body = (await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())).json()
    assert body["outcome"] == "failed"
    assert body["errorCode"] == "SMTP_AUTH_FAILED"
    assert body["steps"][-1] == {**body["steps"][-1], "step": "auth", "outcome": "failed"}


async def test_connection_test_reports_unreachable_port(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit closed", port=1, authMode="none", password=None))
    body = (await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=env.auth())).json()
    assert body["outcome"] == "failed"
    assert body["errorCode"] == "SMTP_CONNECT_FAILED"
    assert [s["outcome"] for s in body["steps"]] == ["passed", "failed"]


async def test_viewer_cannot_run_connection_test(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit viewer"))
    viewer = env.auth(ISSUER_A, ["MANAGER"])
    assert (await env.api.post(f"{_base(env)}/{account['id']}/test-connection", headers=viewer)).status_code == 403
