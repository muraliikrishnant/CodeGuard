"""Tests for LLM response schema validation."""

from codeguard.triage.schema import parse_llm_response


def test_parse_valid_response() -> None:
    raw = (
        '{"label": "real_leak", "confidence": 0.95,'
        ' "reasoning": "AWS key in prod config", "evidence": ["prod path"]}'
    )
    result = parse_llm_response(raw)
    assert result is not None
    assert result.label.value == "real_leak"
    assert result.confidence == 0.95


def test_parse_invalid_json() -> None:
    assert parse_llm_response("not json") is None


def test_parse_invalid_label() -> None:
    raw = '{"label": "bogus", "confidence": 0.5, "reasoning": "test"}'
    assert parse_llm_response(raw) is None


def test_parse_code_fenced_response() -> None:
    raw = (
        '```json\n{"label": "test_placeholder", "confidence": 0.9,'
        ' "reasoning": "in tests dir", "evidence": []}\n```'
    )
    result = parse_llm_response(raw)
    assert result is not None
    assert result.label.value == "test_placeholder"
