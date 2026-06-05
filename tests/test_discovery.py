"""Tests for /.well-known/* discovery endpoints (#26)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_agent_json_returns_200_and_has_skills():
    """Existing canonical A2A endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "compuute-scan-api"
    assert any(s["id"] == "scan_mcp_server" for s in body["skills"])


@pytest.mark.asyncio
async def test_agent_card_json_is_alias_of_agent_json():
    """New alias must return identical content to the canonical endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        canonical = await client.get("/.well-known/agent.json")
        alias = await client.get("/.well-known/agent-card.json")
    assert alias.status_code == 200
    assert alias.json() == canonical.json()


@pytest.mark.asyncio
async def test_x402_json_returns_manifest_with_endpoints_when_configured():
    """When wallet is set, x402.json lists /v1/scan/pay with USDC/Base pricing."""
    with patch("api.services.x402_service.WALLET_ADDRESS", "0xWALLETTEST"), \
         patch("api.services.x402_service.is_x402_configured", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/.well-known/x402.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["x402Version"] == 2
    assert body["provider"]["name"] == "Compuute AB"
    assert len(body["endpoints"]) == 1
    ep = body["endpoints"][0]
    assert ep["url"].endswith("/v1/scan/pay")
    assert ep["method"] == "POST"
    assert ep["accepts"][0]["network"] == "eip155:8453"
    assert ep["accepts"][0]["payTo"] == "0xWALLETTEST"
    # Free endpoint also listed
    assert body["freeEndpoints"][0]["url"].endswith("/v1/scan")


@pytest.mark.asyncio
async def test_x402_json_returns_empty_endpoints_when_not_configured():
    """When wallet is unset, manifest still returns 200 but with no paid endpoints."""
    with patch("api.services.x402_service.is_x402_configured", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/.well-known/x402.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["endpoints"] == []
    assert len(body["freeEndpoints"]) == 1


@pytest.mark.asyncio
async def test_x402_no_suffix_alias_returns_same_as_json():
    """`/.well-known/x402` (no suffix) returns same body as `.json` variant."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with_suffix = await client.get("/.well-known/x402.json")
        no_suffix = await client.get("/.well-known/x402")
    assert no_suffix.status_code == 200
    assert no_suffix.json() == with_suffix.json()


@pytest.mark.asyncio
async def test_sitemap_lists_new_well_known_paths():
    """sitemap.xml advertises the new aliases so search engines pick them up."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/sitemap.xml")
    assert resp.status_code == 200
    body = resp.text
    assert "/.well-known/agent-card.json" in body
    assert "/.well-known/x402.json" in body


@pytest.mark.asyncio
async def test_robots_allows_paid_and_free_scan_paths():
    """robots.txt explicitly allows /v1/scan and /v1/scan/pay."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/robots.txt")
    assert resp.status_code == 200
    body = resp.text
    assert "Allow: /v1/scan" in body
    assert "Allow: /v1/scan/pay" in body
