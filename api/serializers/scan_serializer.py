"""Scan-API Pydantic models — strict validation (input is untrusted)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ScanRequest(BaseModel):
    """POST /v1/scan input."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {"repo_url": "https://github.com/Compuute/compuute-scan"},
                {"repo_url": "https://github.com/modelcontextprotocol/servers"},
            ]
        },
    )

    repo_url: str = Field(
        ...,
        min_length=20,
        max_length=256,
        description=(
            "Public GitHub HTTPS URL. Only github.com is accepted in this version. "
            "Repo must be public and < 200 MB. Example: https://github.com/org/repo"
        ),
    )


class FindingSummary(BaseModel):
    id: str | None = None
    title: str | None = None
    severity: str | None = None
    file: str | None = None
    line: int | None = None
    owasp: str | None = None
    cwe: str | None = None


class ScannerInfo(BaseModel):
    name: str
    version: str
    layers_covered: list[str] = Field(default_factory=list)


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    files_scanned: int = 0


class Performance(BaseModel):
    clone_seconds: float
    scan_seconds: float
    repo_size_bytes: int


class ScanResponse(BaseModel):
    """POST /v1/scan response.

    Stable schema. Agents may rely on field names. Top-level fields cover
    summary + score + recommendation; `top_findings` is bounded to 10 for
    payload size — full findings list is a v2 enhancement.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "repo_url": "https://github.com/org/example-mcp",
                    "scanned_at": "2026-05-23T08:00:00+00:00",
                    "scanner": {
                        "name": "compuute-scan",
                        "version": "0.6.2",
                        "layers_covered": ["L0", "L1"],
                    },
                    "summary": {
                        "critical": 0,
                        "high": 3,
                        "medium": 2,
                        "low": 0,
                        "info": 0,
                        "files_scanned": 44,
                    },
                    "score": 82,
                    "recommendation": "REVIEW — 3 high finding(s). Triage individually.",
                    "findings_count": 5,
                    "top_findings": [],
                    "l0_discovery": {},
                    "performance": {
                        "clone_seconds": 1.2,
                        "scan_seconds": 0.5,
                        "repo_size_bytes": 41234,
                    },
                    "_disclaimer": "PATTERN MATCH — compuute-scan is a static analyzer...",
                }
            ]
        },
    )

    repo_url: str
    scanned_at: str = Field(..., description="UTC timestamp when the scan started.")
    scanner: ScannerInfo
    summary: SeveritySummary
    score: int = Field(..., ge=0, le=100, description="0-100, higher safer.")
    recommendation: str
    findings_count: int
    top_findings: list[FindingSummary] = Field(default_factory=list)
    l0_discovery: dict = Field(default_factory=dict)
    performance: Performance
    disclaimer: str = Field(
        ...,
        alias="_disclaimer",
        description=(
            "Mandatory disclaimer: compuute-scan is a static analyzer. Findings "
            "indicate vulnerable patterns are *present*; exploitability requires "
            "manual dataflow review."
        ),
    )
