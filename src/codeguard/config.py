"""Settings, env loading, defaults."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel


class ScanConfig(BaseModel):
    """Configuration for a CodeGuard scan."""

    history: bool = True
    provider: str = "none"
    model: str = ""
    output_format: str = "json"
    output_file: Path | None = None
    confidence_threshold: float = 0.8
    fail_on: str = "real"
    context_lines: int = 15
    max_file_size_kb: int = 1024
    concurrency: int = 5
    timeout_seconds: int = 30
    cache_dir: Path = Path(".codeguard-cache")
    debug: bool = False

    @property
    def gemini_api_key(self) -> str | None:
        return os.environ.get("GEMINI_API_KEY")

    @property
    def anthropic_api_key(self) -> str | None:
        return os.environ.get("ANTHROPIC_API_KEY")


DEFAULT_CONFIG = ScanConfig()
