"""SARIF report output for GitHub code scanning."""

from __future__ import annotations

import json
from pathlib import Path

from codeguard.models import ScanReport


def generate_sarif_report(report: ScanReport, output: Path | None = None) -> str:
    """Generate SARIF 2.1.0 report."""
    results = []
    for finding in report.findings:
        results.append(
            {
                "ruleId": f"codeguard/{finding.candidate.secret_type}",
                "level": "error" if finding.final_verdict == "leak" else "warning",
                "message": {
                    "text": (
                        f"Potential {finding.candidate.secret_type} detected "
                        f"({finding.final_verdict})"
                    ),
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.candidate.file_path},
                            "region": {"startLine": finding.candidate.line_number},
                        }
                    }
                ],
            }
        )

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeGuard",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/muraliikrishnant/CodeGuard",
                    }
                },
                "results": results,
            }
        ],
    }

    text = json.dumps(sarif, indent=2)
    if output:
        output.write_text(text)
    return text
