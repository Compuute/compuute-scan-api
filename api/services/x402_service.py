"""x402 micropayment integration — pay-per-scan in USDC on Base L2.

Built on the official `x402` Python SDK so the facilitator wire format
(verify/settle envelopes, header encoding, response models) always matches
the x402 v2 protocol instead of a hand-rolled approximation.

Flow:
  1. Agent calls POST /v1/scan/pay without X-Payment header.
  2. Server returns 402 with x402 v2 PaymentRequired body, including the
     Bazaar discovery extension so facilitators can catalog the endpoint.
  3. Agent signs payment and retries with the base64 X-Payment header.
  4. Server decodes the PaymentPayload, verifies against OUR requirements
     via the facilitator, runs the scan, settles.

Facilitator: defaults to the CDP facilitator, which serves both Base mainnet
and Base Sepolia. The community facilitator at x402.org is Sepolia-only —
pointing mainnet payments there fails verification.

Configuration via env vars:
  - X402_WALLET_ADDRESS  : Base L2 address that receives USDC (required to enable).
  - X402_NETWORK         : CAIP-2 network id. Default eip155:8453 (Base mainnet).
                           Set eip155:84532 for Base Sepolia to rehearse the
                           full payment chain with free testnet USDC.
  - X402_PRICE_USD       : Price per scan in USD. Default $0.10.
  - X402_FACILITATOR_URL : Default https://api.cdp.coinbase.com/platform/v2/x402.
  - CDP_API_KEY_ID / CDP_API_KEY_SECRET : CDP API key for facilitator auth.
"""
from __future__ import annotations

import os
from typing import Any

import structlog
from x402.extensions.bazaar import OutputConfig, declare_discovery_extension
from x402.http.facilitator_client import (
    CreateHeadersAuthProvider,
    FacilitatorConfig,
    HTTPFacilitatorClient,
)
from x402.http.utils import decode_payment_signature_header
from x402.schemas import (
    PaymentPayload,
    PaymentRequired,
    PaymentRequirements,
    ResourceInfo,
    SettleResponse,
    VerifyResponse,
)

from api.services.cdp_auth import create_cdp_headers_factory

logger = structlog.get_logger()

MAINNET = "eip155:8453"
BASE_SEPOLIA = "eip155:84532"

# Per-network USDC config. The EIP-712 domain is NOT the same across
# networks — Base mainnet USDC signs as name "USD Coin", Base Sepolia as
# "USDC". Getting it wrong makes every signature fail verification with an
# error that looks like a key problem, so asset and domain are kept together
# here rather than as independent env vars. Values mirror the x402 SDK's
# DEFAULT_ASSETS table (x402.mechanisms.evm.default_assets).
NETWORKS: dict[str, dict[str, Any]] = {
    MAINNET: {
        "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "eip712": {"name": "USD Coin", "version": "2"},
        "is_testnet": False,
        "label": "Base mainnet",
    },
    BASE_SEPOLIA: {
        "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        "eip712": {"name": "USDC", "version": "2"},
        "is_testnet": True,
        "label": "Base Sepolia (testnet)",
    },
}

# Mainnet is the default: a misconfigured network must never silently ask
# real agents to pay in worthless testnet USDC.
NETWORK = os.environ.get("X402_NETWORK", MAINNET).strip() or MAINNET
if NETWORK not in NETWORKS:
    logger.error(
        "x402_unknown_network",
        requested=NETWORK,
        supported=sorted(NETWORKS),
        action="falling back to Base mainnet",
    )
    NETWORK = MAINNET

_NET = NETWORKS[NETWORK]
USDC_ADDRESS: str = _NET["asset"]
USDC_EIP712: dict[str, str] = _NET["eip712"]
IS_TESTNET: bool = _NET["is_testnet"]
NETWORK_LABEL: str = _NET["label"]

if IS_TESTNET:
    logger.warning(
        "x402_testnet_mode",
        network=NETWORK,
        label=NETWORK_LABEL,
        warning="Payments are settled in TESTNET USDC and are worth nothing. "
        "Unset X402_NETWORK before serving real agents.",
    )

# Backwards-compatible alias — some callers imported the mainnet constant.
BASE_NETWORK = NETWORK

# The CDP facilitator serves both Base mainnet and Base Sepolia.
# https://x402.org/facilitator is Base Sepolia only.
DEFAULT_FACILITATOR_URL = "https://api.cdp.coinbase.com/platform/v2/x402"
FACILITATOR_URL = os.environ.get("X402_FACILITATOR_URL", DEFAULT_FACILITATOR_URL)

# Price per scan in USD (fixed). USDC has 6 decimals.
PRICE_PER_SCAN_USD = float(os.environ.get("X402_PRICE_USD", "0.10"))
WALLET_ADDRESS = os.environ.get("X402_WALLET_ADDRESS", "")

RESOURCE_URL = "https://scan.compuute.se/v1/scan/pay"
RESOURCE_DESCRIPTION = (
    "Scan a public GitHub MCP-server repo with compuute-scan. "
    "Returns severity counts, score, top findings, and a triage disclaimer."
)

_facilitator_client: HTTPFacilitatorClient | None = None


def is_x402_configured() -> bool:
    """True iff WALLET_ADDRESS is set."""
    return bool(WALLET_ADDRESS)


def get_facilitator_client() -> HTTPFacilitatorClient:
    """Facilitator client with CDP auth when CDP keys are configured."""
    global _facilitator_client
    if _facilitator_client is None:
        auth_provider = None
        api_key_id = os.environ.get("CDP_API_KEY_ID", "")
        api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "")
        if api_key_id and api_key_secret:
            auth_provider = CreateHeadersAuthProvider(
                create_cdp_headers_factory(api_key_id, api_key_secret, FACILITATOR_URL)
            )
        else:
            logger.warning(
                "x402_facilitator_no_cdp_auth",
                hint="Set CDP_API_KEY_ID/CDP_API_KEY_SECRET — the CDP facilitator "
                "rejects unauthenticated verify/settle on mainnet.",
            )
        _facilitator_client = HTTPFacilitatorClient(
            FacilitatorConfig(url=FACILITATOR_URL, timeout=15.0, auth_provider=auth_provider)
        )
    return _facilitator_client


def build_payment_requirements(price_usd: float | None = None) -> PaymentRequirements:
    """Build x402 v2 payment requirements for one scan."""
    price = price_usd if price_usd is not None else PRICE_PER_SCAN_USD
    return PaymentRequirements(
        scheme="exact",
        network=NETWORK,
        asset=USDC_ADDRESS,
        amount=str(int(price * 1_000_000)),  # USDC has 6 decimals
        pay_to=WALLET_ADDRESS,
        max_timeout_seconds=300,
        extra=dict(USDC_EIP712),
    )


def build_bazaar_extension() -> dict[str, Any]:
    """Bazaar discovery extension declaring how to call POST /v1/scan/pay.

    Facilitators that support the extension (e.g. CDP → Bazaar catalog)
    index the endpoint when a payment carrying this declaration settles.
    """
    extension = declare_discovery_extension(
        input={"repo_url": "https://github.com/modelcontextprotocol/servers"},
        input_schema={
            "properties": {
                "repo_url": {
                    "type": "string",
                    "description": "Public GitHub HTTPS URL of the MCP-server repo to scan.",
                }
            },
            "required": ["repo_url"],
        },
        body_type="json",
        output=OutputConfig(
            example={
                "repo_url": "https://github.com/modelcontextprotocol/servers",
                "score": 0,
                "summary": {"critical": 1, "high": 94, "medium": 22, "low": 0},
                "recommendation": "AVOID — 1 critical and 94 high finding(s)...",
                "_disclaimer": "PATTERN MATCH — not an exploitability claim.",
            }
        ),
    )
    # declare_discovery_extension returns {"bazaar": <model-or-dict>}
    dumped = {
        key: value.model_dump(by_alias=True, exclude_none=True)
        if hasattr(value, "model_dump")
        else value
        for key, value in extension.items()
    }
    # The SDK leaves input.method for runtime enrichment by its own server
    # middleware; we declare it explicitly since the schema requires it.
    dumped["bazaar"]["info"]["input"]["method"] = "POST"
    return dumped


def create_payment_required_response(price_usd: float | None = None) -> dict[str, Any]:
    """Build the 402 Payment Required response body (x402 v2 PaymentRequired)."""
    price = price_usd if price_usd is not None else PRICE_PER_SCAN_USD
    payment_required = PaymentRequired(
        x402_version=2,
        error=f"Payment required: ${price:.4f} USDC per scan",
        resource=ResourceInfo(
            url=RESOURCE_URL,
            description=RESOURCE_DESCRIPTION,
            mime_type="application/json",
        ),
        accepts=[build_payment_requirements(price)],
        extensions=build_bazaar_extension(),
    )
    return payment_required.model_dump(by_alias=True, exclude_none=True)


def decode_payment_header(payment_header: str) -> PaymentPayload | None:
    """Decode the base64 X-Payment header into a v2 PaymentPayload.

    Returns None (fail-closed) on malformed base64/JSON or a v1 payload —
    this endpoint speaks x402 v2 only.
    """
    try:
        payload = decode_payment_signature_header(payment_header)
    except Exception as e:  # noqa: BLE001 — any parse failure is a client error
        logger.warning("x402_payment_header_malformed", error=str(e))
        return None
    if not isinstance(payload, PaymentPayload):
        logger.warning("x402_payment_v1_rejected", got=type(payload).__name__)
        return None
    return payload


async def verify_payment(
    payload: PaymentPayload, price_usd: float | None = None
) -> VerifyResponse:
    """Verify a decoded payment against OUR requirements via the facilitator.

    Fail-closed: network / facilitator errors return is_valid=False.
    """
    requirements = build_payment_requirements(price_usd)
    try:
        result = await get_facilitator_client().verify(payload, requirements)
    except Exception as e:  # noqa: BLE001 — fail closed on any transport error
        logger.warning("x402_verify_failed", error=str(e))
        return VerifyResponse(is_valid=False, invalid_reason="facilitator_error")
    if result.is_valid:
        logger.info("x402_payment_verified", payer=result.payer)
    else:
        logger.warning(
            "x402_payment_invalid",
            reason=result.invalid_reason,
            message=result.invalid_message,
        )
    return result


async def settle_payment(
    payload: PaymentPayload, price_usd: float | None = None
) -> SettleResponse | None:
    """Settle a verified payment via the facilitator.

    Returns the SettleResponse (carrying the on-chain transaction hash), or
    None if settlement errored at the transport level. Settlement failure
    after a successful verify is logged but does not fail the scan response.
    """
    requirements = build_payment_requirements(price_usd)
    try:
        result = await get_facilitator_client().settle(payload, requirements)
    except Exception as e:  # noqa: BLE001 — best-effort, verified already
        logger.warning("x402_settle_failed", error=str(e))
        return None
    if result.success:
        logger.info(
            "x402_payment_settled", transaction=result.transaction, payer=result.payer
        )
    else:
        logger.warning("x402_settle_rejected", reason=result.error_reason)
    return result
