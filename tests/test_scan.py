"""Tests for /v1/scan endpoint.

Service-layer tests use a tiny fixture repo (compuute-scan itself, locally).
HTTP-layer tests mock the service-layer to avoid live clone+scan in CI.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.services.scan import (
    ScanError,
    _compute_score,
    _recommendation,
    _top_findings,
    validate_repo_url,
)
from main import app


# ─────────────────────────────────────────────
# Pure / service-layer
# ─────────────────────────────────────────────


def test_validate_repo_url_accepts_canonical():
    assert validate_repo_url("https://github.com/org/repo") == "https://github.com/org/repo"
    assert validate_repo_url("https://github.com/org/repo.git") == "https://github.com/org/repo"
    assert validate_repo_url("https://github.com/org/repo/") == "https://github.com/org/repo"


def test_validate_repo_url_rejects_non_github():
    with pytest.raises(ScanError) as exc:
        validate_repo_url("https://gitlab.com/org/repo")
    assert exc.value.code == "invalid_url"
    with pytest.raises(ScanError):
        validate_repo_url("http://github.com/org/repo")
    with pytest.raises(ScanError):
        validate_repo_url("https://github.com/")
    with pytest.raises(ScanError):
        validate_repo_url("not a url")


def test_validate_repo_url_rejects_oversized():
    with pytest.raises(ScanError):
        validate_repo_url("https://github.com/" + "x" * 300)


def test_compute_score_clean():
    assert _compute_score({"critical": 0, "high": 0, "medium": 0, "low": 0}) == 100


def test_compute_score_critical_drops_hard():
    assert _compute_score({"critical": 2, "high": 0, "medium": 0, "low": 0}) == 50


def test_compute_score_floors_at_zero():
    assert _compute_score({"critical": 10, "high": 10, "medium": 0, "low": 0}) == 0


def test_recommendation_critical_says_avoid():
    r = _recommendation({"critical": 1, "high": 0})
    assert "AVOID" in r


def test_recommendation_clean_says_clean():
    r = _recommendation({"critical": 0, "high": 0, "medium": 0})
    assert "CLEAN" in r


def test_top_findings_orders_by_severity():
    findings = [
        {"id": "L1-001", "severity": "low", "title": "x"},
        {"id": "L1-002", "severity": "critical", "title": "y"},
        {"id": "L1-003", "severity": "high", "title": "z"},
    ]
    top = _top_findings(findings, limit=10)
    assert top[0]["severity"] == "critical"
    assert top[1]["severity"] == "high"
    assert top[2]["severity"] == "low"


# ─────────────────────────────────────────────
# HTTP layer (service-layer mocked)
# ─────────────────────────────────────────────


_FAKE_SCAN_RESULT = {
    "repo_url": "https://github.com/test/repo",
    "scanned_at": "2026-05-23T00:00:00+00:00",
    "scanner": {"name": "compuute-scan", "version": "0.6.2", "layers_covered": ["L0", "L1"]},
    "summary": {"critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0, "files_scanned": 10},
    "score": 89,
    "recommendation": "REVIEW — 1 high finding(s). Triage individually.",
    "findings_count": 2,
    "top_findings": [],
    "l0_discovery": {},
    "performance": {"clone_seconds": 0.1, "scan_seconds": 0.2, "repo_size_bytes": 1000},
    "_disclaimer": "PATTERN MATCH — compuute-scan is a static analyzer...",
}


@pytest.mark.asyncio
async def test_post_scan_happy_path_carries_cache_headers():
    """ETag + Cache-Control + valid response shape."""
    with patch("api.routes.scan.scan_repo", return_value=_FAKE_SCAN_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/scan", json={"repo_url": "https://github.com/test/repo"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 89
    assert body["scanner"]["name"] == "compuute-scan"
    assert "_disclaimer" in body
    assert "etag" in {k.lower() for k in resp.headers}
    assert "max-age=" in resp.headers.get("cache-control", "")


@pytest.mark.asyncio
async def test_post_scan_etag_returns_304():
    with patch("api.routes.scan.scan_repo", return_value=_FAKE_SCAN_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first = await client.post("/v1/scan", json={"repo_url": "https://github.com/test/repo"})
            etag = first.headers["etag"]
            second = await client.post(
                "/v1/scan",
                json={"repo_url": "https://github.com/test/repo"},
                headers={"If-None-Match": etag},
            )
    assert second.status_code == 304


@pytest.mark.asyncio
async def test_post_scan_idempotency_key_returns_cached_without_re_scan():
    call_count = {"n": 0}

    def _stub(url):
        call_count["n"] += 1
        return _FAKE_SCAN_RESULT

    with patch("api.routes.scan.scan_repo", side_effect=_stub):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"Idempotency-Key": "00000000-0000-0000-0000-000000000001"}
            await client.post("/v1/scan", json={"repo_url": "https://github.com/test/repo"}, headers=headers)
            await client.post("/v1/scan", json={"repo_url": "https://github.com/test/repo"}, headers=headers)
    assert call_count["n"] == 1


@pytest.mark.asyncio
async def test_post_scan_rejects_non_github_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/v1/scan", json={"repo_url": "https://gitlab.com/org/repo"})
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "invalid_url"


@pytest.mark.asyncio
async def test_post_scan_rejects_extra_field():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/scan",
            json={"repo_url": "https://github.com/org/repo", "extra": "bad"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_scan_handles_scanner_error_with_correct_status():
    with patch(
        "api.routes.scan.scan_repo",
        side_effect=ScanError("clone_failed", "repo not found", http_status=422),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/v1/scan", json={"repo_url": "https://github.com/missing/repo"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "clone_failed"


@pytest.mark.asyncio
async def test_openapi_contains_scan_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    spec = resp.json()
    assert "/v1/scan" in spec["paths"]
    op = spec["paths"]["/v1/scan"]["post"]
    assert len(op.get("description", "")) > 200
    assert "422" in op["responses"]
    assert "304" in op["responses"]


@pytest.mark.asyncio
async def test_health_endpoint_reports_scanner_availability():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "operational"
    assert "scanner_available" in body
