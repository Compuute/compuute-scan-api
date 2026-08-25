"""Tests for /v1/scan/pay (x402 v2).

The contract tests mock at the HTTP transport layer (httpx.MockTransport),
NOT at verify_payment/settle_payment — so the exact JSON envelope sent to
the facilitator is asserted against the x402 v2 spec. The original
implementation sent {"payload", "requirements"} instead of
{"x402Version", "paymentPayload", "paymentRequirements"} and no test
caught it; these do.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from x402.http.facilitator_client import FacilitatorConfig, HTTPFacilitatorClient
from x402.http.utils import encode_payment_signature_header
from x402.schemas import PaymentPayload

from main import app

WALLET = "0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67"

FAKE_RESULT = {
    "repo_url": "https://github.com/example/repo",
    "score": 90,
    "summary": {"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0, "files_scanned": 3},
    "recommendation": "REVIEW",
    "findings_count": 1,
    "top_findings": [],
    "performance": {"clone_seconds": 1.0, "scan_seconds": 0.2, "repo_size_bytes": 10},
    "scanner": {"name": "compuute-scan", "version": "0.6.2", "layers_covered": ["L0", "L1"]},
    "_disclaimer": "PATTERN MATCH",
}


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _payment_header() -> str:
    """A structurally valid v2 PaymentPayload, base64-encoded like a client would."""
    from api.services import x402_service

    payload = PaymentPayload(
        x402_version=2,
        payload={"signature": "0xsig", "authorization": {"from": "0xPayer"}},
        accepted=x402_service.build_payment_requirements(),
    )
    return encode_payment_signature_header(payload)


def _facilitator_mock(captured: list[httpx.Request]) -> HTTPFacilitatorClient:
    """Facilitator client whose transport records requests and returns success."""

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path.endswith("/verify"):
            return httpx.Response(200, json={"isValid": True, "payer": "0xPayer"})
        if request.url.path.endswith("/settle"):
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "transaction": "0xtxhash",
                    "network": "eip155:8453",
                    "payer": "0xPayer",
                },
            )
        return httpx.Response(404)

    return HTTPFacilitatorClient(
        FacilitatorConfig(
            url="https://facilitator.test/x402",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
    )


@pytest.mark.asyncio
async def test_x402_returns_503_when_not_configured():
    """No wallet configured → 503 with explicit code."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=False):
        async with _client() as client:
            resp = await client.post("/v1/scan/pay", json={"repo_url": "https://github.com/a/b"})
    assert resp.status_code == 503
    assert resp.json()["code"] == "x402_not_configured"


@pytest.mark.asyncio
async def test_x402_402_body_is_spec_compliant_payment_required():
    """402 body must be x402 v2 PaymentRequired: accepts with EIP-712 extra + bazaar ext."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET):
        async with _client() as client:
            resp = await client.post("/v1/scan/pay", json={"repo_url": "https://github.com/a/b"})
    assert resp.status_code == 402
    body = resp.json()
    assert body["x402Version"] == 2
    accept = body["accepts"][0]
    assert accept["scheme"] == "exact"
    assert accept["network"] == "eip155:8453"
    assert accept["payTo"] == WALLET
    assert accept["amount"] == "100000"
    # EIP-712 domain of Base USDC — clients cannot sign EIP-3009 without it.
    assert accept["extra"] == {"name": "USD Coin", "version": "2"}
    # Bazaar discovery extension: info validates against its own schema shape.
    bazaar = body["extensions"]["bazaar"]
    assert bazaar["info"]["input"]["type"] == "http"
    assert bazaar["info"]["input"]["method"] == "POST"
    assert bazaar["info"]["input"]["bodyType"] == "json"
    assert "repo_url" in bazaar["info"]["input"]["body"]
    assert bazaar["schema"]["$schema"].startswith("https://json-schema.org/")


@pytest.mark.asyncio
async def test_x402_402_on_malformed_payment_header():
    """Garbage X-Payment header → 402 with malformed code, not a 500."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET):
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/a/b"},
                headers={"X-Payment": "not-base64-json!!"},
            )
    assert resp.status_code == 402
    assert resp.json()["code"] == "x402_malformed_payment"


@pytest.mark.asyncio
async def test_x402_verify_wire_format_is_v2_envelope():
    """CONTRACT: the facilitator /verify request body must be the x402 v2 envelope."""
    captured: list[httpx.Request] = []
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET), \
         patch("api.services.x402_service._facilitator_client", _facilitator_mock(captured)), \
         patch("api.routes.scan_x402.scan_repo", return_value=FAKE_RESULT):
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/example/repo"},
                headers={"X-Payment": _payment_header()},
            )
    assert resp.status_code == 200

    verify_requests = [r for r in captured if r.url.path.endswith("/verify")]
    assert len(verify_requests) == 1
    sent = json.loads(verify_requests[0].content)
    # The three spec-mandated top-level keys — not {"payload", "requirements"}.
    assert sent["x402Version"] == 2
    assert "paymentPayload" in sent
    assert "paymentRequirements" in sent
    assert "payload" not in sent
    assert "requirements" not in sent
    # paymentPayload is the decoded object, not a base64 string.
    assert isinstance(sent["paymentPayload"], dict)
    assert sent["paymentPayload"]["x402Version"] == 2
    # Verification runs against OUR requirements (server-side wallet).
    assert sent["paymentRequirements"]["payTo"] == WALLET
    assert sent["paymentRequirements"]["network"] == "eip155:8453"


@pytest.mark.asyncio
async def test_x402_settles_and_returns_receipt_header():
    """Valid payment → scan runs, /settle is called, receipt header returned."""
    captured: list[httpx.Request] = []
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET), \
         patch("api.services.x402_service._facilitator_client", _facilitator_mock(captured)), \
         patch("api.routes.scan_x402.scan_repo", return_value=FAKE_RESULT):
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/example/repo"},
                headers={"X-Payment": _payment_header()},
            )
    assert resp.status_code == 200
    assert resp.json()["score"] == 90
    settle_requests = [r for r in captured if r.url.path.endswith("/settle")]
    assert len(settle_requests) == 1
    sent = json.loads(settle_requests[0].content)
    assert sent["x402Version"] == 2 and "paymentPayload" in sent
    assert "PAYMENT-RESPONSE" in resp.headers
    assert resp.headers["PAYMENT-RESPONSE"] == resp.headers["X-PAYMENT-RESPONSE"]


@pytest.mark.asyncio
async def test_x402_402_when_facilitator_rejects():
    """Facilitator says invalid → 402, scan never runs."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"isValid": False, "invalidReason": "insufficient_funds"}
        )

    rejecting = HTTPFacilitatorClient(
        FacilitatorConfig(
            url="https://facilitator.test/x402",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
    )
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET), \
         patch("api.services.x402_service._facilitator_client", rejecting), \
         patch("api.routes.scan_x402.scan_repo") as scan_mock:
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/example/repo"},
                headers={"X-Payment": _payment_header()},
            )
    assert resp.status_code == 402
    assert resp.json()["code"] == "x402_invalid_payment"
    scan_mock.assert_not_called()


@pytest.mark.asyncio
async def test_x402_fails_closed_on_facilitator_network_error():
    """Facilitator unreachable → 402 (fail-closed), never a free scan."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    broken = HTTPFacilitatorClient(
        FacilitatorConfig(
            url="https://facilitator.test/x402",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
    )
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET), \
         patch("api.services.x402_service._facilitator_client", broken), \
         patch("api.routes.scan_x402.scan_repo") as scan_mock:
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay",
                json={"repo_url": "https://github.com/example/repo"},
                headers={"X-Payment": _payment_header()},
            )
    assert resp.status_code == 402
    scan_mock.assert_not_called()


def test_x402_service_module_exports():
    """Public surface other modules rely on."""
    from api.services import x402_service

    assert x402_service.BASE_NETWORK == "eip155:8453"
    assert x402_service.DEFAULT_FACILITATOR_URL == (
        "https://api.cdp.coinbase.com/platform/v2/x402"
    )
    assert callable(x402_service.is_x402_configured)
    assert callable(x402_service.build_payment_requirements)
    assert callable(x402_service.build_bazaar_extension)
    assert callable(x402_service.create_payment_required_response)
    assert callable(x402_service.decode_payment_header)


@pytest.mark.asyncio
async def test_openapi_documents_x402_endpoint():
    """OpenAPI spec exposes /v1/scan/pay with the 402 response documented."""
    async with _client() as client:
        resp = await client.get("/openapi.json")
    spec = resp.json()
    pay = spec["paths"]["/v1/scan/pay"]["post"]
    assert "402" in pay["responses"]


@pytest.mark.asyncio
async def test_x402_discovery_probe_without_body_returns_402():
    """REGRESSION: `awal x402 details` probes each HTTP method with NO body
    and no Content-Type, and treats any non-402 as "endpoint takes no
    payment". A required Pydantic body made FastAPI answer 422 before the
    route ran, so real x402 tooling could not discover our pricing at all.
    """
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET):
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay", headers={"Accept": "application/json"}
            )
    assert resp.status_code == 402, (
        "discovery probe must reach the payment gate, not body validation"
    )
    body = resp.json()
    assert body["x402Version"] == 2
    assert body["accepts"][0]["extra"] == {"name": "USD Coin", "version": "2"}
    assert "bazaar" in body["extensions"]


@pytest.mark.asyncio
async def test_x402_paid_request_without_body_is_422_not_402():
    """Presenting payment with nothing to scan is a client error, and must
    not be answered with another payment challenge."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=True), \
         patch("api.services.x402_service.WALLET_ADDRESS", WALLET):
        async with _client() as client:
            resp = await client.post(
                "/v1/scan/pay", headers={"X-Payment": _payment_header()}
            )
    assert resp.status_code == 422
    assert resp.json()["code"] == "missing_body"


@pytest.mark.asyncio
async def test_x402_discovery_probe_still_503_when_unconfigured():
    """A body-less probe must not mask an unconfigured server as 402."""
    with patch("api.routes.scan_x402.is_x402_configured", return_value=False):
        async with _client() as client:
            resp = await client.post("/v1/scan/pay")
    assert resp.status_code == 503
