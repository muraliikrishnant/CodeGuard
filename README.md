# CodeGuard

Git-aware secret scanner that pairs regex/entropy detection ([detect-secrets](https://github.com/Yelp/detect-secrets)) with an **LLM triage step** — each candidate finding is sent to the model with surrounding code, file path, and git blame context, and classified as **real leak** vs **test/placeholder/example** with per-finding reasoning.

## Why LLM Triage?

Traditional secret scanners produce many false positives on test fixtures, documentation examples, and placeholder values. CodeGuard's LLM triage step examines the surrounding code context and classifies each finding, reducing false positives while preserving recall on real leaks.

**Key design principle:** The LLM can only *downgrade* noise. If it fails, times out, or is uncertain, findings are **kept** (fail-open toward reporting).

## Features

- **Full git history sweep** — secrets removed in later commits are still found
- **LLM triage** with Gemini or Claude (or run without for baseline mode)
- **Structured verdicts** with confidence scores and evidence-based reasoning
- **Multiple output formats** — JSON, SARIF (GitHub code scanning), Markdown
- **On-disk response cache** for cheap, reproducible reruns
- **Web dashboard** for interactive scanning
- **Docker support** and **GitHub Actions** integration

## Quickstart

### CLI

```bash
# Install
pip install -e ".[dev]"

# Scan a repo (detect-secrets only)
codeguard scan /path/to/repo

# Scan with LLM triage
export GEMINI_API_KEY=your-key
codeguard scan /path/to/repo --provider gemini

# Output SARIF for GitHub
codeguard scan /path/to/repo --format sarif --output results.sarif
```

### Docker

```bash
docker build -t codeguard .
docker run --rm -v "$PWD:/repo" -e GEMINI_API_KEY codeguard scan /repo
```

### Web Dashboard

```bash
# Start the API server
pip install -e ".[frontend]"
uvicorn codeguard.api:app --reload

# Start the frontend (in another terminal)
cd frontend && npm install && npm run dev
```

### GitHub Action

Add to your workflow:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
- run: pip install codeguard
- run: codeguard scan . --format sarif --output results.sarif
- uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
```

## CLI Reference

```
codeguard scan <path> [--history/--no-history] [--provider gemini|claude|none]
                      [--model NAME] [--format json|sarif|md] [--output FILE]
                      [--threshold 0.8] [--fail-on real|needs_review|none]
```

**Exit codes:** `0` clean, `1` findings at/above `--fail-on` level, `2` tool error.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full pipeline diagram and design decisions.

## Benchmark

Benchmarked against GitLeaks and TruffleHog on 22 public repos with planted secrets. See [docs/methodology.md](docs/methodology.md) for the full benchmark protocol.

Results: TBD (run `python benchmarks/evaluate.py` after completing the benchmark corpus)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run checks
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/codeguard/
pytest -m "not live"
```

## License

MIT
