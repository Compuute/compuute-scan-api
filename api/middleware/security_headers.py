"""Security headers middleware — OWASP-recommended response headers.

Applied to every response. Configurable but with sensible production defaults.
Notably we do NOT set Cache-Control: no-store globally (unlike lead-enrich-api)
because /v1/scan must remain cacheable for agent consumers — see ARCHITECTURE.md.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers without breaking cache semantics."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # HSTS — 2 years, includeSubDomains.  Railway terminates TLS upstream
        # but adding HSTS at the app level is belt-and-suspenders for proxies.
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains",
        )
        # MIME-sniffing protection
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Clickjacking — we don't serve HTML, but defense-in-depth costs nothing
        response.headers.setdefault("X-Frame-Options", "DENY")
        # Referrer hygiene
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # No browser features needed by an API
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), fullscreen=(), payment=()",
        )
        # CSP — we never serve HTML, so a strict policy is safe
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'",
        )
        return response
