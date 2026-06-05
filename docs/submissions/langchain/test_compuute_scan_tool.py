"""Tests for the LangChain CompuuteScanTool wrapper."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from compuute_scan_tool import CompuuteScanTool, CompuuteScanInput


def test_tool_metadata_matches_langchain_conventions():
    """Tool name + description must be present and stable."""
    t = CompuuteScanTool()
    assert t.name == "compuute_scan_mcp_server"
    assert "Scan a public GitHub MCP-server" in t.description
    assert "BEFORE installing" in t.description
    assert "free tier" in t.description.lower()


def test_input_schema_rejects_extra_fields():
    """Buyer-agents probe schemas; extra fields must be rejected."""
    with pytest.raises(Exception):
        CompuuteScanInput(repo_url="https://github.com/o/r", extra="x")


def test_input_schema_accepts_valid_url():
    """A normal GitHub URL passes validation at the input layer."""
    inp = CompuuteScanInput(repo_url="https://github.com/Compuute/compuute-scan")
    assert inp.repo_url == "https://github.com/Compuute/compuute-scan"


def test_run_returns_dict_on_200():
    """Happy path: 200 → returns the parsed JSON dict from the endpoint."""
    t = CompuuteScanTool()
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "score": 92,
        "summary": {"critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0, "files_scanned": 10},
        "_disclaimer": "PATTERN MATCH...",
    }
    with patch("compuute_scan_tool.httpx.post", return_value=fake_response):
        out = t._run("https://github.com/Compuute/compuute-scan")
    assert out["score"] == 92
    assert "_disclaimer" in out


def test_run_returns_invalid_input_on_422():
    """422 from server propagates as a structured error, not an exception."""
    t = CompuuteScanTool()
    fake_response = MagicMock()
    fake_response.status_code = 422
    fake_response.json.return_value = {"detail": "Only public GitHub URLs accepted"}
    with patch("compuute_scan_tool.httpx.post", return_value=fake_response):
        out = t._run("http://localhost")
    assert out["error"] == "invalid_input"


def test_run_returns_scan_timeout_on_504():
    """504 propagates as a structured timeout error."""
    t = CompuuteScanTool()
    fake_response = MagicMock()
    fake_response.status_code = 504
    with patch("compuute_scan_tool.httpx.post", return_value=fake_response):
        out = t._run("https://github.com/big/repo")
    assert out["error"] == "scan_timeout"


def test_run_returns_network_error_on_exception():
    """A RequestError (DNS, refused, etc.) returns a structured error."""
    import httpx
    t = CompuuteScanTool()
    with patch("compuute_scan_tool.httpx.post", side_effect=httpx.ConnectError("boom")):
        out = t._run("https://github.com/o/r")
    assert out["error"] == "network_error"
