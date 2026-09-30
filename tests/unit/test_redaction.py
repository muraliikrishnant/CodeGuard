"""Tests for secret redaction."""

from codeguard.context.redact import redact_secret


def test_redact_keeps_prefix() -> None:
    result = redact_secret("AKIAIOSFODNN7EXAMPLE")
    assert result.startswith("AKIA")
    assert "IOSFODNN7EXAMPLE" not in result


def test_redact_short_value() -> None:
    result = redact_secret("abc")
    assert result == "***"


def test_redact_shows_length() -> None:
    result = redact_secret("sk_live_1234567890abcdef")
    assert "len=24" in result
