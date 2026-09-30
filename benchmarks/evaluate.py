"""Precision / recall / FPR evaluation with confidence intervals."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConfusionMatrix:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom > 0 else 0.0

    @property
    def fpr(self) -> float:
        denom = self.fp + self.tn
        return self.fp / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


@dataclass
class EvalResult:
    tool_name: str
    matrix: ConfusionMatrix
    per_repo: dict[str, ConfusionMatrix] = field(default_factory=dict)
    ci_precision: tuple[float, float] = (0.0, 0.0)
    ci_recall: tuple[float, float] = (0.0, 0.0)
    ci_fpr: tuple[float, float] = (0.0, 0.0)


def _wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def evaluate(
    manifest_path: Path,
    results_path: Path,
    tool_name: str,
    line_tolerance: int = 3,
) -> EvalResult:
    """Evaluate a tool's output against ground truth manifest."""
    manifest = json.loads(manifest_path.read_text())
    results = json.loads(results_path.read_text())

    ground_truth = manifest.get("items", [])
    detections = results.get("findings", [])

    real_items = [g for g in ground_truth if g["label"] == "real"]
    decoy_items = [g for g in ground_truth if g["label"] == "decoy"]

    matrix = ConfusionMatrix()

    matched_real: set[str] = set()
    for det in detections:
        det_file = det.get("file", det.get("file_path", ""))
        det_line = det.get("line", det.get("line_number", 0))

        matched = False
        for item in real_items:
            if (
                item["file"] == det_file
                and abs(item["line"] - det_line) <= line_tolerance
                and item["id"] not in matched_real
            ):
                matrix.tp += 1
                matched_real.add(item["id"])
                matched = True
                break

        if not matched:
            is_decoy = any(
                d["file"] == det_file and abs(d["line"] - det_line) <= line_tolerance
                for d in decoy_items
            )
            if is_decoy:
                matrix.fp += 1

    matrix.fn = len(real_items) - len(matched_real)
    matrix.tn = len(decoy_items) - matrix.fp

    result = EvalResult(
        tool_name=tool_name,
        matrix=matrix,
        ci_precision=_wilson_ci(matrix.tp, matrix.tp + matrix.fp),
        ci_recall=_wilson_ci(matrix.tp, matrix.tp + matrix.fn),
        ci_fpr=_wilson_ci(matrix.fp, matrix.fp + matrix.tn),
    )
    return result


def format_results(results: list[EvalResult]) -> str:
    """Format evaluation results as a markdown table."""
    lines = [
        "| Tool | Precision | Recall | FPR | F1 | TP | FP | FN | TN |",
        "|------|-----------|--------|-----|----|----|----|----|-----|",
    ]
    for r in results:
        m = r.matrix
        lines.append(
            f"| {r.tool_name} | {m.precision:.1%} "
            f"({r.ci_precision[0]:.1%}-{r.ci_precision[1]:.1%}) "
            f"| {m.recall:.1%} "
            f"({r.ci_recall[0]:.1%}-{r.ci_recall[1]:.1%}) "
            f"| {m.fpr:.1%} "
            f"({r.ci_fpr[0]:.1%}-{r.ci_fpr[1]:.1%}) "
            f"| {m.f1:.1%} | {m.tp} | {m.fp} | {m.fn} | {m.tn} |"
        )
    return "\n".join(lines)
