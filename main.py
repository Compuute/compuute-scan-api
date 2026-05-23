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

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import scan

logger = structlog.get_logger()

app = FastAPI(
    title="compuute-scan-api",
    description=(
        "HTTP + MCP wrapper around compuute-scan, the MCP-specific static "
        "security scanner. Designed for agent-callable consumption: "
        "idempotent retries, cache headers, OpenAPI spec, MCP tool exposure."
    ),
    version="0.1.0",
    contact={"name": "Compuute AB", "url": "https://compuute.se", "email": "daniel@compuute.se"},
    license_info={"name": "MIT", "url": "https://github.com/Compuute/compuute-scan-api/blob/main/LICENSE"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/v1", tags=["scan"])


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
        "mcp_endpoint": "/mcp/",
        "homepage": "https://compuute.se",
    }
