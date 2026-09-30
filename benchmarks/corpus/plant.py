"""Planted-secret injection for benchmark repos."""

from __future__ import annotations

import json
import random
import string
from pathlib import Path

SEED = 42

SECRET_TEMPLATES = {
    "aws_access_key": "AKIA{suffix}",
    "aws_secret_key": "{random_40}",
    "github_token": "ghp_{random_36}",
    "stripe_secret": "sk_live_{random_24}",
    "stripe_publishable": "pk_live_{random_24}",
    "slack_token": "xoxb-{random_12}-{random_12}-{random_24}",
    "generic_api_key": "{random_32}",
    "private_key_header": "-----BEGIN RSA PRIVATE KEY-----",
    "db_connection": "postgresql://user:{random_16}@db.example.com:5432/prod",
}

DECOY_TEMPLATES = {
    "test_aws_key": "AKIAIOSFODNN7EXAMPLE",
    "test_placeholder": "your-api-key-here",
    "example_token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "changeme": "changeme",
    "test_stripe": "sk_test_xxxxxxxxxxxxxxxxxxxx",
    "readme_example": "sk_live_EXAMPLE_DO_NOT_USE",
}

LOCATIONS = [
    "src/config.py",
    "src/settings.js",
    ".env.example",
    "deploy/docker-compose.yml",
    "ci/.github/workflows/deploy.yml",
    "docs/setup.md",
    "tests/test_auth.py",
    "README.md",
    "src/utils/database.ts",
    "config/production.json",
]


def _random_string(length: int, rng: random.Random) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(rng.choice(chars) for _ in range(length))


def generate_planted_secrets(
    output_dir: Path,
    num_real: int = 30,
    num_decoys: int = 20,
) -> dict[str, list[dict[str, str | int | bool]]]:
    """Generate planted secrets and ground-truth manifest."""
    rng = random.Random(SEED)
    manifest: dict[str, list[dict[str, str | int | bool]]] = {"items": []}

    for i in range(num_real):
        template_name = rng.choice(list(SECRET_TEMPLATES.keys()))
        template = SECRET_TEMPLATES[template_name]
        value = template.format(
            suffix=_random_string(16, rng),
            random_40=_random_string(40, rng),
            random_36=_random_string(36, rng),
            random_24=_random_string(24, rng),
            random_16=_random_string(16, rng),
            random_12=_random_string(12, rng),
            random_32=_random_string(32, rng),
        )
        location = rng.choice(LOCATIONS[:6])
        manifest["items"].append({
            "id": f"real_{i}",
            "type": template_name,
            "file": location,
            "line": rng.randint(5, 50),
            "value_hash": f"sha256:{hash(value) & 0xFFFFFFFF:08x}",
            "label": "real",
            "planted": True,
        })

    for i in range(num_decoys):
        template_name = rng.choice(list(DECOY_TEMPLATES.keys()))
        value = DECOY_TEMPLATES[template_name]
        location = rng.choice(LOCATIONS[5:])
        manifest["items"].append({
            "id": f"decoy_{i}",
            "type": template_name,
            "file": location,
            "line": rng.randint(1, 30),
            "value_hash": f"sha256:{hash(value) & 0xFFFFFFFF:08x}",
            "label": "decoy",
            "planted": True,
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    generate_planted_secrets(Path("benchmarks/corpus/manifest"))
