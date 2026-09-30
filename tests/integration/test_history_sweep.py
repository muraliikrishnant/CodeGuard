"""Integration test: build a tiny git repo with a secret added and later deleted."""

import subprocess
from pathlib import Path

import pytest

from codeguard.config import ScanConfig
from codeguard.scanner.history import _shannon_entropy, sweep_history


def test_shannon_entropy_high_for_random() -> None:
    assert _shannon_entropy("aB3kL9mNpQ2rSt5uVw8xYz") > 4.0


def test_shannon_entropy_low_for_repeated() -> None:
    assert _shannon_entropy("aaaaaaaaaa") < 1.0


@pytest.fixture()
def temp_git_repo(tmp_path: Path) -> Path:
    """Create a temp git repo with a secret added then deleted."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    def run(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            env={
                "GIT_AUTHOR_NAME": "Test",
                "GIT_AUTHOR_EMAIL": "test@test.com",
                "GIT_COMMITTER_NAME": "Test",
                "GIT_COMMITTER_EMAIL": "test@test.com",
                "HOME": str(tmp_path),
                "PATH": "/usr/bin:/usr/local/bin:/opt/homebrew/bin",
            },
        )

    run("init", "-b", "main")
    run("config", "user.email", "test@test.com")
    run("config", "user.name", "Test")

    config_file = repo / "config.py"
    config_file.write_text('AWS_SECRET = "wJalrXUtnFEMI0K7MDENG0bPxRfiCYEXAMPLEKEY"\n')
    run("add", ".")
    run("commit", "-m", "add secret")

    config_file.write_text('AWS_SECRET = ""\n')
    run("add", ".")
    run("commit", "-m", "remove secret")

    return repo


def test_history_sweep_finds_deleted_secret(temp_git_repo: Path) -> None:
    config = ScanConfig(history=True, max_file_size_kb=100)
    candidates = sweep_history(temp_git_repo, config)
    secret_found = any("wJalrXUtnFEMI" in c.raw_value for c in candidates)
    assert secret_found, "History sweep should find the deleted secret"
