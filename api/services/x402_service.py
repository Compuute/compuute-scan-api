"""x402 micropayment integration — pay-per-scan in USDC on Base L2.

Implements the x402 protocol without the SDK to avoid dependency issues in prod.
Uses direct HTTP calls to the Coinbase facilitator for verification and settlement.

Adapted from the lead-enrich-api x402 service. Same protocol, different pricing
and a single fixed-price scan instead of per-unit billing.

Flow:
  1. Agent calls POST /v1/scan/pay without X-Payment header.
  2. Server returns 402 with x402 payment requirements (USDC amount, wallet, network).
  3. Agent pays via x402 facilitator (Coinbase or self-hosted).
  4. Agent retries with X-Payment header containing the signed payment payload.
  5. Server verifies payment via facilitator, runs the scan, settles.

Configuration via env vars:
  - X402_WALLET_ADDRESS  : Coinbase wallet (Base L2) that receives USDC.
  - X402_PRICE_USD       : Price per scan in USD. Default $0.10.
  - X402_FACILITATOR_URL : Default https://x402.org/facilitator.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()

# USDC on Base L2 (CAIP-2 format)
BASE_NETWORK = "eip155:8453"
USDC_BASE_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Default Coinbase facilitator
FACILITATOR_URL = os.environ.get("X402_FACILITATOR_URL", "https://x402.org/facilitator")

# Price per scan in USD (fixed). USDC has 6 decimals.
PRICE_PER_SCAN_USD = float(os.environ.get("X402_PRICE_USD", "0.10"))
WALLET_ADDRESS = os.environ.get("X402_WALLET_ADDRESS", "")


def is_x402_configured() -> bool:
    """True iff WALLET_ADDRESS is set."""
    return bool(WALLET_ADDRESS)


def build_payment_requirements(price_usd: float | None = None) -> dict[str, Any]:
    """Build x402 payment requirements for one scan."""
    price = price_usd if price_usd is not None else PRICE_PER_SCAN_USD
    amount_micro = str(int(price * 1_000_000))  # USDC has 6 decimals
    return {
        "scheme": "exact",
        "network": BASE_NETWORK,
        "asset": USDC_BASE_ADDRESS,
        "amount": amount_micro,
        "payTo": WALLET_ADDRESS,
        "maxTimeoutSeconds": 300,
    }


def create_payment_required_response(price_usd: float | None = None) -> dict[str, Any]:
    """Build the 402 Payment Required response body (x402 v2 format)."""
    price = price_usd if price_usd is not None else PRICE_PER_SCAN_USD
    requirements = build_payment_requirements(price)
    return {
        "x402Version": 2,
        "error": f"Payment required: ${price:.4f} USDC per scan",
        "accepts": [requirements],
        "resource": {
            "url": "/v1/scan/pay",
            "method": "POST",
            "contentType": "application/json",
            "description": (
                "Scan a public GitHub MCP-server repo with compuute-scan. "
                "Returns severity counts, score, top findings, and a triage disclaimer."
            ),
            "category": "security",
            "tags": ["mcp", "static-analysis", "supply-chain", "cve"],
        },
    }


async def verify_payment(payment_header: str, price_usd: float | None = None) -> bool:
    """Verify an x402 payment payload via the facilitator.

    Returns True iff facilitator confirms the on-chain settlement matches
    the requirements. Network errors → False (fail-closed).
    """
    requirements = build_payment_requirements(price_usd)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(
                f"{FACILITATOR_URL}/verify",
                json={"payload": payment_header, "requirements": requirements},
            )
            if resp.status_code == 200:
                result = resp.json()
                is_valid = bool(result.get("isValid", False))
                if is_valid:
                    logger.info("x402_payment_verified", price_usd=price_usd or PRICE_PER_SCAN_USD)
                else:
                    logger.warning("x402_payment_invalid", result=result)
                return is_valid
            logger.warning("x402_facilitator_error", status=resp.status_code, body=resp.text[:200])
            return False
    except Exception as e:  # noqa: BLE001
        logger.warning("x402_verify_failed", error=str(e))
        return False


async def settle_payment(payment_header: str, price_usd: float | None = None) -> bool:
    """Trigger settlement of an x402 payment via the facilitator.

    Some facilitators auto-settle on verify. This call is best-effort and
    returns True even if the facilitator does not implement /settle —
    verification already happened before this is called.
    """
    requirements = build_payment_requirements(price_usd)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.post(
                f"{FACILITATOR_URL}/settle",
                json={"payload": payment_header, "requirements": requirements},
            )
            if resp.status_code == 200:
                logger.info("x402_payment_settled")
                return True
            logger.info("x402_settle_no_op", status=resp.status_code)
            return True
    except Exception as e:  # noqa: BLE001
        logger.warning("x402_settle_failed", error=str(e))
        return True  # best-effort
