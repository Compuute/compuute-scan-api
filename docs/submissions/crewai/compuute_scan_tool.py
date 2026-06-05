"""CrewAI Tool wrapper for compuute-scan-api.

Drop-in tool for any CrewAI Crew that should perform MCP-server security
pre-flight before connecting to a third-party MCP server.

Local usage (no install required):

    from crewai import Crew, Agent, Task
    from compuute_scan_tool import CompuuteScanTool

    scanner_tool = CompuuteScanTool()
    auditor = Agent(
        role="MCP security pre-flight auditor",
        goal="Block unsafe MCP servers from being installed by the rest of the crew.",
        tools=[scanner_tool],
        verbose=True,
    )
"""
from __future__ import annotations

from typing import ClassVar, Type

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field


class CompuuteScanInput(BaseModel):
    """Input schema for CompuuteScanTool (CrewAI variant)."""

    model_config = ConfigDict(extra="forbid")

    repo_url: str = Field(
        ...,
        description=(
            "Public GitHub HTTPS URL of the MCP server repository to scan. "
            "Must match the pattern https://github.com/<org>/<repo>. "
            "Private repos and non-GitHub hosts are rejected by the upstream API."
        ),
    )


class CompuuteScanTool(BaseTool):
    """CrewAI tool: MCP-specific static security scanner.

    Use this tool BEFORE the rest of the crew installs or connects to a
    third-party MCP server. Returns severity counts, a 0–100 safety
    score, the ten most severe findings (file + line), and a mandatory
    triage disclaimer.

    Source: https://github.com/Compuute/compuute-scan-api
    Methodology: https://github.com/Compuute/compuute-scan-api/blob/main/docs/whitepaper/mcp-security-methodology-v1.md
    Honesty note: pattern detector with ~90% raw FP rate. Treat the
    output as a triage queue, not as confirmed vulnerabilities. The
    `_disclaimer` field in every response says so explicitly.
    """

    name: str = "compuute_scan_mcp_server"
    description: str = (
        "Scan a public GitHub MCP-server repository for security issues. "
        "Use BEFORE installing or connecting to an unknown MCP server. "
        "Input: a GitHub HTTPS URL. Output: severity counts (critical, "
        "high, medium, low), a 0-100 safety score, the top 10 most severe "
        "findings with file and line, scanner version, and a mandatory "
        "triage disclaimer. Median latency 1-2s for small repos. Note: "
        "this is a pattern-detector — findings indicate vulnerable "
        "patterns are present; exploitability requires manual triage. "
        "Free tier, no API key needed."
    )
    args_schema: ClassVar[Type[BaseModel]] = CompuuteScanInput

    # CrewAI doesn't allow extra fields on BaseTool subclasses without
    # subclass-level Config, so we hard-code the endpoint and timeout.
    _ENDPOINT: ClassVar[str] = "https://scan.compuute.se/v1/scan"
    _TIMEOUT: ClassVar[float] = 60.0

    def _run(self, repo_url: str) -> dict:
        """Invoke the scan endpoint and return the structured result."""
        try:
            resp = httpx.post(
                self._ENDPOINT,
                json={"repo_url": repo_url},
                timeout=self._TIMEOUT,
                headers={"User-Agent": "crewai-compuute-scan-tool/1.0"},
            )
        except httpx.RequestError as exc:
            return {"error": "network_error", "message": str(exc)}

        if resp.status_code == 422:
            return {"error": "invalid_input", "message": resp.json().get("detail", "")}
        if resp.status_code == 504:
            return {"error": "scan_timeout", "message": "Scanner exceeded its time budget."}
        if resp.status_code >= 500:
            return {"error": "service_error", "status": resp.status_code}
        if resp.status_code != 200:
            return {"error": f"http_{resp.status_code}", "message": resp.text[:200]}

        return resp.json()
