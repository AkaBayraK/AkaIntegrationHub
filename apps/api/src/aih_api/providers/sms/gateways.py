"""SMS sağlayıcı adaptörleri.

Adaptörler istisna fırlatmaz; sonucu ``GatewayResult`` ile döner. Sağlayıcı adresi koddadır (kullanıcı URL'i yok →
SSRF yok), ham sağlayıcı yanıtı/telefon/metin loglanmaz ve saklanmaz. Sonucu belirsiz hata ``unknown`` döner:
mutabakat olmadan tekrar gönderim veya kontör iadesi yapılmaz (çift SMS'e karşı).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol
from xml.sax.saxutils import escape

import httpx

from aih_api.providers.sms.capabilities import SmsProviderType
from aih_api.secrets import SecretValue

NETGSM_SEND_URL = "https://api.netgsm.com.tr/sms/send/xml"
NETGSM_TIMEOUT_SECONDS = 10.0
MAX_PROVIDER_RESPONSE_BYTES = 4096
NETGSM_SUCCESS_CODES = frozenset({"00", "01", "02"})
# Netgsm XML API hata kodları: 20 metin/uzunluk, 30 kimlik/IP, 40 başlık, 50/51 İYS, 70 parametre, 85 mükerrer.
NETGSM_PERMANENT_ERRORS = {
    "20": "SMS_TEXT_REJECTED",
    "30": "SMS_AUTH_FAILED",
    "40": "SMS_SENDER_REJECTED",
    "50": "SMS_IYS_REJECTED",
    "51": "SMS_IYS_REJECTED",
    "70": "SMS_REQUEST_INVALID",
    "85": "SMS_DUPLICATE_REJECTED",
}
HTTP_SERVER_ERROR = 500


@dataclass(frozen=True)
class GatewayRequest:
    phone_e164: str
    body: str
    sender_header: str
    username: str | None
    secret: SecretValue | None

    def __repr__(self) -> str:
        return f"GatewayRequest(header={self.sender_header!r}, length={len(self.body)}, secret=***)"


@dataclass(frozen=True)
class GatewayResult:
    outcome: str  # sent | failed | unknown
    provider_message_id: str | None = None
    error_code: str | None = None


class SmsGateway(Protocol):
    async def send(self, request: GatewayRequest) -> GatewayResult: ...


class MockGateway:
    """Geliştirme sağlayıcısı: operatöre gitmez, yalnız kabul kimliği üretir."""

    async def send(self, request: GatewayRequest) -> GatewayResult:  # noqa: ARG002 - SmsGateway sözleşmesi
        return GatewayResult("sent", provider_message_id=f"MOCK-{uuid.uuid4().hex}")


class NetgsmGateway:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    @staticmethod
    def payload(request: GatewayRequest) -> str:
        secret = request.secret.reveal() if request.secret else ""
        body = request.body.replace("]]>", "]]]]><![CDATA[>")
        return (
            '<?xml version="1.0" encoding="UTF-8"?><mainbody><header>'
            '<company dil="TR">Netgsm</company>'
            f"<usercode>{escape(request.username or '')}</usercode><password>{escape(secret)}</password>"
            f"<type>1:n</type><msgheader>{escape(request.sender_header)}</msgheader></header>"
            f"<body><msg><![CDATA[{body}]]></msg><no>{request.phone_e164[3:]}</no></body></mainbody>"
        )

    @staticmethod
    def parse(status: int, text: str) -> GatewayResult:
        if status >= HTTP_SERVER_ERROR:
            return GatewayResult("unknown", error_code="SMS_PROVIDER_UNAVAILABLE")
        parts = text.strip().split()
        code = parts[0] if parts else ""
        if code in NETGSM_SUCCESS_CODES and len(parts) > 1 and parts[1].isdigit():
            return GatewayResult("sent", provider_message_id=parts[1][:100])
        if code in NETGSM_PERMANENT_ERRORS:
            return GatewayResult("failed", error_code=NETGSM_PERMANENT_ERRORS[code])
        return GatewayResult("unknown", error_code="SMS_PROVIDER_RESPONSE_UNKNOWN")

    async def send(self, request: GatewayRequest) -> GatewayResult:
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=NETGSM_TIMEOUT_SECONDS, follow_redirects=False
            ) as client:
                response = await client.post(
                    NETGSM_SEND_URL,
                    content=self.payload(request).encode(),
                    headers={"Content-Type": "application/xml; charset=utf-8"},
                )
        except (httpx.TimeoutException, httpx.TransportError):
            return GatewayResult("unknown", error_code="SMS_PROVIDER_UNAVAILABLE")
        return self.parse(response.status_code, response.text[:MAX_PROVIDER_RESPONSE_BYTES])


def default_gateways() -> dict[SmsProviderType, SmsGateway]:
    return {SmsProviderType.MOCK_TEST: MockGateway(), SmsProviderType.NETGSM: NetgsmGateway()}
