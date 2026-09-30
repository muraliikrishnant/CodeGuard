"""Tests for core data models."""

from codeguard.models import (
    Candidate,
    FinalVerdict,
    Finding,
    Label,
    LLMVerdict,
    SecretType,
    TriageContext,
)


def test_candidate_excludes_raw_value_from_dict() -> None:
    c = Candidate(
        file_path="src/config.py",
        line_number=10,
        commit_sha="abc123",
        secret_hash="deadbeef",
        secret_type=SecretType.AWS_ACCESS_KEY,
        detector_name="AWSKeyDetector",
        raw_value="AKIAIOSFODNN7EXAMPLE",
    )
    d = c.model_dump()
    assert "raw_value" not in d
    assert c.raw_value == "AKIAIOSFODNN7EXAMPLE"


def test_llm_verdict_validation() -> None:
    v = LLMVerdict(
        label=Label.REAL_LEAK,
        confidence=0.95,
        reasoning="Key matches AWS format and is in production config",
        evidence=["file is src/config.py", "not in tests directory"],
    )
    assert v.label == Label.REAL_LEAK
    assert v.confidence == 0.95


def test_finding_with_needs_review() -> None:
    c = Candidate(
        file_path="app.py",
        line_number=5,
        commit_sha="def456",
        secret_hash="cafe",
        secret_type=SecretType.GENERIC_API_KEY,
        detector_name="HighEntropyString",
        raw_value="placeholder",
    )
    ctx = TriageContext(candidate=c, code_window="api_key = 'placeholder'")
    f = Finding(
        candidate=c,
        context=ctx,
        llm_verdict=None,
        final_verdict=FinalVerdict.NEEDS_REVIEW,
    )
    assert f.final_verdict == FinalVerdict.NEEDS_REVIEW
    assert f.llm_verdict is None
