"""Scan-as-a-Service — wraps compuute-scan for HTTP/MCP consumption.

This is the *actual product*: clone a repo (GitHub URL), run the full
compuute-scan against it in a tempdir, parse the JSON output, return a
structured response. Reuses 95% of compuute-scan's value (37 L1 rules,
8-language coverage, MCP-specific threat patterns) — not just its CVE
side-feature.

Threat model:
  - Input is a public Git URL (validated upstream by serializer)
  - We shallow-clone with strict size/timeout limits
  - We invoke the local compuute-scan CLI in --json mode
  - We NEVER execute the cloned code (compuute-scan is static analysis,
    Node.js built-ins only — see compuute-scan/SECURITY.md)
  - tempdir is wiped after every scan

Production hardening (post-MVP): wrap clone+scan in a Docker sandbox with
--network none, read-only mount, cap_drop ALL (mirrors compuute-scan's
own scan.sh recipe).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

# Default path to compuute-scan repo. Override via env if installed elsewhere.
COMPUUTE_SCAN_PATH = Path(
    os.environ.get("COMPUUTE_SCAN_PATH", os.path.expanduser("~/compuute-scan/compuute-scan.js"))
)

CLONE_TIMEOUT_SEC = int(os.environ.get("SCAN_CLONE_TIMEOUT", "60"))
SCAN_TIMEOUT_SEC = int(os.environ.get("SCAN_TIMEOUT", "120"))
MAX_REPO_SIZE_MB = int(os.environ.get("SCAN_MAX_REPO_SIZE_MB", "200"))

# Strict GitHub-only URL pattern. We reject GitLab/Bitbucket here to keep the
# threat surface tight for the MVP. Add later with deliberate review.
_REPO_URL_RE = re.compile(
    r"^https://github\.com/[a-zA-Z0-9][\w.\-]{0,38}/[a-zA-Z0-9][\w.\-]{0,99}(?:\.git)?/?$"
)


class ScanError(Exception):
    """Service-layer error with a stable code consumable by the route."""

    def __init__(self, code: str, message: str, http_status: int = 422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


# ─────────────────────────────────────────────
# Disclaimer (mirrors compuute-scan's L1-038 framing)
# ─────────────────────────────────────────────

_DISCLAIMER = (
    "PATTERN MATCH — compuute-scan is a static analyzer. Findings indicate that "
    "a vulnerable pattern is present in the source; exploitability depends on "
    "whether the affected code path is actually reachable from an attacker-"
    "controlled input. Manual dataflow review required for production decisions. "
    "Scanner version and rule set are reported in `scanner` field for audit."
)


# ─────────────────────────────────────────────
# Input validation (URL)
# ─────────────────────────────────────────────


def validate_repo_url(url: str) -> str:
    """Normalize + validate a GitHub HTTPS URL. Returns the canonical form.

    Raises ScanError with code='invalid_url' on bad input.
    """
    if not url or len(url) > 256:
        raise ScanError("invalid_url", "URL must be 1-256 chars.", http_status=422)
    stripped = url.strip().rstrip("/")
    if not _REPO_URL_RE.match(stripped + ("" if stripped.endswith(".git") else ".git")):
        # Be tolerant of trailing-slash + .git variants
        if not _REPO_URL_RE.match(stripped):
            raise ScanError(
                "invalid_url",
                "Only public GitHub HTTPS URLs are accepted in this version. "
                "Example: https://github.com/org/repo",
                http_status=422,
            )
    # Strip trailing .git for the canonical record (compuute-scan handles both)
    canonical = stripped[:-4] if stripped.endswith(".git") else stripped
    return canonical


# ─────────────────────────────────────────────
# Clone + scan pipeline
# ─────────────────────────────────────────────


def _clone(url: str, dest: Path) -> dict[str, Any]:
    """Shallow-clone a public repo with strict timeout and size limit."""
    start = time.monotonic()
    cmd = [
        "git",
        "clone",
        "--depth", "1",
        "--single-branch",
        "--no-tags",
        "--filter=blob:limit=10m",
        url,
        str(dest),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ScanError(
            "clone_timeout",
            f"git clone exceeded {CLONE_TIMEOUT_SEC}s",
            http_status=504,
        )
    if proc.returncode != 0:
        # Common failures: 404, auth required for private repo, network
        stderr_tail = (proc.stderr or "")[-200:]
        raise ScanError(
            "clone_failed",
            f"git clone failed: {stderr_tail.strip()}",
            http_status=422 if "not found" in stderr_tail.lower() else 502,
        )

    # Enforce size cap post-clone
    total = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file())
    if total > MAX_REPO_SIZE_MB * 1024 * 1024:
        raise ScanError(
            "repo_too_large",
            f"Cloned repo > {MAX_REPO_SIZE_MB} MB.",
            http_status=413,
        )

    return {
        "clone_seconds": round(time.monotonic() - start, 2),
        "size_bytes": total,
    }


def _run_scanner(repo_path: Path) -> dict[str, Any]:
    """Invoke compuute-scan in --json mode against a cloned repo.

    Writes scanner output to a tempfile via --output to avoid stdout-pipe
    truncation on large monorepos (~64KB pipe buffer would corrupt JSON).
    """
    if not COMPUUTE_SCAN_PATH.exists():
        raise ScanError(
            "scanner_unavailable",
            f"compuute-scan not found at {COMPUUTE_SCAN_PATH}. "
            "Set COMPUUTE_SCAN_PATH env var.",
            http_status=500,
        )
    start = time.monotonic()
    # Sibling temp file inside the same temp parent dir as the cloned repo
    out_file = repo_path.parent / "scan-output.json"
    cmd = [
        "node",
        str(COMPUUTE_SCAN_PATH),
        str(repo_path),
        "--json",
        "--output",
        str(out_file),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SCAN_TIMEOUT_SEC,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise ScanError(
            "scan_timeout",
            f"compuute-scan exceeded {SCAN_TIMEOUT_SEC}s",
            http_status=504,
        )
    # compuute-scan exits non-zero when findings exist; that's expected.
    if not out_file.exists():
        raise ScanError(
            "scanner_no_output",
            f"compuute-scan produced no output file. stderr: {(proc.stderr or '')[:200]}",
            http_status=502,
        )
    try:
        with out_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ScanError(
            "scanner_bad_json",
            f"compuute-scan produced invalid JSON: {e}",
            http_status=502,
        )
    data["_scan_seconds"] = round(time.monotonic() - start, 2)
    return data


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────


def scan_repo(url: str) -> dict[str, Any]:
    """Scan a public GitHub repo with compuute-scan; return structured findings.

    Pure with respect to external state: no DB writes, no logging side-effects
    here (route layer logs). Tempdir is cleaned up unconditionally.
    """
    canonical_url = validate_repo_url(url)

    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with tempfile.TemporaryDirectory(prefix="compuute-scan-") as tmp:
        repo_dir = Path(tmp) / "repo"
        clone_meta = _clone(canonical_url, repo_dir)
        try:
            raw = _run_scanner(repo_dir)
        finally:
            # tempfile.TemporaryDirectory handles cleanup, but be explicit
            # in case of partial state in production override environments.
            try:
                shutil.rmtree(repo_dir, ignore_errors=True)
            except Exception:
                pass

    summary = raw.get("summary", {}) or {}
    findings = raw.get("findings", []) or []
    score = _compute_score(summary)

    return {
        "repo_url": canonical_url,
        "scanned_at": started_at,
        "scanner": {
            "name": "compuute-scan",
            "version": raw.get("version") or "unknown",
            "layers_covered": raw.get("layersCovered") or [],
        },
        "summary": {
            "critical": summary.get("critical", 0),
            "high": summary.get("high", 0),
            "medium": summary.get("medium", 0),
            "low": summary.get("low", 0),
            "info": summary.get("info", 0),
            "files_scanned": raw.get("filesScanned", 0),
        },
        "score": score,
        "recommendation": _recommendation(summary),
        "findings_count": len(findings),
        "top_findings": _top_findings(findings, limit=10),
        "l0_discovery": raw.get("l0Discovery") or {},
        "performance": {
            "clone_seconds": clone_meta["clone_seconds"],
            "scan_seconds": raw.get("_scan_seconds", 0),
            "repo_size_bytes": clone_meta["size_bytes"],
        },
        "_disclaimer": _DISCLAIMER,
    }


# ─────────────────────────────────────────────
# Scoring + summarisation
# ─────────────────────────────────────────────


_SEVERITY_WEIGHT = {"critical": 25, "high": 8, "medium": 3, "low": 1}


def _compute_score(summary: dict[str, Any]) -> int:
    """Higher = safer. 100 = clean. Bounded at 0.

    Coarse summary, not a precision claim. Disclaimer in response.
    """
    penalty = sum(
        _SEVERITY_WEIGHT.get(k, 0) * int(summary.get(k, 0) or 0)
        for k in ("critical", "high", "medium", "low")
    )
    return max(0, 100 - penalty)


def _recommendation(summary: dict[str, Any]) -> str:
    crit = int(summary.get("critical", 0) or 0)
    high = int(summary.get("high", 0) or 0)
    if crit:
        return (
            f"AVOID — {crit} critical and {high} high finding(s). "
            "Manual triage required; do not deploy without addressing critical issues."
        )
    if high >= 5:
        return f"REVIEW — {high} high-severity findings indicate broad pattern exposure."
    if high:
        return f"REVIEW — {high} high finding(s). Triage individually."
    if int(summary.get("medium", 0) or 0):
        return "ACCEPTABLE for low-risk deployments; review medium findings before production."
    return "CLEAN — no high/critical findings against compuute-scan's L0+L1 rule set."


def _top_findings(findings: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Return at most `limit` findings, prioritising critical/high. Drops noise."""
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(
        findings,
        key=lambda f: (
            severity_rank.get(f.get("severity", "info"), 99),
            f.get("id", ""),
        ),
    )
    out = []
    for f in sorted_findings[:limit]:
        out.append({
            "id": f.get("id"),
            "title": f.get("title"),
            "severity": f.get("severity"),
            "file": f.get("file"),
            "line": f.get("line"),
            "owasp": f.get("owasp"),
            "cwe": f.get("cwe"),
        })
    return out
