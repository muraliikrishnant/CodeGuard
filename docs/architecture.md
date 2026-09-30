# CodeGuard Architecture

## Pipeline

```
git repo ──► scanner (detect-secrets + history sweep)
          ──► dedupe candidates
          ──► context builder (code window, path, git blame, commit info)
          ──► redaction (mask secret before LLM)
          ──► LLM triage (structured verdict + reasoning)
          ──► policy layer (fail-open rules, thresholds)
          ──► report (JSON / SARIF / Markdown)
```

## Components

### Scanner (`src/codeguard/scanner/`)
- **detect.py**: Wraps `detect-secrets` for working-tree scanning
- **history.py**: Git history traversal using GitPython, scans all reachable commits
- **dedupe.py**: Collapses duplicate candidates by secret hash + file path

### Context Builder (`src/codeguard/context/`)
- **builder.py**: Assembles surrounding code, git blame, path heuristics
- **redact.py**: Masks secret values before LLM calls (keeps prefix + length shape)

### LLM Triage (`src/codeguard/triage/`)
- **base.py**: `LLMProvider` protocol
- **gemini.py / claude.py**: Provider implementations
- **prompts.py**: Versioned prompt templates with injection defense
- **schema.py**: Strict JSON output validation
- **policy.py**: Fail-open policy (uncertain/errors → needs_review, never suppressed)
- **cache.py**: On-disk response cache keyed by prompt version + model + context hash

### Reports (`src/codeguard/report/`)
- JSON, SARIF (GitHub code scanning), and Markdown output formats

### API (`src/codeguard/api.py`)
- FastAPI backend serving the frontend dashboard

## Design Decisions
- **Fail-open**: LLM errors never suppress findings (§2.1 of CLAUDE.md)
- **Redaction before LLM**: Secret values masked to prefix + shape
- **Provider abstraction**: Gemini and Claude behind one protocol
- **Deterministic output**: Reports sorted by path, line, commit
