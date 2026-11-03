from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from conftest_api import ISSUER_B, Env  # type: ignore[import-not-found]
from sqlalchemy import text

from aih_api.providers.sms.capabilities import SmsProviderType
from aih_api.providers.sms.gateways import NetgsmGateway

pytestmark = pytest.mark.integration

ALLOWED_PHONE = "0555 111 22 33"


def _accounts(env: Env, tenant: uuid.UUID | None = None) -> str:
    return f"/v1/tenants/{tenant or env.tenant_a}/sms-accounts"


def _messages(env: Env) -> str:
    return f"/v1/tenants/{env.tenant_a}/sms/messages"


def _key() -> dict[str, str]:
    return {"Idempotency-Key": f"test-{uuid.uuid4().hex}"}


async def _create(env: Env, **overrides: Any) -> dict[str, Any]:
    payload = {
        "name": f"sms-{uuid.uuid4().hex[:8]}",
        "providerType": "mock_test",
        "senderHeader": "AKAHUB",
        "environment": "test",
        **overrides,
    }
    response = await env.api.post(_accounts(env), json=payload, headers=env.auth())
    assert response.status_code == 201, response.text
    return dict(response.json())


async def _load(env: Env, account: dict[str, Any], quantity: int) -> dict[str, Any]:
    response = await env.api.post(
        f"{_accounts(env)}/{account['id']}/credits", json={"quantity": quantity, "reason": "test"}, headers=env.auth()
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.fixture
def netgsm_responses(env: Env) -> Iterator[list[httpx.Response]]:
    responses: list[httpx.Response] = []
    seen: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.content)
        return responses.pop(0)

    original = env.app.state.sms_gateways[SmsProviderType.NETGSM]
    env.app.state.sms_gateways[SmsProviderType.NETGSM] = NetgsmGateway(httpx.MockTransport(handler))
    yield responses
    env.app.state.sms_gateways[SmsProviderType.NETGSM] = original


async def test_sms_provider_types(env: Env) -> None:
    types = {c["type"]: c for c in (await env.api.get("/v1/provider-types/sms", headers=env.auth())).json()}
    assert types["netgsm"]["available"] is True
    assert types["verimor"]["available"] is False
    assert types["mock_test"]["environments"] == ["test"]


async def test_test_sms_consumes_credit_and_keeps_only_masked_phone(env: Env) -> None:
    account = await _create(env)
    loaded = await _load(env, account, 5)
    assert loaded["creditBalance"] == 5

    response = await env.api.post(
        f"{_accounts(env)}/{account['id']}/send-test",
        json={"phone": "0532 123 45 67", "confirm": True},
        headers={**env.auth(), **_key()},
    )

    body = response.json()
    assert response.status_code == 200, response.text
    assert body["status"] == "sent"
    assert body["phoneMasked"] == "+90532*****67"
    assert body["providerMessageId"].startswith("MOCK-")
    assert "5321234567" not in response.text
    fetched = (await env.api.get(f"{_accounts(env)}/{account['id']}", headers=env.auth())).json()
    assert fetched["creditBalance"] == 4
    assert fetched["lastTestOutcome"] == "passed"
    history = (await env.api.get(f"{_accounts(env)}/{account['id']}/credits", headers=env.auth())).json()
    assert [(h["kind"], h["quantity"], h["balanceAfter"]) for h in history] == [("consume", -1, 4), ("load", 5, 5)]
    async with env.infra.engine.connect() as conn:
        stored = (await conn.execute(text("SELECT phone_masked FROM sms.messages"))).scalars().all()
    assert all("1234567" not in phone for phone in stored)


async def test_insufficient_credit_rejects_without_recording(env: Env) -> None:
    account = await _create(env)
    response = await env.api.post(
        f"{_accounts(env)}/{account['id']}/send-test",
        json={"phone": "05321234567", "confirm": True},
        headers={**env.auth(), **_key()},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "AIH-SMS-016"
    listed = (await env.api.get(f"{_messages(env)}?accountId={account['id']}", headers=env.auth())).json()
    assert listed["items"] == []


async def test_send_api_uses_default_account_and_is_idempotent(env: Env) -> None:
    account = await _create(env, makeDefault=True)
    await _load(env, account, 10)
    payload = {"environment": "test", "phone": "05321234567", "body": "Aidat hatırlatması", "purpose": "operational"}
    key = _key()

    first = await env.api.post(_messages(env), json=payload, headers={**env.auth(), **key})
    replay = await env.api.post(_messages(env), json=payload, headers={**env.auth(), **key})
    conflict = await env.api.post(_messages(env), json={**payload, "body": "farklı"}, headers={**env.auth(), **key})

    assert first.status_code == 200, first.text
    assert first.json()["accountId"] == account["id"]
    assert replay.json()["id"] == first.json()["id"]
    assert conflict.status_code == 409
    fetched = (await env.api.get(f"{_accounts(env)}/{account['id']}", headers=env.auth())).json()
    assert fetched["creditBalance"] == 9


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"purpose": "marketing"}, "AIH-SMS-014"),
        ({"phone": "02121234567"}, "AIH-SMS-013"),
        ({"body": "ş" * 700}, "AIH-SMS-015"),
    ],
)
async def test_send_rules(env: Env, overrides: dict[str, Any], code: str) -> None:
    account = await _create(env)
    await _load(env, account, 50)
    payload = {"accountId": account["id"], "phone": "05321234567", "body": "Merhaba", "purpose": "operational"}
    response = await env.api.post(_messages(env), json={**payload, **overrides}, headers={**env.auth(), **_key()})
    assert response.status_code == 422, response.text
    assert response.json()["code"] == code


@pytest.mark.usefixtures("netgsm_responses")
async def test_netgsm_failure_refunds_and_unknown_keeps_credit(
    env: Env, netgsm_responses: list[httpx.Response]
) -> None:
    account = await _create(
        env, providerType="netgsm", username="8501234567", password="api-pass", environment="production"
    )
    assert account["hasSecret"] is True
    await _load(env, account, 10)
    netgsm_responses.extend(
        [httpx.Response(200, text="30"), httpx.Response(503), httpx.Response(200, text="00 987654")]
    )
    payload = {"accountId": account["id"], "phone": "05321234567", "body": "Bakım duyurusu", "purpose": "operational"}

    failed = (await env.api.post(_messages(env), json=payload, headers={**env.auth(), **_key()})).json()
    unknown = (await env.api.post(_messages(env), json=payload, headers={**env.auth(), **_key()})).json()
    sent = (await env.api.post(_messages(env), json=payload, headers={**env.auth(), **_key()})).json()

    assert (failed["status"], failed["errorCode"]) == ("failed", "SMS_AUTH_FAILED")
    assert (unknown["status"], unknown["errorCode"]) == ("unknown", "SMS_PROVIDER_UNAVAILABLE")
    assert (sent["status"], sent["providerMessageId"]) == ("sent", "987654")
    balance = (await env.api.get(f"{_accounts(env)}/{account['id']}", headers=env.auth())).json()["creditBalance"]
    assert balance == 8


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"environment": "production"}, "AIH-SMS-002"),
        ({"providerType": "netgsm", "password": "x"}, "AIH-SMS-004"),
        ({"providerType": "netgsm", "username": "8501234567"}, "AIH-SMS-005"),
        ({"providerType": "verimor", "username": "u", "password": "p"}, "AIH-SMS-001"),
    ],
)
async def test_account_rules(env: Env, overrides: dict[str, Any], code: str) -> None:
    payload = {"name": f"r-{uuid.uuid4().hex[:6]}", "providerType": "mock_test", "senderHeader": "AKAHUB"}
    response = await env.api.post(
        _accounts(env), json={**payload, "environment": "test", **overrides}, headers=env.auth()
    )
    assert response.status_code == 422, response.text
    assert response.json()["code"] == code


async def test_real_provider_test_sms_only_to_allowlisted_numbers(
    env: Env, netgsm_responses: list[httpx.Response]
) -> None:
    account = await _create(env, providerType="netgsm", username="8501234567", password="api-pass")
    await _load(env, account, 3)
    denied = await env.api.post(
        f"{_accounts(env)}/{account['id']}/send-test",
        json={"phone": "05321234567", "confirm": True},
        headers={**env.auth(), **_key()},
    )
    assert denied.json()["code"] == "AIH-SMS-018"
    netgsm_responses.append(httpx.Response(200, text="00 1"))
    allowed = await env.api.post(
        f"{_accounts(env)}/{account['id']}/send-test",
        json={"phone": ALLOWED_PHONE, "confirm": True},
        headers={**env.auth(), **_key()},
    )
    assert allowed.json()["status"] == "sent"


async def test_tenant_isolation_and_viewer_permissions(env: Env) -> None:
    account = await _create(env)
    other = env.auth(ISSUER_B, ["SYSTEM_ADMIN"])
    assert account["id"] not in (await env.api.get(_accounts(env, env.tenant_b), headers=other)).text
    assert (await env.api.get(f"{_accounts(env)}/{account['id']}", headers=other)).status_code in (403, 404)

    viewer = env.auth(roles=["MANAGER"])
    assert (await env.api.get(f"{_accounts(env)}/{account['id']}", headers=viewer)).status_code == 200
    assert (await env.api.get(_messages(env), headers=viewer)).status_code == 200
    credit = await env.api.post(f"{_accounts(env)}/{account['id']}/credits", json={"quantity": 5}, headers=viewer)
    assert credit.status_code == 403
    send = {"accountId": account["id"], "phone": "05321234567", "body": "x", "purpose": "operational"}
    assert (await env.api.post(_messages(env), json=send, headers={**viewer, **_key()})).status_code == 403


async def test_credit_rules(env: Env) -> None:
    account = await _create(env)
    base = f"{_accounts(env)}/{account['id']}/credits"
    assert (await env.api.post(base, json={"quantity": -1}, headers=env.auth())).json()["code"] == "AIH-SMS-010"
    over = await env.api.post(base, json={"kind": "adjust", "quantity": -1}, headers=env.auth())
    assert over.json()["code"] == "AIH-SMS-011"
    refund = await env.api.post(base, json={"kind": "refund", "quantity": 1}, headers=env.auth())
    assert refund.json()["code"] == "AIH-SMS-009"
