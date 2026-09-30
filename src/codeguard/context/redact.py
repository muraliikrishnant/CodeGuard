"""Mask secret values before LLM calls."""

from __future__ import annotations


def redact_secret(value: str, keep_prefix: int = 4) -> str:
    """Mask a secret value, keeping the first few chars and showing length/charset shape."""
    if len(value) <= keep_prefix:
        return "*" * len(value)
    prefix = value[:keep_prefix]
    masked_len = len(value) - keep_prefix
    return f"{prefix}{'*' * masked_len} (len={len(value)})"
