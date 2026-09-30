"""Core data models passed between pipeline stages."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SecretType(StrEnum):
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    STRIPE_KEY = "stripe_key"
    SLACK_TOKEN = "slack_token"
    PRIVATE_KEY = "private_key"
    DB_CONNECTION_STRING = "db_connection_string"
    GENERIC_API_KEY = "generic_api_key"
    GENERIC_HIGH_ENTROPY = "generic_high_entropy"
    OTHER = "other"


class Label(StrEnum):
    REAL_LEAK = "real_leak"
    TEST_PLACEHOLDER = "test_placeholder"
    EXAMPLE_DOC = "example_doc"
    UNCERTAIN = "uncertain"


class FinalVerdict(StrEnum):
    LEAK = "leak"
    SUPPRESSED = "suppressed"
    NEEDS_REVIEW = "needs_review"


class Candidate(BaseModel):
    """A potential secret found by the scanner."""

    file_path: str
    line_number: int
    commit_sha: str
    secret_hash: str
    secret_type: SecretType
    detector_name: str
    raw_value: str = Field(exclude=True, repr=False)
    first_commit: str = ""
    last_commit: str = ""


class TriageContext(BaseModel):
    """Context assembled for LLM triage of a candidate."""

    candidate: Candidate
    code_window: str
    blame_author: str = ""
    blame_date: str = ""
    blame_commit_message: str = ""
    is_test_path: bool = False
    is_docs_path: bool = False
    is_example_path: bool = False
    neighboring_identifiers: list[str] = Field(default_factory=list)
    redacted_value: str = ""


class LLMVerdict(BaseModel):
    """Structured output from the LLM triage step."""

    label: Label
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    evidence: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    """A fully triaged finding with final verdict."""

    candidate: Candidate
    context: TriageContext
    llm_verdict: LLMVerdict | None = None
    final_verdict: FinalVerdict
    suppression_reason: str = ""


class ScanReport(BaseModel):
    """Complete scan report."""

    repo_path: str
    scan_id: str
    timestamp: str
    provider: str = "none"
    model: str = ""
    prompt_version: str = ""
    findings: list[Finding] = Field(default_factory=list)
    suppressed: list[Finding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    token_usage: dict[str, Any] = Field(default_factory=dict)
    stats: dict[str, int] = Field(default_factory=dict)
