"""Markdown report output."""

from __future__ import annotations

from pathlib import Path

from codeguard.models import ScanReport


def generate_markdown_report(report: ScanReport, output: Path | None = None) -> str:
    """Generate a Markdown summary report."""
    lines = [
        "# CodeGuard Scan Report",
        "",
        f"**Repository:** {report.repo_path}",
        f"**Scan ID:** {report.scan_id}",
        f"**Timestamp:** {report.timestamp}",
        f"**Provider:** {report.provider} ({report.model})",
        "",
        "## Summary",
        "",
        f"- **Findings (reported):** {len(report.findings)}",
        f"- **Suppressed:** {len(report.suppressed)}",
        f"- **Errors:** {len(report.errors)}",
        "",
    ]

    if report.findings:
        lines.extend(
            [
                "## Findings",
                "",
                "| File | Line | Type | Verdict | Confidence |",
                "|------|------|------|---------|------------|",
            ]
        )
        for f in report.findings:
            confidence = f"{f.llm_verdict.confidence:.0%}" if f.llm_verdict else "N/A"
            lines.append(
                f"| {f.candidate.file_path} | {f.candidate.line_number} "
                f"| {f.candidate.secret_type} | {f.final_verdict} | {confidence} |"
            )
        lines.append("")

    if report.suppressed:
        lines.extend(
            [
                "## Suppressed (LLM-triaged as non-secrets)",
                "",
                "| File | Line | Type | Reason |",
                "|------|------|------|--------|",
            ]
        )
        for f in report.suppressed:
            lines.append(
                f"| {f.candidate.file_path} | {f.candidate.line_number} "
                f"| {f.candidate.secret_type} | {f.suppression_reason} |"
            )
        lines.append("")

    text = "\n".join(lines)
    if output:
        output.write_text(text)
    return text
