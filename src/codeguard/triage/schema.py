"""Strict output schema validation for LLM responses."""

from __future__ import annotations

import json

from codeguard.models import Label, LLMVerdict


def parse_llm_response(raw: str) -> LLMVerdict | None:
    """Parse and validate LLM JSON response. Returns None on invalid output."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        return LLMVerdict(
            label=Label(data["label"]),
            confidence=float(data["confidence"]),
            reasoning=str(data["reasoning"]),
            evidence=[str(e) for e in data.get("evidence", [])],
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
