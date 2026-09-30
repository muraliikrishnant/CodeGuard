"""JSON report output."""

from __future__ import annotations

import json
from pathlib import Path

from codeguard.models import ScanReport


def generate_json_report(report: ScanReport, output: Path | None = None) -> str:
    """Generate JSON report, optionally writing to file."""
    data = report.model_dump(mode="json")
    text = json.dumps(data, indent=2, default=str)
    if output:
        output.write_text(text)
    return text
