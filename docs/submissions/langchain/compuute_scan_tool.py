"""LangChain Tool wrapper for compuute-scan-api.

Drop-in tool for any LangChain agent that should perform MCP-security
due diligence before installing or connecting to a third-party MCP server.

Install: this file is a candidate for `langchain-community/tools/`. See
`SUBMISSION.md` in this directory for the proposed PR text.

Local usage (no install required):

    from compuute_scan_tool import CompuuteScanTool
    from langchain.agents import initialize_agent

    tools = [CompuuteScanTool()]
    agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
    agent.run("Should I install https://github.com/foo/mcp-server?")
"""
from __future__ import annotations

from typing import ClassVar, Optional

import httpx
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field


class CompuuteScanInput(BaseModel):
    """Input schema for CompuuteScanTool."""

    model_config = ConfigDict(extra="forbid")

    repo_url: str = Field(
        ...,
        description=(
            "Public GitHub HTTPS URL of the MCP server repository to scan. "
            "Must match the pattern https://github.com/<org>/<repo>. "
            "Private repos and other hosts are rejected."
        ),
    )


class CompuuteScanTool(BaseTool):
    """LangChain tool: MCP-specific static security scanner.

    Use this tool BEFORE your agent installs or connects to a third-party
    MCP server. Returns severity counts, a 0-100 safety score, the ten
    most severe findings with file+line, and a mandatory triage disclaimer.

    The tool is a thin wrapper around compuute-scan-api at
    https://scan.compuute.se/v1/scan. Free tier requires no API key and
    is rate-limited.

    Source: https://github.com/Compuute/compuute-scan-api
    Methodology: https://github.com/Compuute/compuute-scan-api/blob/main/docs/whitepaper/mcp-security-methodology-v1.md
    Honesty note: this is a pattern detector with ~90% raw false-positive
    rate. Every response carries a `_disclaimer` field stating this
    explicitly. See docs/FP-RATES.md for per-rule transparency.
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
    args_schema: ClassVar[type[BaseModel]] = CompuuteScanInput

    # Configurable endpoint — defaults to the hosted instance.
    endpoint: str = "https://scan.compuute.se/v1/scan"
    timeout_seconds: float = 60.0

    def _run(
        self,
        repo_url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict:
        """Invoke the scan endpoint synchronously and return the structured result."""
        try:
            resp = httpx.post(
                self.endpoint,
                json={"repo_url": repo_url},
                timeout=self.timeout_seconds,
                headers={"User-Agent": "langchain-compuute-scan-tool/1.0"},
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

    async def _arun(
        self,
        repo_url: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> dict:
        """Async invocation (preferred in async agent stacks)."""
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                resp = await client.post(
                    self.endpoint,
                    json={"repo_url": repo_url},
                    headers={"User-Agent": "langchain-compuute-scan-tool/1.0"},
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
