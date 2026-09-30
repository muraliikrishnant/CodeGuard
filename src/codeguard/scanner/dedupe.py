"""Collapse duplicate candidates across commits."""

from __future__ import annotations

from codeguard.models import Candidate


def dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Dedupe by secret_hash + file_path, keeping first-introduced and last-seen commit."""
    seen: dict[str, Candidate] = {}

    for c in candidates:
        key = f"{c.secret_hash}:{c.file_path}"
        if key not in seen:
            seen[key] = c.model_copy(
                update={"first_commit": c.commit_sha, "last_commit": c.commit_sha}
            )
        else:
            existing = seen[key]
            seen[key] = existing.model_copy(update={"last_commit": c.commit_sha})

    return list(seen.values())
