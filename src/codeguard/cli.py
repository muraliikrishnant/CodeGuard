"""CLI entrypoint."""

from __future__ import annotations

import logging
from pathlib import Path

import typer
from rich.console import Console

from codeguard.config import ScanConfig
from codeguard.pipeline import run_scan
from codeguard.report.json_report import generate_json_report
from codeguard.report.markdown import generate_markdown_report
from codeguard.report.sarif import generate_sarif_report

app = typer.Typer(name="codeguard", help="Git-aware secret scanner with LLM triage.")
console = Console()

_PATH_ARG = typer.Argument(..., help="Path to git repository to scan")
_HISTORY_OPT = typer.Option(True, help="Sweep full git history")
_PROVIDER_OPT = typer.Option("nvidia", help="LLM provider: nvidia, gemini, claude, or none")
_MODEL_OPT = typer.Option("", help="Model name override")
_FORMAT_OPT = typer.Option("json", "--format", help="Output format: json, sarif, md")
_OUTPUT_OPT = typer.Option(None, "--output", "-o", help="Output file path")
_THRESHOLD_OPT = typer.Option(0.8, help="Confidence threshold for suppression")
_FAIL_ON_OPT = typer.Option("real", help="Exit 1 on: real, needs_review, none")
_DEBUG_OPT = typer.Option(False, help="Enable debug logging")


@app.command()
def scan(
    path: Path = _PATH_ARG,
    history: bool = _HISTORY_OPT,
    provider: str = _PROVIDER_OPT,
    model: str = _MODEL_OPT,
    format: str = _FORMAT_OPT,
    output: Path | None = _OUTPUT_OPT,
    threshold: float = _THRESHOLD_OPT,
    fail_on: str = _FAIL_ON_OPT,
    debug: bool = _DEBUG_OPT,
) -> None:
    """Scan a repository for secrets."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = ScanConfig(
        history=history,
        provider=provider,
        model=model,
        output_format=format,
        output_file=output,
        confidence_threshold=threshold,
        fail_on=fail_on,
        debug=debug,
    )

    console.print(f"[bold]CodeGuard[/bold] scanning {path}", style="blue")
    report = run_scan(path.resolve(), config)

    if format == "sarif":
        text = generate_sarif_report(report, output)
    elif format == "md":
        text = generate_markdown_report(report, output)
    else:
        text = generate_json_report(report, output)

    if not output:
        console.print(text)

    console.print(
        f"\n[bold]Results:[/bold] {report.stats.get('reported', 0)} findings, "
        f"{report.stats.get('suppressed', 0)} suppressed, "
        f"{report.stats.get('errors', 0)} errors",
    )

    if fail_on == "none":
        raise typer.Exit(0)

    has_leaks = any(f.final_verdict == "leak" for f in report.findings)
    has_reviews = any(f.final_verdict == "needs_review" for f in report.findings)

    if fail_on == "real" and has_leaks:
        raise typer.Exit(1)
    if fail_on == "needs_review" and (has_leaks or has_reviews):
        raise typer.Exit(1)

    raise typer.Exit(0)


if __name__ == "__main__":
    app()
