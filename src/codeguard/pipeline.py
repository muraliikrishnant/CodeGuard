"""Main scan pipeline orchestrator."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from codeguard.config import ScanConfig
from codeguard.context.builder import build_context
from codeguard.models import FinalVerdict, Finding, ScanReport
from codeguard.scanner.dedupe import dedupe_candidates
from codeguard.scanner.detect import scan_working_tree
from codeguard.scanner.history import sweep_history
from codeguard.triage.cache import TriageCache
from codeguard.triage.policy import apply_policy

logger = logging.getLogger(__name__)


def _get_provider(config: ScanConfig) -> object | None:
    if config.provider == "gemini":
        key = config.gemini_api_key
        if not key:
            logger.error("GEMINI_API_KEY not set")
            return None
        from codeguard.triage.gemini import GeminiProvider

        return GeminiProvider(api_key=key, model=config.model or "gemini-2.0-flash")
    elif config.provider == "claude":
        key = config.anthropic_api_key
        if not key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None
        from codeguard.triage.claude import ClaudeProvider

        return ClaudeProvider(api_key=key, model=config.model or "claude-sonnet-4-20250514")
    elif config.provider == "nvidia":
        key = config.nvidia_api_key
        if not key:
            logger.error("NVIDIA_API_KEY not set")
            return None
        from codeguard.triage.nvidia import NvidiaProvider

        return NvidiaProvider(api_key=key, model=config.model or "meta/llama-3.1-70b-instruct")
    return None


def run_scan(repo_path: Path, config: ScanConfig) -> ScanReport:
    """Execute the full scan pipeline."""
    scan_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(UTC).isoformat()

    candidates = scan_working_tree(repo_path, config)
    logger.info("Working tree scan: %d candidates", len(candidates))

    if config.history:
        history_candidates = sweep_history(repo_path, config)
        logger.info("History sweep: %d candidates", len(history_candidates))
        candidates.extend(history_candidates)

    candidates = dedupe_candidates(candidates)
    logger.info("After dedupe: %d candidates", len(candidates))

    provider = _get_provider(config)
    cache = TriageCache(config.cache_dir, config.model) if provider else None

    findings: list[Finding] = []
    suppressed: list[Finding] = []
    errors: list[str] = []

    for candidate in candidates:
        context = build_context(candidate, repo_path, config)

        verdict = None
        if provider and cache:
            verdict = cache.get(context)
            if verdict is None:
                try:
                    verdict = asyncio.run(provider.classify(context))  # type: ignore[attr-defined]
                    cache.put(context, verdict)
                except Exception as e:
                    msg = f"LLM error for {candidate.file_path}:{candidate.line_number}: {e}"
                    errors.append(msg)

        if provider:
            finding = apply_policy(candidate, context, verdict, config.confidence_threshold)
        else:
            finding = Finding(
                candidate=candidate,
                context=context,
                llm_verdict=None,
                final_verdict=FinalVerdict.NEEDS_REVIEW,
                suppression_reason="No LLM provider configured",
            )

        if finding.final_verdict == FinalVerdict.SUPPRESSED:
            suppressed.append(finding)
        else:
            findings.append(finding)

    findings.sort(key=lambda f: (f.candidate.file_path, f.candidate.line_number))
    suppressed.sort(key=lambda f: (f.candidate.file_path, f.candidate.line_number))

    return ScanReport(
        repo_path=str(repo_path),
        scan_id=scan_id,
        timestamp=timestamp,
        provider=config.provider,
        model=config.model,
        prompt_version="v1",
        findings=findings,
        suppressed=suppressed,
        errors=errors,
        stats={
            "total_candidates": len(candidates),
            "reported": len(findings),
            "suppressed": len(suppressed),
            "errors": len(errors),
        },
    )
