"""Policy layer: map LLM verdicts to final decisions (fail-open)."""

from __future__ import annotations

from codeguard.models import (
    Candidate,
    FinalVerdict,
    Finding,
    Label,
    LLMVerdict,
    TriageContext,
)


def apply_policy(
    candidate: Candidate,
    context: TriageContext,
    verdict: LLMVerdict | None,
    confidence_threshold: float,
) -> Finding:
    """Apply fail-open policy to an LLM verdict."""
    if verdict is None:
        return Finding(
            candidate=candidate,
            context=context,
            llm_verdict=None,
            final_verdict=FinalVerdict.NEEDS_REVIEW,
            suppression_reason="LLM returned no valid verdict",
        )

    if verdict.label == Label.REAL_LEAK:
        return Finding(
            candidate=candidate,
            context=context,
            llm_verdict=verdict,
            final_verdict=FinalVerdict.LEAK,
        )

    if verdict.label == Label.UNCERTAIN:
        return Finding(
            candidate=candidate,
            context=context,
            llm_verdict=verdict,
            final_verdict=FinalVerdict.NEEDS_REVIEW,
            suppression_reason="LLM classified as uncertain",
        )

    if verdict.confidence >= confidence_threshold:
        return Finding(
            candidate=candidate,
            context=context,
            llm_verdict=verdict,
            final_verdict=FinalVerdict.SUPPRESSED,
            suppression_reason=(
                f"LLM classified as {verdict.label} with confidence {verdict.confidence:.2f}"
            ),
        )

    return Finding(
        candidate=candidate,
        context=context,
        llm_verdict=verdict,
        final_verdict=FinalVerdict.NEEDS_REVIEW,
        suppression_reason=(
            f"LLM classified as {verdict.label} but confidence "
            f"{verdict.confidence:.2f} < threshold {confidence_threshold:.2f}"
        ),
    )
