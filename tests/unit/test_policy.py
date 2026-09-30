"""Tests for the policy layer — fail-open behavior is mandatory."""

from codeguard.models import (
    Candidate,
    FinalVerdict,
    Label,
    LLMVerdict,
    SecretType,
    TriageContext,
)
from codeguard.triage.policy import apply_policy


def _make_candidate() -> Candidate:
    return Candidate(
        file_path="src/app.py",
        line_number=10,
        commit_sha="abc123",
        secret_hash="deadbeef",
        secret_type=SecretType.AWS_ACCESS_KEY,
        detector_name="AWSKeyDetector",
        raw_value="AKIAIOSFODNN7EXAMPLE",
    )


def _make_context(candidate: Candidate) -> TriageContext:
    return TriageContext(candidate=candidate, code_window="api_key = '...'")


def test_none_verdict_yields_needs_review() -> None:
    c = _make_candidate()
    f = apply_policy(c, _make_context(c), None, 0.8)
    assert f.final_verdict == FinalVerdict.NEEDS_REVIEW


def test_real_leak_yields_leak() -> None:
    c = _make_candidate()
    v = LLMVerdict(label=Label.REAL_LEAK, confidence=0.95, reasoning="real", evidence=[])
    f = apply_policy(c, _make_context(c), v, 0.8)
    assert f.final_verdict == FinalVerdict.LEAK


def test_uncertain_yields_needs_review() -> None:
    c = _make_candidate()
    v = LLMVerdict(label=Label.UNCERTAIN, confidence=0.5, reasoning="unclear", evidence=[])
    f = apply_policy(c, _make_context(c), v, 0.8)
    assert f.final_verdict == FinalVerdict.NEEDS_REVIEW


def test_test_placeholder_high_confidence_suppressed() -> None:
    c = _make_candidate()
    v = LLMVerdict(label=Label.TEST_PLACEHOLDER, confidence=0.95, reasoning="test", evidence=[])
    f = apply_policy(c, _make_context(c), v, 0.8)
    assert f.final_verdict == FinalVerdict.SUPPRESSED


def test_test_placeholder_low_confidence_needs_review() -> None:
    c = _make_candidate()
    v = LLMVerdict(
        label=Label.TEST_PLACEHOLDER, confidence=0.6, reasoning="maybe test", evidence=[]
    )
    f = apply_policy(c, _make_context(c), v, 0.8)
    assert f.final_verdict == FinalVerdict.NEEDS_REVIEW


def test_example_doc_high_confidence_suppressed() -> None:
    c = _make_candidate()
    v = LLMVerdict(label=Label.EXAMPLE_DOC, confidence=0.9, reasoning="doc example", evidence=[])
    f = apply_policy(c, _make_context(c), v, 0.8)
    assert f.final_verdict == FinalVerdict.SUPPRESSED
