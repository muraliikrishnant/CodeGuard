"""LLMProvider protocol definition."""

from __future__ import annotations

from typing import Protocol

from codeguard.models import LLMVerdict, TriageContext


class LLMProvider(Protocol):
    """Protocol for LLM triage providers."""

    async def classify(self, context: TriageContext) -> LLMVerdict: ...
