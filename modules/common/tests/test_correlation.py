import pytest

from aih_common import correlation


def test_keeps_well_formed_id() -> None:
    assert correlation.resolve("abc-123_DEF.456") == "abc-123_DEF.456"


@pytest.mark.parametrize(
    "candidate", [None, "", "short", "has space inside", "inject\r\nheader", "<script>alert(1)</script>"]
)
def test_replaces_missing_or_unsafe_id_with_uuid(candidate: str | None) -> None:
    resolved = correlation.resolve(candidate)
    assert resolved != candidate
    assert len(resolved) == 36


def test_rejects_id_longer_than_limit() -> None:
    assert correlation.sanitize("a" * 65) is None
