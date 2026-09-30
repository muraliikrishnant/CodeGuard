"""Claude LLM provider implementation."""

from __future__ import annotations

import logging

import anthropic

from codeguard.models import Label, LLMVerdict, TriageContext
from codeguard.triage.prompts import CLASSIFY_TEMPLATE, SYSTEM_PROMPT
from codeguard.triage.schema import parse_llm_response

logger = logging.getLogger(__name__)


class ClaudeProvider:
    """Claude-based LLM triage provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def classify(self, context: TriageContext) -> LLMVerdict:
        """Classify a candidate finding using Claude."""
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

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=0.0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens

        raw = ""
        if response.content:
            block = response.content[0]
            if hasattr(block, "text"):
                raw = block.text
        verdict = parse_llm_response(raw)
        if verdict is None:
            return LLMVerdict(
                label=Label.UNCERTAIN,
                confidence=0.0,
                reasoning="Failed to parse Claude response",
                evidence=[],
            )
        return verdict
