"""MCP server — exposes scan-as-a-service as an agent-callable tool.

Mounted at /mcp/ on the main FastAPI app. Wraps the same scan service used
by the REST endpoint. No auth in this MVP — public free-tier; rate-limited
at the infrastructure layer.

Tool exposed:
  - scan_mcp_server(github_url) → structured findings

Install (Claude Code):
  claude mcp add compuute-scan \\
    --transport http \\
    --url https://scan.compuute.se/mcp/
"""
from __future__ import annotations

import structlog
from mcp.server.fastmcp import Context, FastMCP

from api.services.scan import ScanError, scan_repo

logger = structlog.get_logger()

mcp_app = FastMCP(
    name="compuute-scan",
    instructions=(
        "Scan a public GitHub MCP-server repo with compuute-scan, the MCP-specific "
        "static security scanner (37 L1 rules across TS/JS, Python, Go, Rust, C#, "
        "Java, Kotlin). Use this before an agent connects to an unknown MCP server "
        "or before installing a third-party MCP-server package. Every response "
        "carries a triage disclaimer: findings are pattern matches, not exploitability "
        "claims — manual dataflow review required for production decisions."
    ),
    # Tolerate scanners (Smithery, Anthropic registry crawlers) that skip the
    # notifications/initialized step between handshake and tools/list.
    stateless_http=True,
)

# Mount at /mcp/ root — FastAPI does app.mount("/mcp", mcp_http_app); FastMCP
# default would otherwise resolve to /mcp/mcp/.
mcp_app.settings.streamable_http_path = "/"

# FastMCP's transport-security defaults only allow localhost (DNS-rebinding
# protection). In production behind Railway we must explicitly allow the
# public domains we serve from.
mcp_app.settings.transport_security.allowed_hosts = [
    "scan.compuute.se",
    "scan.compuute.se:*",
    "compuute-scan-api-production.up.railway.app",
    "compuute-scan-api-production.up.railway.app:*",
    # Keep localhost for local dev + healthchecks
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
]
mcp_app.settings.transport_security.allowed_origins = [
    "https://scan.compuute.se",
    "https://compuute-scan-api-production.up.railway.app",
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
]


@mcp_app.tool()
async def scan_mcp_server(ctx: Context, github_url: str) -> dict:
    """Scan a public GitHub MCP-server repository for security issues.

    Clones the repo (shallow, <60s, <200 MB), runs compuute-scan v0.6.2 in
    static analysis mode (no code execution from the target), and returns a
    structured report with severity counts, a 0-100 score, and the 10 most
    severe findings.

    WHEN TO USE:
      - Before connecting to an unknown MCP server discovered via Anthropic
        Registry, Smithery, mcp.so, or a Discord recommendation.
      - Before installing a third-party MCP-server package into a production
        pipeline.
      - As part of an agent's pre-commit / pre-deploy due-diligence step
        when adding new dependencies.
      - As one input to a multi-source trust evaluation (combine with
        publisher reputation, package install count, last-update recency).

    WHEN NOT TO USE:
      - For private repos. Use the on-prem CLI instead:
          `npx compuute-scan ./path-to-private-repo`
      - For deep exploitability assessment of a specific code path. This is
        pattern matching, not dataflow analysis. Book a manual L2-L4 audit
        at https://compuute.se/audit for that depth.
      - For non-GitHub hosts (GitLab, Bitbucket, self-hosted). v1 supports
        github.com only.
      - For repos > 200 MB or clone time > 60s. The endpoint returns a 413
        or 504 in those cases — fall back to local CLI.

    EXPECTED RESPONSE TIME:
      - Median: ~1-2 seconds for small repos (<100 files).
      - p99: ~10 seconds for medium repos.
      - Hard timeout at clone=60s, scan=120s combined.

    EXPECTED COST:
      - Free tier in MVP. Future Pro tier may charge per-scan or per-month.

    DATA FRESHNESS:
      - Scanner version is reported in response.scanner.version.
      - L1 rule set freshness reflects compuute-scan releases — see
        github.com/Compuute/compuute-scan/CHANGELOG.md for the latest CVE
        and threat-intel response timeline.

    EXAMPLES:

      Example 1 — scan an MCP server you're evaluating:
        github_url = "https://github.com/modelcontextprotocol/servers"
        → score: 0, summary: {critical: 1, high: 94, medium: 22}
        → top_findings include SSRF, eval, etc.
        → recommendation: "AVOID — 1 critical and 94 high finding(s)..."

      Example 2 — scan a clean reference implementation:
        github_url = "https://github.com/microsoft/azure-devops-mcp"
        → score: 90+, summary: {critical: 0, high: 1}
        → recommendation: "REVIEW — 1 high finding(s)..."

      Example 3 — scan your own dev MCP-server before publishing:
        github_url = "https://github.com/yourorg/your-mcp"
        → audit your own surface before others install it

    OUTPUT FIELDS (stable schema):
      - repo_url (str): canonical URL of the scanned repo.
      - score (int): 0-100, higher safer. Coarse summary, not a precision claim.
      - summary (object): {critical, high, medium, low, info, files_scanned}.
      - recommendation (str): action guidance derived from severity counts.
      - findings_count (int): total raw findings (may include false positives).
      - top_findings (list): up to 10 most severe, each with {id, title,
        severity, file, line, owasp, cwe}.
      - l0_discovery (object): MCP transport, tool count, dependency pinning.
      - performance (object): clone_seconds, scan_seconds, repo_size_bytes.
      - scanner (object): {name, version, layers_covered}.
      - _disclaimer (str): MANDATORY triage disclaimer. Read it.

    Args:
      github_url: Public GitHub HTTPS URL (e.g. https://github.com/org/repo).
                  Must be public and < 200 MB. v1 is github.com only.

    Returns:
      Structured scan result. On error, returns {"error": code, "message": ...}
      with HTTP-style code (invalid_url, clone_failed, scan_timeout, etc.).
    """
    try:
        return scan_repo(github_url)
    except ScanError as e:
        logger.warning("mcp_scan_failed", code=e.code, repo=github_url)
        return {"error": e.code, "message": e.message}
    except Exception as e:  # noqa: BLE001
        logger.error("mcp_scan_unhandled", repo=github_url, error=str(e))
        return {"error": "internal_error", "message": str(e)}


# Streamable HTTP app to mount under FastAPI.
mcp_http_app = mcp_app.streamable_http_app()
