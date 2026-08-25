"""Tests for the minimal CDP facilitator JWT auth."""
from __future__ import annotations

import jwt as pyjwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from api.services.cdp_auth import create_cdp_headers_factory, generate_cdp_jwt


def _ec_key_pem() -> str:
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()


def test_generate_cdp_jwt_es256_shape():
    token = generate_cdp_jwt(
        "test-key-id", _ec_key_pem(), "POST", "api.cdp.coinbase.com", "/platform/v2/x402/verify"
    )
    header = pyjwt.get_unverified_header(token)
    assert header["alg"] == "ES256"
    assert header["kid"] == "test-key-id"
    assert len(header["nonce"]) == 16
    claims = pyjwt.decode(token, options={"verify_signature": False})
    assert claims["iss"] == "cdp"
    assert claims["sub"] == "test-key-id"
    assert claims["uris"] == ["POST api.cdp.coinbase.com/platform/v2/x402/verify"]
    assert claims["exp"] - claims["nbf"] == 120


def test_create_headers_factory_covers_verify_and_settle():
    factory = create_cdp_headers_factory(
        "test-key-id", _ec_key_pem(), "https://api.cdp.coinbase.com/platform/v2/x402"
    )
    headers = factory()
    assert headers["verify"]["Authorization"].startswith("Bearer ")
    assert headers["settle"]["Authorization"].startswith("Bearer ")
    verify_claims = pyjwt.decode(
        headers["verify"]["Authorization"].removeprefix("Bearer "),
        options={"verify_signature": False},
    )
    assert verify_claims["uris"] == ["POST api.cdp.coinbase.com/platform/v2/x402/verify"]
