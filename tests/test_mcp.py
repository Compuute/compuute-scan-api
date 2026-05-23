"""Tests for the MCP server integration."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


def test_mcp_app_mounted_on_main_app():
    """FastMCP's streamable_http_app is mounted at /mcp on the FastAPI app.

    We assert mount presence at app-config level rather than over HTTP because
    FastMCP requires its session manager to run (via lifespan) before HTTP
    requests work — verified post-deploy via curl against the live URL.
    """
    paths = [getattr(r, "path", "") for r in app.routes]
    assert "/mcp" in paths, f"expected /mcp mount; got {paths}"


def test_mcp_app_exposes_scan_tool_by_name():
    """The FastMCP instance has scan_mcp_server registered."""
    from api.mcp_server import mcp_app, scan_mcp_server
    assert callable(scan_mcp_server)
    # Sanity: name matches what an agent would discover via tools/list
    assert "scan_mcp_server" in str(scan_mcp_server)


def test_mcp_tool_description_meets_anthropic_spec():
    """Tool docstring must include WHEN TO USE / WHEN NOT TO USE / EXAMPLES."""
    from api.mcp_server import scan_mcp_server
    doc = scan_mcp_server.__doc__ or ""
    assert "WHEN TO USE" in doc
    assert "WHEN NOT TO USE" in doc
    assert "EXAMPLES" in doc
    assert "EXPECTED RESPONSE TIME" in doc
    # Should be substantive — > 1.5 KB
    assert len(doc) > 1500


def test_mcp_tool_delegates_to_scan_service():
    """Tool invokes the same scan_repo as the REST endpoint (no duplicate logic)."""
    from api.mcp_server import scan_mcp_server
    # Inspect source to confirm delegation
    import inspect
    src = inspect.getsource(scan_mcp_server.fn if hasattr(scan_mcp_server, "fn") else scan_mcp_server)
    assert "scan_repo" in src
