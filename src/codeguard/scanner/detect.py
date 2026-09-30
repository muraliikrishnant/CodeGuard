"""detect-secrets wrapper for working tree and history scanning."""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from pathlib import Path

from codeguard.config import ScanConfig
from codeguard.models import Candidate, SecretType

logger = logging.getLogger(__name__)

SECRET_TYPE_MAP: dict[str, SecretType] = {
    "AWSKeyDetector": SecretType.AWS_ACCESS_KEY,
    "ArtifactoryDetector": SecretType.GENERIC_API_KEY,
    "AzureStorageKeyDetector": SecretType.GENERIC_API_KEY,
    "BasicAuthDetector": SecretType.GENERIC_API_KEY,
    "CloudantDetector": SecretType.GENERIC_API_KEY,
    "DiscordBotTokenDetector": SecretType.GENERIC_API_KEY,
    "GitHubTokenDetector": SecretType.GITHUB_TOKEN,
    "HexHighEntropyString": SecretType.GENERIC_HIGH_ENTROPY,
    "Base64HighEntropyString": SecretType.GENERIC_HIGH_ENTROPY,
    "IbmCloudIamDetector": SecretType.GENERIC_API_KEY,
    "IbmCosHmacDetector": SecretType.GENERIC_API_KEY,
    "JwtTokenDetector": SecretType.GENERIC_API_KEY,
    "KeywordDetector": SecretType.GENERIC_API_KEY,
    "MailchimpDetector": SecretType.GENERIC_API_KEY,
    "NpmDetector": SecretType.GENERIC_API_KEY,
    "PrivateKeyDetector": SecretType.PRIVATE_KEY,
    "SendGridDetector": SecretType.GENERIC_API_KEY,
    "SlackDetector": SecretType.SLACK_TOKEN,
    "SoftlayerDetector": SecretType.GENERIC_API_KEY,
    "SquareOAuthDetector": SecretType.GENERIC_API_KEY,
    "StripeDetector": SecretType.STRIPE_KEY,
    "TwilioKeyDetector": SecretType.GENERIC_API_KEY,
}


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _map_secret_type(detector: str) -> SecretType:
    return SECRET_TYPE_MAP.get(detector, SecretType.OTHER)


def scan_working_tree(repo_path: Path, config: ScanConfig) -> list[Candidate]:
    """Scan the working tree at HEAD using detect-secrets."""
    result = subprocess.run(
        ["detect-secrets", "scan", str(repo_path)],
        capture_output=True,
        text=True,
        timeout=config.timeout_seconds * 10,
        check=False,
    )
    if result.returncode != 0:
        logger.warning("detect-secrets scan failed: %s", result.stderr[:500])
        return []

    return _parse_detect_secrets_output(result.stdout, commit_sha="HEAD")


def _parse_detect_secrets_output(raw_json: str, commit_sha: str) -> list[Candidate]:
    """Parse detect-secrets JSON output into Candidate objects."""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("Failed to parse detect-secrets output")
        return []

    candidates: list[Candidate] = []
    results = data.get("results", {})
    for file_path, secrets in results.items():
        for secret in secrets:
            raw_value = secret.get("secret", "")
            candidates.append(
                Candidate(
                    file_path=file_path,
                    line_number=secret.get("line_number", 0),
                    commit_sha=commit_sha,
                    secret_hash=_hash_secret(raw_value),
                    secret_type=_map_secret_type(secret.get("type", "")),
                    detector_name=secret.get("type", "unknown"),
                    raw_value=raw_value,
                )
            )
    return candidates
