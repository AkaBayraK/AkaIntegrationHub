from aih_common.logging import MASK, redact_sensitive


def test_masks_sensitive_keys_including_nested() -> None:
    event = {
        "event": "smtp_saved",
        "password": "hunter2",
        "account": {"username": "ops", "secret_value": "s3cr3t", "headers": {"Authorization": "Bearer x"}},
        "items": [{"api_key": "k"}],
    }
    out = redact_sensitive(None, "info", event)
    assert out["password"] == MASK
    assert out["account"]["username"] == "ops"
    assert out["account"]["secret_value"] == MASK
    assert out["account"]["headers"]["Authorization"] == MASK
    assert out["items"][0]["api_key"] == MASK
    assert out["event"] == "smtp_saved"
