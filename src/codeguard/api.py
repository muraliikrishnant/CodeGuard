"""FastAPI backend for CodeGuard frontend."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from codeguard.config import ScanConfig
from codeguard.pipeline import run_scan

app = FastAPI(title="CodeGuard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    repo_path: str
    history: bool = True
    provider: str = "nvidia"
    model: str = ""
    threshold: float = 0.8


class ScanResponse(BaseModel):
    scan_id: str
    timestamp: str
    total_candidates: int
    findings_count: int
    suppressed_count: int
    errors_count: int
    findings: list[dict[str, Any]]
    suppressed: list[dict[str, Any]]
    errors: list[str]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scan", response_model=ScanResponse)
def scan_repo(req: ScanRequest) -> ScanResponse:
    """Run a CodeGuard scan and return results."""
    repo_path = Path(req.repo_path).resolve()
    if not repo_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {req.repo_path}")

    config = ScanConfig(
        history=req.history,
        provider=req.provider,
        model=req.model,
        confidence_threshold=req.threshold,
    )

    report = run_scan(repo_path, config)

    def finding_to_dict(f: Any) -> dict[str, Any]:
        return {
            "file_path": f.candidate.file_path,
            "line_number": f.candidate.line_number,
            "secret_type": f.candidate.secret_type,
            "detector": f.candidate.detector_name,
            "verdict": f.final_verdict,
            "suppression_reason": f.suppression_reason,
            "llm_label": f.llm_verdict.label if f.llm_verdict else None,
            "llm_confidence": f.llm_verdict.confidence if f.llm_verdict else None,
            "llm_reasoning": f.llm_verdict.reasoning if f.llm_verdict else None,
            "commit_sha": f.candidate.commit_sha,
        }

    return ScanResponse(
        scan_id=report.scan_id,
        timestamp=report.timestamp,
        total_candidates=report.stats.get("total_candidates", 0),
        findings_count=len(report.findings),
        suppressed_count=len(report.suppressed),
        errors_count=len(report.errors),
        findings=[finding_to_dict(f) for f in report.findings],
        suppressed=[finding_to_dict(f) for f in report.suppressed],
        errors=report.errors,
    )
