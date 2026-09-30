"""Gemini LLM provider implementation."""

from __future__ import annotations

import logging
from typing import Any

import google.generativeai as genai

from codeguard.models import Label, LLMVerdict, TriageContext
from codeguard.triage.prompts import CLASSIFY_TEMPLATE, SYSTEM_PROMPT
from codeguard.triage.schema import parse_llm_response

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Gemini-based LLM triage provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self.model: Any = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=model,
            system_instruction=SYSTEM_PROMPT,
            generation_config={"temperature": 0.0},
        )
        self.model_name = model
        self.total_tokens = 0

    async def classify(self, context: TriageContext) -> LLMVerdict:
        """Classify a candidate finding using Gemini."""
        prompt = CLASSIFY_TEMPLATE.format(
            file_path=context.candidate.file_path,
            line_number=context.candidate.line_number,
            secret_type=context.candidate.secret_type,
            redacted_value=context.redacted_value,
            is_test_path=context.is_test_path,
            is_docs_path=context.is_docs_path,
            is_example_path=context.is_example_path,
            blame_author=context.blame_author,
            blame_date=context.blame_date,
            blame_commit_message=context.blame_commit_message,
            code_window=context.code_window,
        )

        response = self.model.generate_content(prompt)
        if response.usage_metadata:
            self.total_tokens += response.usage_metadata.total_token_count or 0

        raw: str = response.text or ""
        verdict = parse_llm_response(raw)
        if verdict is None:
            return LLMVerdict(
                label=Label.UNCERTAIN,
                confidence=0.0,
                reasoning="Failed to parse Gemini response",
                evidence=[],
            )
        return verdict
