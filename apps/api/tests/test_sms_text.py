from __future__ import annotations

import pytest

from aih_api.providers.sms.gateways import GatewayRequest, NetgsmGateway
from aih_api.providers.sms.text import is_valid_sender_header, mask_phone, normalize_tr_mobile, segments


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0532 123 45 67", "+905321234567"),
        ("5321234567", "+905321234567"),
        ("+90 (532) 123-4567", "+905321234567"),
        ("00905321234567", "+905321234567"),
        ("02121234567", None),
        ("532123456", None),
        ("", None),
    ],
)
def test_normalize_tr_mobile(raw: str, expected: str | None) -> None:
    assert normalize_tr_mobile(raw) == expected


def test_mask_phone_hides_the_middle() -> None:
    assert mask_phone("+905321234567") == "+90532*****67"
    assert mask_phone("123") == "***"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a" * 160, 1),
        ("a" * 161, 2),
        ("{" * 80, 1),
        ("{" * 81, 2),
        ("ş" * 70, 1),
        ("ş" + "a" * 70, 2),
        ("Dogrulama kodunuz: 123456", 1),
    ],
)
def test_segments_follow_gsm_and_unicode_limits(text: str, expected: int) -> None:
    assert segments(text) == expected


@pytest.mark.parametrize(
    ("header", "valid"), [("BLDFLOW", True), ("Aka-Hub.1", True), ("AB", False), ("X" * 12, False)]
)
def test_sender_header(header: str, valid: bool) -> None:
    assert is_valid_sender_header(header) is valid


def test_netgsm_payload_escapes_values_and_keeps_text_in_cdata() -> None:
    request = GatewayRequest("+905321234567", "a]]>b <x>", "AKA&HUB", "user<1>", None)

    payload = NetgsmGateway.payload(request)

    assert "<no>5321234567</no>" in payload
    assert "<msgheader>AKA&amp;HUB</msgheader>" in payload
    assert "<usercode>user&lt;1&gt;</usercode>" in payload
    assert "<![CDATA[a]]]]><![CDATA[>b <x>]]>" in payload
    assert "5321234567" not in repr(request)
    assert "<x>" not in repr(request)


@pytest.mark.parametrize(
    ("status", "text", "outcome", "error"),
    [
        (200, "00 123456789", "sent", None),
        (200, "30", "failed", "SMS_AUTH_FAILED"),
        (200, "40", "failed", "SMS_SENDER_REJECTED"),
        (200, "99", "unknown", "SMS_PROVIDER_RESPONSE_UNKNOWN"),
        (200, "00 abc", "unknown", "SMS_PROVIDER_RESPONSE_UNKNOWN"),
        (503, "", "unknown", "SMS_PROVIDER_UNAVAILABLE"),
    ],
)
def test_netgsm_response_mapping(status: int, text: str, outcome: str, error: str | None) -> None:
    result = NetgsmGateway.parse(status, text)

    assert (result.outcome, result.error_code) == (outcome, error)
