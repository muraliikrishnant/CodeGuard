"""On-disk response cache for LLM triage calls."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from codeguard.models import LLMVerdict, TriageContext
from codeguard.triage.prompts import PROMPT_VERSION

logger = logging.getLogger(__name__)


class TriageCache:
    """Disk-backed cache keyed by hash(prompt_version + model + redacted_context)."""

    def __init__(self, cache_dir: Path, model: str) -> None:
        self.cache_dir = cache_dir
        self.model = model
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, context: TriageContext) -> str:
        content = f"{PROMPT_VERSION}:{self.model}:{context.redacted_value}:{context.code_window}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, context: TriageContext) -> LLMVerdict | None:
        """Retrieve cached verdict if available."""
        key = self._cache_key(context)
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return LLMVerdict.model_validate(data)
        except Exception:
            logger.debug("Cache miss (corrupt): %s", key)
            return None

    def put(self, context: TriageContext, verdict: LLMVerdict) -> None:
        """Store verdict in cache."""
        key = self._cache_key(context)
        path = self._cache_path(key)
        path.write_text(verdict.model_dump_json(indent=2))
