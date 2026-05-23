"""Tests for /v1/scan/pay (x402 micropayments)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_x402_returns_503_when_not_configured():
    """No wallet address → 503 with clear error code."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/Compuute/compuute-scan"},
            )
    assert resp.status_code == 503
    assert resp.json()["code"] == "x402_not_configured"


@pytest.mark.asyncio
async def test_x402_returns_402_without_payment_header():
    """Configured + no X-Payment → 402 with x402 requirements."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", "0xTEST"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/Compuute/compuute-scan"},
            )
    assert resp.status_code == 402
    assert resp.headers.get("x-payment-protocol") == "x402"
    body = resp.json()
    assert body["x402Version"] == 2
    assert body["accepts"][0]["scheme"] == "exact"
    assert body["accepts"][0]["network"] == "eip155:8453"
    assert "USDC" in body["error"] or "Payment required" in body["error"]


@pytest.mark.asyncio
async def test_x402_returns_402_on_invalid_payment():
    """Configured + invalid X-Payment → 402 (re-prompt with requirements)."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", "0xTEST"), \
         patch("api.routes.scan_x402.verify_payment", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/Compuute/compuute-scan"},
                headers={"X-Payment": "fake-payload"},
            )
    assert resp.status_code == 402
    assert resp.json()["code"] == "x402_invalid_payment"


@pytest.mark.asyncio
async def test_x402_runs_scan_on_valid_payment():
    """Configured + valid X-Payment → 200 with scan result."""
    fake_result = {
        "repo_url": "https://github.com/test/repo",
        "scanned_at": "2026-05-23T00:00:00+00:00",
        "scanner": {"name": "compuute-scan", "version": "0.6.2", "layers_covered": ["L0", "L1"]},
        "summary": {"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0, "files_scanned": 10},
        "score": 92,
        "recommendation": "REVIEW",
        "findings_count": 1,
        "top_findings": [],
        "l0_discovery": {},
        "performance": {"clone_seconds": 0.1, "scan_seconds": 0.2, "repo_size_bytes": 1000},
        "_disclaimer": "PATTERN MATCH...",
    }
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", "0xTEST"), \
         patch("api.routes.scan_x402.verify_payment", return_value=True), \
         patch("api.routes.scan_x402.settle_payment", return_value=True), \
         patch("api.routes.scan_x402.scan_repo", return_value=fake_result):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/test/repo"},
                headers={"X-Payment": "valid-payload"},
            )
    assert resp.status_code == 200
    assert resp.json()["score"] == 92


def test_x402_service_module_exports():
    """Sanity check on the service module API."""
    from api.services.x402_service import (
        PRICE_PER_SCAN_USD,
        build_payment_requirements,
        create_payment_required_response,
        is_x402_configured,
    )
    req = build_payment_requirements()
    assert req["network"] == "eip155:8453"
    assert req["scheme"] == "exact"

    resp = create_payment_required_response()
    assert resp["x402Version"] == 2
    assert resp["accepts"][0]["amount"] == str(int(PRICE_PER_SCAN_USD * 1_000_000))


@pytest.mark.asyncio
async def test_openapi_documents_x402_endpoint():
    """OpenAPI lists /v1/scan/pay with 402 response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    spec = resp.json()
    assert "/v1/scan/pay" in spec["paths"]
    op = spec["paths"]["/v1/scan/pay"]["post"]
    assert "402" in op["responses"]
    assert "x402" in (op.get("description", "").lower())
