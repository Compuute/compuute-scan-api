"""POST /v1/scan/pay — pay-per-scan via x402 micropayments. No API key required.

Agents pay $0.10 (configurable) in USDC on Base L2 per scan. The 402 body is
x402 v2 PaymentRequired and carries the Bazaar discovery extension, so
facilitators that support it (CDP → Bazaar catalog) index this endpoint when
the first payment settles.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

from api.serializers.scan_serializer import ScanRequest, ScanResponse
from api.services.scan import ScanError, scan_repo
from api.services.x402_service import (
    PRICE_PER_SCAN_USD,
    create_payment_required_response,
    decode_payment_header,
    is_x402_configured,
    settle_payment,
    verify_payment,
)
from x402.http.utils import encode_payment_response_header

logger = structlog.get_logger()
router = APIRouter()


def _payment_required(extra: dict | None = None) -> JSONResponse:
    """402 with x402 v2 PaymentRequired body (+ optional error fields)."""
    body = create_payment_required_response()
    if extra:
        body = {**extra, **body}
    return JSONResponse(
        status_code=402,
        content=body,
        headers={"X-Payment-Protocol": "x402"},
    )


@router.post(
    "/scan/pay",
    response_model=ScanResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_200_OK,
    summary="Pay-per-scan via x402 (no API key required)",
    description=(
        "Agent-callable scan endpoint billed per-call via x402 micropayments on "
        f"Base L2 USDC. Current price: ${PRICE_PER_SCAN_USD:.2f} per scan.\n\n"
        "**Flow (x402 v2):**\n"
        "1. POST without `X-Payment` header → 402 with x402 payment requirements.\n"
        "2. Agent signs the payment (EIP-3009 USDC transfer) per the `accepts` entry.\n"
        "3. POST with `X-Payment: <base64 PaymentPayload>` header → server verifies "
        "via the facilitator, runs the scan, settles, and returns the result with a "
        "`PAYMENT-RESPONSE` header containing the settlement receipt.\n\n"
        "**When NOT to use:** if the free tier suffices, use `/v1/scan` "
        "instead. This endpoint is for agents paying autonomously."
    ),
    responses={
        200: {"description": "Scan completed successfully."},
        402: {"description": "Payment required. Body is an x402 v2 PaymentRequired object."},
        413: {"description": "Repo exceeds size limit."},
        422: {"description": "Invalid GitHub URL or repo not found."},
        503: {"description": "x402 not configured on this server."},
    },
)
async def scan_with_x402(
    payload: ScanRequest,
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

    # No payment header → 402 with requirements + Bazaar discovery extension.
    if not x_payment:
        return _payment_required()

    # Decode the base64 PaymentPayload from the header (fail-closed).
    payment = decode_payment_header(x_payment)
    if payment is None:
        return _payment_required(
            {"code": "x402_malformed_payment", "message": "X-Payment header is not a valid x402 v2 payload."}
        )

    # Verify against OUR requirements via the facilitator.
    verification = await verify_payment(payment)
    if not verification.is_valid:
        return _payment_required(
            {
                "code": "x402_invalid_payment",
                "message": verification.invalid_message
                or f"Invalid or insufficient x402 payment ({verification.invalid_reason}).",
            }
        )

    # Run the scan.
    try:
        result = scan_repo(payload.repo_url)
    except ScanError as e:
        logger.warning("scan_x402_failed", code=e.code, repo=payload.repo_url)
        return JSONResponse(
            status_code=e.http_status,
            content={"code": e.code, "message": e.message},
        )

    # Settle. Failure after successful verify is logged, not fatal to the scan.
    settlement = await settle_payment(payment)

    headers = {"X-Payment-Protocol": "x402"}
    if settlement is not None:
        receipt = encode_payment_response_header(settlement)
        headers["PAYMENT-RESPONSE"] = receipt
        headers["X-PAYMENT-RESPONSE"] = receipt  # v1-style alias some clients read

    logger.info(
        "scan_x402_complete",
        repo=payload.repo_url,
        score=result["score"],
        critical=result["summary"]["critical"],
        high=result["summary"]["high"],
        payer=verification.payer,
    )
    return JSONResponse(status_code=200, content=result, headers=headers)
