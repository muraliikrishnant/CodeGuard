"""Git history traversal for scanning all commits/branches."""

from __future__ import annotations

import logging
from pathlib import Path

from git import Repo

from codeguard.config import ScanConfig
from codeguard.models import Candidate
from codeguard.scanner.detect import _hash_secret, _map_secret_type

logger = logging.getLogger(__name__)

SKIP_EXTENSIONS = frozenset(
    {
        ".lock",
        ".sum",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".svg",
        ".mp4",
        ".webm",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".min.js",
        ".min.css",
        ".map",
        ".pyc",
        ".class",
        ".o",
        ".so",
        ".dll",
    }
)

SKIP_FILENAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "Pipfile.lock",
        "poetry.lock",
        "composer.lock",
        "Gemfile.lock",
        "go.sum",
        "Cargo.lock",
        "flake.lock",
    }
)


def _should_skip_file(file_path: str) -> bool:
    """Skip lockfiles, binaries, and other non-secret-bearing files."""
    name = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
    if name in SKIP_FILENAMES:
        return True
    return any(file_path.endswith(ext) for ext in SKIP_EXTENSIONS)


def sweep_history(repo_path: Path, config: ScanConfig) -> list[Candidate]:
    """Walk all reachable commits and scan each for secrets using detect-secrets."""
    repo = Repo(str(repo_path))
    if repo.bare:
        logger.warning("Bare repository, skipping history sweep")
        return []

    candidates: list[Candidate] = []
    seen_commits: set[str] = set()

    for branch in repo.references:
        try:
            for commit in repo.iter_commits(branch):
                sha = commit.hexsha
                if sha in seen_commits:
                    continue
                seen_commits.add(sha)
                candidates.extend(_scan_commit(repo, commit, config))
        except Exception:
            logger.debug("Could not iterate branch %s", branch, exc_info=True)

    logger.info("Scanned %d commits, found %d candidates", len(seen_commits), len(candidates))
    return candidates


def _scan_commit(repo: Repo, commit: object, config: ScanConfig) -> list[Candidate]:
    """Scan a single commit's tree for secrets."""
    from git import Commit

    if not isinstance(commit, Commit):
        return []

    candidates: list[Candidate] = []

    for blob in commit.tree.traverse():
        if not hasattr(blob, "data_stream"):
            continue
        try:
            if blob.size > config.max_file_size_kb * 1024:  # type: ignore[union-attr]
                continue
            data = blob.data_stream.read().decode("utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            continue

        file_path = str(blob.path)  # type: ignore[union-attr]
        if _should_skip_file(file_path):
            continue
        for _line_num, line in enumerate(data.splitlines(), 1):
            for finding in _quick_entropy_check(line, file_path, str(commit.hexsha)):
                candidates.append(finding)

    return candidates


def _quick_entropy_check(line: str, file_path: str, commit_sha: str) -> list[Candidate]:
    """Quick high-entropy string detection for history scanning."""
    import re

    candidates: list[Candidate] = []
    pattern = re.compile(r"""(?:['\"=:\s])([A-Za-z0-9+/=_\-]{20,})(?:['\";\s,\n]|$)""")
    for match in pattern.finditer(line):
        value = match.group(1)
        entropy = _shannon_entropy(value)
        if entropy > 4.5 and len(value) >= 20:
            candidates.append(
                Candidate(
                    file_path=file_path,
                    line_number=0,
                    commit_sha=commit_sha,
                    secret_hash=_hash_secret(value),
                    secret_type=_map_secret_type(""),
                    detector_name="HistoryEntropyScanner",
                    raw_value=value,
                )
            )
    return candidates


def _shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    import math

    if not data:
        return 0.0
    freq: dict[str, int] = {}
    for c in data:
        freq[c] = freq.get(c, 0) + 1
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())
