from __future__ import annotations

import asyncio
import uuid
from typing import Any

import httpx
import pytest
from conftest_api import ISSUER_A, ISSUER_B, Env  # type: ignore[import-not-found]
from test_smtp_accounts_integration import _base, _create, custom_payload, mailpit_payload  # type: ignore[import-not-found]

pytestmark = pytest.mark.integration


async def _mailpit_messages(mailpit: Any) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(base_url=f"http://{mailpit.host}:{mailpit.http_port}") as client:
        for _ in range(20):
            data = (await client.get("/api/v1/messages")).json()
            if data.get("messages"):
                return list(data["messages"])
            await asyncio.sleep(0.2)
    return []


def _key() -> str:
    return f"test-{uuid.uuid4()}"


async def test_send_test_email_is_captured_by_mailpit(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit send"))
    key = _key()
    url = f"{_base(env)}/{account['id']}/send-test-email"
    headers = {**env.auth(), "Idempotency-Key": key, "X-Correlation-Id": "send-test-0001"}
    response = await env.api.post(url, json={"recipient": "ops@anywhere.example", "confirm": True}, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "accepted_by_smtp"
    assert body["attemptCount"] == 1
    assert body["attempts"][0]["outcome"] == "accepted"
    assert body["correlationId"] == "send-test-0001"

    messages = await _mailpit_messages(mailpit)
    subjects = [m["Subject"] for m in messages]
    assert "Aka Integration Hub — SMTP test e-postası" in subjects
    captured = next(m for m in messages if m["MessageID"] == body["messageId"].strip("<>"))
    assert captured["To"][0]["Address"] == "ops@anywhere.example"

    # Aynı anahtar → aynı kayıt, ikinci gönderim yok
    again = await env.api.post(url, json={"recipient": "ops@anywhere.example", "confirm": True}, headers=headers)
    assert again.json()["id"] == body["id"]
    assert len([m for m in await _mailpit_messages(mailpit) if m["MessageID"] == captured["MessageID"]]) == 1
    # Aynı anahtar + farklı gövde → 409
    other = await env.api.post(url, json={"recipient": "else@anywhere.example", "confirm": True}, headers=headers)
    assert other.status_code == 409

    detail = (await env.api.get(f"/v1/tenants/{env.tenant_a}/email-deliveries/{body['id']}", headers=env.auth())).json()
    assert detail["attempts"][0]["smtpResponseClass"] == "2xx"
    refreshed = (await env.api.get(f"{_base(env)}/{account['id']}", headers=env.auth())).json()
    assert refreshed["lastSuccessSendAt"] is not None


async def test_send_requires_confirmation_and_idempotency_key(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit confirm"))
    url = f"{_base(env)}/{account['id']}/send-test-email"
    no_confirm = await env.api.post(
        url, json={"recipient": "a@b.example", "confirm": False}, headers={**env.auth(), "Idempotency-Key": _key()}
    )
    assert no_confirm.json()["code"] == "AIH-EMAIL-003"
    no_key = await env.api.post(url, json={"recipient": "a@b.example", "confirm": True}, headers=env.auth())
    assert no_key.status_code == 400


async def test_real_provider_recipient_must_be_safe(env: Env) -> None:
    account = await _create(env, custom_payload("Safe recipient"))
    url = f"{_base(env)}/{account['id']}/send-test-email"
    response = await env.api.post(
        url,
        json={"recipient": "stranger@gmail.example", "confirm": True},
        headers={**env.auth(), "Idempotency-Key": _key()},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "AIH-EMAIL-002"


async def test_failed_send_is_recorded(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit fail", password="wrong-password"))
    response = await env.api.post(
        f"{_base(env)}/{account['id']}/send-test-email",
        json={"recipient": "ops@x.example", "confirm": True},
        headers={**env.auth(), "Idempotency-Key": _key()},
    )
    body = response.json()
    assert body["status"] == "failed"
    assert body["lastErrorCode"] == "SMTP_AUTH_FAILED"
    listing = await env.api.get(
        f"/v1/tenants/{env.tenant_a}/email-deliveries", headers=env.auth(), params={"status": "failed"}
    )
    assert body["id"] in [d["id"] for d in listing.json()]


async def test_viewer_cannot_send_and_sees_masked_recipient(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit viewer send"))
    viewer = env.auth(ISSUER_A, ["MANAGER"])
    url = f"{_base(env)}/{account['id']}/send-test-email"
    denied = await env.api.post(
        url, json={"recipient": "a@b.example", "confirm": True}, headers={**viewer, "Idempotency-Key": _key()}
    )
    assert denied.status_code == 403
    await env.api.post(
        url, json={"recipient": "person@b.example", "confirm": True}, headers={**env.auth(), "Idempotency-Key": _key()}
    )
    listing = (await env.api.get(f"/v1/tenants/{env.tenant_a}/email-deliveries", headers=viewer)).json()
    assert any(d["recipient"] == "p***@b.example" for d in listing)


async def test_deliveries_are_tenant_isolated(env: Env, mailpit: Any) -> None:
    account = await _create(env, mailpit_payload(mailpit, "Mailpit isolation"))
    sent = await env.api.post(
        f"{_base(env)}/{account['id']}/send-test-email",
        json={"recipient": "ops@x.example", "confirm": True},
        headers={**env.auth(), "Idempotency-Key": _key()},
    )
    delivery_id = sent.json()["id"]
    b_admin = env.auth(ISSUER_B, ["SYSTEM_ADMIN"])
    own = await env.api.get(f"/v1/tenants/{env.tenant_b}/email-deliveries/{delivery_id}", headers=b_admin)
    assert own.status_code == 404
    send_other = await env.api.post(
        f"{_base(env, env.tenant_b)}/{account['id']}/send-test-email",
        json={"recipient": "ops@x.example", "confirm": True},
        headers={**b_admin, "Idempotency-Key": _key()},
    )
    assert send_other.status_code == 404
