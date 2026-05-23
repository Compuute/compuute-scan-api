"""POST /v1/scan/pay — pay-per-scan via x402 micropayments. No API key required.

Agents pay $0.10 (configurable) in USDC on Base L2 per scan. This is the
endpoint that Coinbase Agentic.market's CDP Facilitator can auto-discover
and index once the first payment is processed.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from api.serializers.scan_serializer import ScanRequest, ScanResponse
from api.services.scan import ScanError, scan_repo
from api.services.x402_service import (
    PRICE_PER_SCAN_USD,
    create_payment_required_response,
    is_x402_configured,
    settle_payment,
    verify_payment,
)

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/scan/pay",
    response_model=ScanResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Pay-per-scan via x402 (no API key required)",
    description=(
        "Agent-callable scan endpoint billed per-call via x402 micropayments on "
        f"Base L2 USDC. Current price: ${PRICE_PER_SCAN_USD:.2f} per scan.\n\n"
        "**Flow:**\n"
        "1. POST without `X-Payment` header → 402 with x402 payment requirements.\n"
        "2. Agent pays via x402 facilitator (Coinbase) and obtains a signed receipt.\n"
        "3. POST with `X-Payment: <receipt>` header → server verifies, runs the scan, returns result.\n\n"
        "**When NOT to use:** if you already have a free-tier API key, use `/v1/scan` "
        "instead. This endpoint is for agents without accounts."
    ),
    responses={
        200: {"description": "Scan completed successfully."},
        402: {"description": "Payment required. Body contains x402 requirements."},
        413: {"description": "Repo exceeds size limit."},
        422: {"description": "Invalid GitHub URL or repo not found."},
        503: {"description": "x402 not configured on this server."},
    },
)
async def scan_with_x402(
    payload: ScanRequest,
    request: Request,
    x_payment: str | None = Header(default=None, alias="X-Payment"),
):
    """Scan with x402 micropayment."""
    if not is_x402_configured():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "code": "x402_not_configured",
                "message": "x402 payments not configured (X402_WALLET_ADDRESS not set).",
            },
        )

    # No payment header → return 402 with requirements (Agentic.market auto-indexes here)
    if not x_payment:
        body = create_payment_required_response()
        return JSONResponse(
            status_code=402,
            content=body,
            headers={"X-Payment-Protocol": "x402"},
        )

    # Verify payment with facilitator
    is_valid = await verify_payment(x_payment)
    if not is_valid:
        return JSONResponse(
            status_code=402,
            content={
                "code": "x402_invalid_payment",
                "message": "Invalid or insufficient x402 payment.",
                **create_payment_required_response(),
            },
            headers={"X-Payment-Protocol": "x402"},
        )

    # Run the scan
    try:
        result = scan_repo(payload.repo_url)
    except ScanError as e:
        logger.warning("scan_x402_failed", code=e.code, repo=payload.repo_url)
        return JSONResponse(
            status_code=e.http_status,
            content={"code": e.code, "message": e.message},
        )

    # Best-effort settlement (facilitator may auto-settle on verify)
    await settle_payment(x_payment)

    logger.info(
        "scan_x402_complete",
        repo=payload.repo_url,
        score=result["score"],
        critical=result["summary"]["critical"],
        high=result["summary"]["high"],
    )
    return result
