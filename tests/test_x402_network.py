"""Tests for X402_NETWORK selection (mainnet vs Base Sepolia).

The trap these guard: Base mainnet USDC and Base Sepolia USDC do NOT share
an EIP-712 domain name ("USD Coin" vs "USDC"). Swapping only the network id
and contract address while keeping the mainnet domain makes every client
signature fail verification, with an error that reads like a bad API key.
Asset and domain must always move together.
"""
from __future__ import annotations

import importlib

import pytest
from httpx import ASGITransport, AsyncClient


def _reload_service(monkeypatch, **env):
    """Reload x402_service with the given env, since config is module-level."""
    for key in ("X402_NETWORK", "X402_WALLET_ADDRESS", "X402_PRICE_USD"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import api.services.x402_service as svc

    return importlib.reload(svc)


@pytest.fixture(autouse=True)
def _restore_service_module():
    """Leave the module back on its default config for other test files."""
    yield
    import api.services.x402_service as svc

    importlib.reload(svc)


def test_defaults_to_mainnet(monkeypatch):
    """No X402_NETWORK set → Base mainnet, never testnet."""
    svc = _reload_service(monkeypatch)
    assert svc.NETWORK == "eip155:8453"
    assert svc.IS_TESTNET is False
    assert svc.USDC_ADDRESS == "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    assert svc.USDC_EIP712 == {"name": "USD Coin", "version": "2"}


def test_sepolia_uses_its_own_asset_and_eip712_domain(monkeypatch):
    """Base Sepolia signs as "USDC", not "USD Coin" — the whole point."""
    svc = _reload_service(monkeypatch, X402_NETWORK="eip155:84532")
    assert svc.NETWORK == "eip155:84532"
    assert svc.IS_TESTNET is True
    assert svc.USDC_ADDRESS == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    assert svc.USDC_EIP712 == {"name": "USDC", "version": "2"}


def test_mainnet_and_sepolia_domains_differ():
    """Regression guard: if these ever match, one of them is wrong."""
    import api.services.x402_service as svc

    mainnet = svc.NETWORKS["eip155:8453"]
    sepolia = svc.NETWORKS["eip155:84532"]
    assert mainnet["eip712"] != sepolia["eip712"]
    assert mainnet["asset"] != sepolia["asset"]


def test_unknown_network_falls_back_to_mainnet(monkeypatch):
    """A typo must not disable payments or silently pick a testnet."""
    svc = _reload_service(monkeypatch, X402_NETWORK="eip155:99999")
    assert svc.NETWORK == "eip155:8453"
    assert svc.IS_TESTNET is False


def test_blank_network_falls_back_to_mainnet(monkeypatch):
    """An empty env var (set but blank) behaves like unset."""
    svc = _reload_service(monkeypatch, X402_NETWORK="   ")
    assert svc.NETWORK == "eip155:8453"


def test_payment_requirements_follow_selected_network(monkeypatch):
    """The 402 requirements must carry the selected network's asset + domain."""
    svc = _reload_service(
        monkeypatch, X402_NETWORK="eip155:84532", X402_WALLET_ADDRESS="0xWALLET"
    )
    req = svc.build_payment_requirements()
    assert req.network == "eip155:84532"
    assert req.asset == "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
    assert req.extra == {"name": "USDC", "version": "2"}
    assert req.pay_to == "0xWALLET"


@pytest.mark.asyncio
async def test_health_reports_active_network():
    """Operators must see the payment mode without reading env vars."""
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/v1/health")
    x402 = resp.json()["x402"]
    assert x402["network"] == "eip155:8453"
    assert x402["testnet"] is False
    assert x402["network_label"] == "Base mainnet"
    assert "enabled" in x402
