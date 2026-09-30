# ADR 001: Fail-Open Policy

## Decision
When the LLM fails, times out, returns malformed output, or classifies a finding as "uncertain", the finding is kept and flagged as `needs_review`. It is never suppressed.

## Rationale
Recall is sacred. The LLM may only downgrade noise; it must never be the reason a real secret is silently dropped. False negatives in a security scanner are far more dangerous than false positives.

## Consequences
- Higher false-positive rate when LLM is unavailable, but zero risk of missed real leaks due to LLM failure
- Suppressed findings are still written to reports for human audit
