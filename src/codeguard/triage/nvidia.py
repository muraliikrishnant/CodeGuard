"""NVIDIA build.nvidia.com LLM provider (OpenAI-compatible API)."""

from __future__ import annotations

import logging

from openai import OpenAI

from codeguard.models import Label, LLMVerdict, TriageContext
from codeguard.triage.prompts import CLASSIFY_TEMPLATE, SYSTEM_PROMPT
from codeguard.triage.schema import parse_llm_response

logger = logging.getLogger(__name__)


class NvidiaProvider:
    """NVIDIA build.nvidia.com triage provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "meta/llama-3.2-11b-vision-instruct",
    ) -> None:
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model_name = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def classify(self, context: TriageContext) -> LLMVerdict:
        """Classify a candidate finding using NVIDIA-hosted model."""
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

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )

        if response.usage:
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

        raw = ""
        if response.choices and response.choices[0].message.content:
            raw = response.choices[0].message.content

        verdict = parse_llm_response(raw)
        if verdict is None:
            return LLMVerdict(
                label=Label.UNCERTAIN,
                confidence=0.0,
                reasoning="Failed to parse NVIDIA response",
                evidence=[],
            )
        return verdict
