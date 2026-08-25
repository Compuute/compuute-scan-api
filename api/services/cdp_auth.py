"""Minimal CDP (Coinbase Developer Platform) API auth for the x402 facilitator.

The mainnet x402 facilitator (https://api.cdp.coinbase.com/platform/v2/x402)
requires CDP API-key JWTs on /verify and /settle. The official `cdp-sdk`
implements this but drags in web3 + solana; this module replicates only the
JWT scheme (verified against cdp-sdk 1.48.0, cdp/auth/utils/jwt.py) using
PyJWT + cryptography.

Supported key formats — both of what CDP issues:
  - EC private key in PEM  → ES256
  - Ed25519 key as base64 (64 bytes: seed + public key) → EdDSA

Env vars:
  CDP_API_KEY_ID
  CDP_API_KEY_SECRET
"""
from __future__ import annotations

import base64
import random
import time

import jwt as pyjwt
import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

logger = structlog.get_logger()

_JWT_TTL_SECONDS = 120


def _parse_private_key(key_data: str) -> ec.EllipticCurvePrivateKey | ed25519.Ed25519PrivateKey:
    """Parse a CDP API key secret (PEM EC key or base64 Ed25519 key).

    CDP issues either format, so a failure to parse as one is expected, not
    an error — only failing both is fatal. Never log the key material itself.
    """
    # Env vars often carry literal \n sequences instead of newlines.
    if "\\n" in key_data:
        key_data = key_data.replace("\\n", "\n")

    try:
        key = serialization.load_pem_private_key(key_data.encode(), password=None)
        if isinstance(key, ec.EllipticCurvePrivateKey):
            return key
    except Exception as e:  # noqa: BLE001 — fall through to the Ed25519 attempt
        logger.debug("cdp_key_not_pem_ec", error=str(e))

    try:
        decoded = base64.b64decode(key_data)
        if len(decoded) == 64:
            # Ed25519: first 32 bytes are the seed, last 32 the public key.
            return ed25519.Ed25519PrivateKey.from_private_bytes(decoded[:32])
    except Exception as e:  # noqa: BLE001 — both formats failed; raise below
        logger.debug("cdp_key_not_base64_ed25519", error=str(e))

    raise ValueError("CDP_API_KEY_SECRET must be a PEM EC key or a base64 Ed25519 key")


def generate_cdp_jwt(
    api_key_id: str,
    api_key_secret: str,
    request_method: str,
    request_host: str,
    request_path: str,
) -> str:
    """Generate a CDP REST-API bearer JWT for one request."""
    private_key = _parse_private_key(api_key_secret)
    algorithm = "ES256" if isinstance(private_key, ec.EllipticCurvePrivateKey) else "EdDSA"

    now = int(time.time())
    header = {
        "alg": algorithm,
        "kid": api_key_id,
        "typ": "JWT",
        "nonce": "".join(random.choices("0123456789", k=16)),
    }
    claims = {
        "sub": api_key_id,
        "iss": "cdp",
        "aud": None,
        "nbf": now,
        "exp": now + _JWT_TTL_SECONDS,
        "uris": [f"{request_method} {request_host}{request_path}"],
    }
    return pyjwt.encode(claims, private_key, algorithm=algorithm, headers=header)


def create_cdp_headers_factory(api_key_id: str, api_key_secret: str, facilitator_url: str):
    """Return a create_headers callable in the shape CreateHeadersAuthProvider expects.

    Produces per-endpoint auth headers for the facilitator's /verify and
    /settle routes, matching cdp-sdk's create_cdp_auth_headers output.
    """
    # facilitator_url is e.g. https://api.cdp.coinbase.com/platform/v2/x402
    stripped = facilitator_url.replace("https://", "").replace("http://", "")
    host, _, base_path = stripped.partition("/")
    base_path = f"/{base_path}" if base_path else ""

    def _headers_for(path_suffix: str, method: str) -> dict[str, str]:
        token = generate_cdp_jwt(
            api_key_id,
            api_key_secret,
            request_method=method,
            request_host=host,
            request_path=f"{base_path}{path_suffix}",
        )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Correlation-Context": "sdk_language=python,source=compuute-scan-api",
        }

    def _create_headers() -> dict[str, dict[str, str]]:
        return {
            "verify": _headers_for("/verify", "POST"),
            "settle": _headers_for("/settle", "POST"),
            "supported": _headers_for("/supported", "GET"),
            "list": {},
        }

    return _create_headers
