"""Telefon normalizasyonu, maskeleme ve SMS parça (kontör) hesabı.

BuildingFlow (`SmsText`) ve TraceFlow (`PhoneNumbers`, `SmsSegments`) ile aynı kurallar: yalnız TR cep numarası,
E.164 (+905321234567) biçiminde tutulur; GSM 03.38 dışı tek karakter mesajı Unicode'a (70/67) geçirir.
"""

from __future__ import annotations

import hashlib
import re

_NON_DIGIT = re.compile(r"\D")
_TR_MOBILE = re.compile(r"^5\d{9}$")
_HEADER = re.compile(r"^[A-Za-z0-9 .-]{3,11}$")

GSM_BASIC = frozenset(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM_EXTENDED = frozenset("^{}\\[~]|€")
GSM_SINGLE, GSM_PART = 160, 153
UNICODE_SINGLE, UNICODE_PART = 70, 67
MAX_SEGMENTS = 10
MASK_VISIBLE_PREFIX = 6
MASK_VISIBLE_SUFFIX = 2
NATIONAL_WITH_TRUNK = 11
NATIONAL_WITH_COUNTRY = 12


def normalize_tr_mobile(raw: str) -> str | None:
    """0532.., 532.., +90532.., 0090532.. → +905321234567; geçersizse None."""
    digits = _NON_DIGIT.sub("", raw or "")
    if digits.startswith("0090"):
        digits = digits[4:]
    elif digits.startswith("90") and len(digits) == NATIONAL_WITH_COUNTRY:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == NATIONAL_WITH_TRUNK:
        digits = digits[1:]
    return f"+90{digits}" if _TR_MOBILE.match(digits) else None


def mask_phone(e164: str) -> str:
    """+905321234567 → +90532*****67. Liste, log ve audit'te tam numara görünmez."""
    if len(e164) <= MASK_VISIBLE_PREFIX + MASK_VISIBLE_SUFFIX:
        return "***"
    hidden = len(e164) - MASK_VISIBLE_PREFIX - MASK_VISIBLE_SUFFIX
    return e164[:MASK_VISIBLE_PREFIX] + "*" * hidden + e164[-MASK_VISIBLE_SUFFIX:]


def phone_fingerprint(e164: str, tenant_salt: str) -> str:
    """Numaranın kendisini saklamadan aramaya izin veren tenant tuzlu özet."""
    return hashlib.sha256(f"{tenant_salt}:{e164}".encode()).hexdigest()


def segments(text: str) -> int:
    septets = 0
    for ch in text:
        if ch in GSM_BASIC:
            septets += 1
        elif ch in GSM_EXTENDED:
            septets += 2
        else:
            return _parts(len(text), UNICODE_SINGLE, UNICODE_PART)
    return _parts(septets, GSM_SINGLE, GSM_PART)


def _parts(length: int, single: int, part: int) -> int:
    return 1 if length <= single else -(-length // part)


def is_valid_sender_header(value: str) -> bool:
    return bool(_HEADER.match(value))
