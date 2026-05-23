"""POST /v1/scan — scan a public GitHub MCP-server repo with compuute-scan.

Agent-callable. Idempotent retries are free (24h cache). ETag-based caching
supported. Strict input validation. Findings carry a triage disclaimer.
"""
from __future__ import annotations

import hashlib
import json

import structlog
from fastapi import APIRouter, Header, HTTPException, Request, Response, status

from api.serializers.scan_serializer import ScanRequest, ScanResponse
from api.services.scan import ScanError, scan_repo

logger = structlog.get_logger()
router = APIRouter()

_IDEMPOTENCY_TTL = 86400         # 24h
_CACHE_MAX_AGE = 1800            # 30 min — scan results are mildly stale-tolerant


def _etag_for(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return f'"{digest}"'


# In-process LRU cache (MVP). Production: Redis with TTL. Capped at 1000 entries.
_idem_cache: dict[str, dict] = {}
_idem_order: list[str] = []
_IDEM_CACHE_MAX = 1000


def _cache_get(key: str) -> dict | None:
    return _idem_cache.get(key)


def _cache_put(key: str, value: dict) -> None:
    if key in _idem_cache:
        return
    _idem_cache[key] = value
    _idem_order.append(key)
    while len(_idem_order) > _IDEM_CACHE_MAX:
        oldest = _idem_order.pop(0)
        _idem_cache.pop(oldest, None)


@router.post(
    "/scan",
    response_model=ScanResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Scan a public GitHub MCP-server repo with compuute-scan",
    description=(
        "Clones a public GitHub repository and runs compuute-scan's L0+L1 static "
        "analysis (37 MCP-specific rules across 8 languages: TS/JS, Python, Go, "
        "Rust, C#, Java, Kotlin). Returns a structured summary with severity "
        "counts, a coarse 0-100 score, recommendation, and the 10 most severe "
        "findings inline.\n\n"
        "**Idempotency:** supply `Idempotency-Key` header (UUIDv4 recommended). "
        "Identical key returns the cached scan for 24h with no re-execution.\n\n"
        "**Caching:** responses are `Cache-Control: public, max-age=1800` with an "
        "`ETag`. Send `If-None-Match` on revisit for a 304 Not Modified.\n\n"
        "**Limits:** repo must be public, <200 MB, clone <60s, scan <120s.\n\n"
        "**When NOT to use:** for exploitability assessment of a specific code "
        "path (this is pattern matching — book a manual audit at compuute.se/audit "
        "for that). For private repos, use the on-prem CLI: `npx compuute-scan ./repo`."
    ),
    responses={
        200: {"description": "Scan completed successfully."},
        304: {"description": "Not Modified — caller's ETag is current."},
        413: {"description": "Repo exceeds 200 MB size limit."},
        422: {"description": "Invalid GitHub URL or repo not found."},
        502: {"description": "Scanner failure (compuute-scan returned no/bad JSON)."},
        504: {"description": "Clone or scan timeout."},
    },
)
async def scan_endpoint(
    payload: ScanRequest,
    response: Response,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    if_none_match: str | None = Header(default=None, alias="If-None-Match"),
):
    """Scan a public GitHub MCP-server repo."""
    cache_key = None
    if idempotency_key:
        cache_key = f"scan:{idempotency_key}:{payload.repo_url}"
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info("scan_idempotent_hit", idempotency_key=idempotency_key, repo=payload.repo_url)
            etag = _etag_for(cached)
            if if_none_match and if_none_match.strip() == etag:
                _apply_headers(response, etag)
                return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=dict(response.headers))
            _apply_headers(response, etag)
            return cached

    try:
        result = scan_repo(payload.repo_url)
    except ScanError as e:
        logger.warning("scan_failed", code=e.code, repo=payload.repo_url, message=e.message)
        raise HTTPException(status_code=e.http_status, detail={"code": e.code, "message": e.message})
    except Exception as e:  # noqa: BLE001
        logger.error("scan_unhandled", repo=payload.repo_url, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": "unexpected failure during scan"},
        )

    etag = _etag_for(result)
    if if_none_match and if_none_match.strip() == etag:
        _apply_headers(response, etag)
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=dict(response.headers))

    _apply_headers(response, etag)

    if cache_key:
        _cache_put(cache_key, result)

    logger.info(
        "scan_complete",
        repo=payload.repo_url,
        score=result["score"],
        critical=result["summary"]["critical"],
        high=result["summary"]["high"],
        files=result["summary"]["files_scanned"],
    )
    return result


@router.get(
    "/scan/info",
    summary="Scanner version + capabilities (for agents deciding whether to call /v1/scan)",
    description=(
        "Reports the bundled compuute-scan version, supported languages, layers "
        "covered, and rate limits. Use this to decide whether the scanner meets "
        "your freshness/coverage criteria before calling /v1/scan."
    ),
)
async def scan_info():
    """Reports scanner capabilities."""
    from api.services.scan import COMPUUTE_SCAN_PATH, MAX_REPO_SIZE_MB, SCAN_TIMEOUT_SEC, CLONE_TIMEOUT_SEC
    info = {
        "scanner_path_exists": COMPUUTE_SCAN_PATH.exists(),
        "max_repo_size_mb": MAX_REPO_SIZE_MB,
        "clone_timeout_sec": CLONE_TIMEOUT_SEC,
        "scan_timeout_sec": SCAN_TIMEOUT_SEC,
        "supported_ecosystems": ["TypeScript", "JavaScript", "Python", "Go", "Rust", "C#", "Java", "Kotlin"],
        "layers_covered": ["L0", "L1"],
        "paid_layers_available": ["L2", "L3", "L4 — see https://compuute.se/audit"],
    }
    return info


def _apply_headers(response: Response, etag: str) -> None:
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = f"public, max-age={_CACHE_MAX_AGE}"
    response.headers["Vary"] = "If-None-Match"
