"""compuute-scan-api — agent-callable HTTP+MCP wrapper around compuute-scan.

Exposes:
  POST /v1/scan       — scan a public GitHub MCP-server repo
  GET  /v1/scan/info  — scanner capabilities + limits
  GET  /v1/health     — liveness
  GET  /openapi.json  — machine-readable spec (for agent discovery)
  /mcp/               — Streamable HTTP MCP server (tool: scan_mcp_server)

Wraps compuute-scan v0.6.2 (37 MCP-specific L1 rules, 8 languages).
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import scan, scan_x402

logger = structlog.get_logger()

# Load MCP with graceful degradation — REST works without it.
try:
    from api.mcp_server import mcp_app as _mcp_app, mcp_http_app
    _mcp_available = True
except Exception as _e:  # noqa: BLE001
    _mcp_app = None
    mcp_http_app = None
    _mcp_available = False
    logger.warning("mcp_server_unavailable", error=str(_e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start FastMCP's session manager so /mcp/ requests succeed."""
    if _mcp_available and _mcp_app is not None:
        async with _mcp_app.session_manager.run():
            logger.info("mcp_session_manager_started")
            yield
    else:
        yield


app = FastAPI(
    title="compuute-scan-api",
    description=(
        "HTTP + MCP wrapper around compuute-scan, the MCP-specific static "
        "security scanner. Designed for agent-callable consumption: "
        "idempotent retries, cache headers, OpenAPI spec, MCP tool exposure."
    ),
    version="0.3.0",
    contact={"name": "Compuute AB", "url": "https://compuute.se", "email": "daniel@compuute.se"},
    license_info={"name": "MIT", "url": "https://github.com/Compuute/compuute-scan-api/blob/main/LICENSE"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/v1", tags=["scan"])
app.include_router(scan_x402.router, prefix="/v1", tags=["scan-x402"])


@app.get("/v1/health", tags=["health"])
async def health():
    """Liveness probe + scanner-binary check."""
    from api.services.scan import COMPUUTE_SCAN_PATH
    return {
        "status": "operational",
        "version": app.version,
        "scanner_available": COMPUUTE_SCAN_PATH.exists(),
        "scanner_path": str(COMPUUTE_SCAN_PATH),
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "compuute-scan-api",
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "mcp_endpoint": "/mcp/" if _mcp_available else None,
        "homepage": "https://compuute.se",
    }


# Mount the MCP server now that lifespan above will start its session manager.
if _mcp_available and mcp_http_app is not None:
    app.mount("/mcp", mcp_http_app)
    logger.info("mcp_server_mounted")
