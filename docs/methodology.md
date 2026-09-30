# Benchmark Methodology

## Corpus
- 22 public repositories selected for language diversity (Python, JS/TS, Go, Java, Ruby, PHP, Rust, C#)
- Pinned at specific commit SHAs in `benchmarks/corpus/repos.yaml`
- Selection criteria: popular open-source projects with realistic codebases containing test fixtures, docs, and config files where false positives commonly occur

## Planted Secrets
- `plant.py` injects synthetic secrets using a fixed seed (42) for reproducibility
- Types: AWS keys, GitHub tokens, Stripe keys, Slack tokens, private keys, DB connection strings, generic API keys
- Locations: source, config, .env, CI files, docs, tests
- Includes decoys: test placeholders, example values, README samples
- Ground-truth manifest generated per repo

## Splits
- `splits.yaml` frozen before any tuning
- Split by repo (not by finding) to avoid leakage
- ~70% dev (15 repos), ~30% held-out (7 repos)
- Stratified by language

## Metrics
- **Match rule**: same file + line (±3 tolerance) + same secret value hash
- **TP**: real planted secret correctly reported
- **FN**: real planted secret missed
- **FP**: reported finding that is a decoy or not a real leak
- **TN**: decoy correctly not reported
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **FPR** = FP / (FP + TN)
- Wilson score confidence intervals reported for all metrics

## Tools Compared
1. GitLeaks (pinned version)
2. TruffleHog (pinned version)
3. detect-secrets alone (no LLM) — isolates LLM contribution
4. CodeGuard (detect-secrets + LLM triage)

## Limitations
- Synthetic planted secrets vs. real-world leaks
- Corpus size (22 repos)
- LLM model nondeterminism (mitigated by temperature=0 and caching)
- TruffleHog verification disabled for planted synthetic secrets
