"""Tests for candidate deduplication."""

from codeguard.models import Candidate, SecretType
from codeguard.scanner.dedupe import dedupe_candidates


def test_dedupe_identical_secrets() -> None:
    c1 = Candidate(
        file_path="config.py",
        line_number=10,
        commit_sha="aaa",
        secret_hash="hash1",
        secret_type=SecretType.AWS_ACCESS_KEY,
        detector_name="AWSKeyDetector",
        raw_value="secret",
    )
    c2 = Candidate(
        file_path="config.py",
        line_number=10,
        commit_sha="bbb",
        secret_hash="hash1",
        secret_type=SecretType.AWS_ACCESS_KEY,
        detector_name="AWSKeyDetector",
        raw_value="secret",
    )
    result = dedupe_candidates([c1, c2])
    assert len(result) == 1
    assert result[0].first_commit == "aaa"
    assert result[0].last_commit == "bbb"


def test_dedupe_different_files() -> None:
    c1 = Candidate(
        file_path="a.py",
        line_number=1,
        commit_sha="aaa",
        secret_hash="hash1",
        secret_type=SecretType.OTHER,
        detector_name="test",
        raw_value="s",
    )
    c2 = Candidate(
        file_path="b.py",
        line_number=1,
        commit_sha="aaa",
        secret_hash="hash1",
        secret_type=SecretType.OTHER,
        detector_name="test",
        raw_value="s",
    )
    result = dedupe_candidates([c1, c2])
    assert len(result) == 2
