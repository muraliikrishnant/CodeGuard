"""Surrounding code, path, blame, commit metadata context builder."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from codeguard.config import ScanConfig
from codeguard.context.redact import redact_secret
from codeguard.models import Candidate, TriageContext

logger = logging.getLogger(__name__)

TEST_PATH_PATTERNS = re.compile(r"(^|/)tests?/|_test\.\w+$|\.test\.\w+$|/fixtures?/|/mocks?/")
DOCS_PATH_PATTERNS = re.compile(r"(^|/)docs?/|README|\.md$|\.rst$|\.txt$")
EXAMPLE_PATH_PATTERNS = re.compile(r"(^|/)examples?/|/samples?/|/demo/|\.example")


def build_context(
    candidate: Candidate,
    repo_path: Path,
    config: ScanConfig,
) -> TriageContext:
    """Build triage context for a candidate finding."""
    code_window = _get_code_window(
        repo_path / candidate.file_path,
        candidate.line_number,
        config.context_lines,
    )

    blame_author, blame_date, blame_message = _get_blame_info(
        repo_path, candidate.file_path, candidate.line_number
    )

    file_path = candidate.file_path
    return TriageContext(
        candidate=candidate,
        code_window=code_window,
        blame_author=blame_author,
        blame_date=blame_date,
        blame_commit_message=blame_message,
        is_test_path=bool(TEST_PATH_PATTERNS.search(file_path)),
        is_docs_path=bool(DOCS_PATH_PATTERNS.search(file_path)),
        is_example_path=bool(EXAMPLE_PATH_PATTERNS.search(file_path)),
        neighboring_identifiers=_extract_identifiers(code_window),
        redacted_value=redact_secret(candidate.raw_value),
    )


def _get_code_window(file_path: Path, line_number: int, context_lines: int) -> str:
    """Extract surrounding lines of code."""
    try:
        lines = file_path.read_text(errors="replace").splitlines()
    except (OSError, UnicodeDecodeError):
        return ""

    start = max(0, line_number - context_lines - 1)
    end = min(len(lines), line_number + context_lines)
    window_lines = []
    for i, line in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if i == line_number else "   "
        window_lines.append(f"{marker} {i:4d} | {line}")
    return "\n".join(window_lines)


def _get_blame_info(repo_path: Path, file_path: str, line_number: int) -> tuple[str, str, str]:
    """Get git blame info for a specific line."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_path),
                "blame",
                "-L",
                f"{line_number},{line_number}",
                "--porcelain",
                "--",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return "", "", ""

        author = ""
        date = ""
        message = ""
        for line in result.stdout.splitlines():
            if line.startswith("author "):
                author = line[7:]
            elif line.startswith("author-time "):
                date = line[12:]
            elif line.startswith("summary "):
                message = line[8:]
        return author, date, message
    except Exception:
        return "", "", ""


def _extract_identifiers(code_window: str) -> list[str]:
    """Extract variable/function names near the finding."""
    identifiers = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]{2,})\b", code_window)
    unique = list(dict.fromkeys(identifiers))
    return unique[:20]
