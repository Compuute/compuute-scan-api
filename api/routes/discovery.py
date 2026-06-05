"""Agent + crawler discovery endpoints.

Exposes machine-readable capability cards and SEO surfaces so AI agents,
agent-orchestration frameworks, and search engines can find this API
without manual configuration.

  /.well-known/agent.json        — Google A2A Agent Card
  /.well-known/agent-card.json   — alias of agent.json (alternate A2A naming
                                   convention observed in real probes)
  /.well-known/ai-plugin.json    — OpenAI/ChatGPT plugin manifest
  /.well-known/x402.json         — x402 payment-discovery manifest for
                                   x402-aware agents/aggregators
  /.well-known/x402              — alias of x402.json (no-suffix variant
                                   also observed in real probes)
  /robots.txt                    — crawler policy
  /sitemap.xml                   — crawler index
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse, Response

router = APIRouter()

_BASE_URL = "https://scan.compuute.se"


@router.get("/.well-known/agent.json", include_in_schema=False)
async def a2a_agent_card():
    """A2A Agent Card — Google Agent-to-Agent protocol discovery."""
    return JSONResponse({
        "name": "compuute-scan-api",
        "description": (
            "MCP-specific static security scanner for agents. Scan any public "
            "GitHub MCP-server repo and get severity counts, score, top findings, "
            "and a triage disclaimer. 37 L1 rules across TS/JS, Python, Go, Rust, "
            "C#, Java, Kotlin. Threat-intel response cadence: new rules added "
            "within one week of published CVE classes (see compuute-scan v0.6.2's "
            "L1-038 for the Ox Security npx-argument-injection vector)."
        ),
        "url": _BASE_URL,
        "version": "0.3.0",
        "documentationUrl": f"{_BASE_URL}/docs",
        "mcpEndpoint": f"{_BASE_URL}/mcp/",
        "provider": {
            "organization": "Compuute AB",
            "url": "https://compuute.se",
        },
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": False,
            "multiTurn": False,
        },
        "authentication": {
            "schemes": ["none", "x402"],
            "x402Endpoint": f"{_BASE_URL}/v1/scan/pay",
            "freeEndpoint": f"{_BASE_URL}/v1/scan",
        },
        "skills": [
            {
                "id": "scan_mcp_server",
                "name": "Scan MCP server repo",
                "description": (
                    "Clone a public GitHub MCP-server repo and run compuute-scan "
                    "L0+L1 static analysis. Returns severity counts, 0-100 score, "
                    "10 most severe findings, performance metrics, and a triage "
                    "disclaimer. Median latency 1-2s for small repos."
                ),
                "tags": ["security", "mcp", "static-analysis", "supply-chain", "cve"],
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
                "examples": [
                    {
                        "description": "Scan an MCP server you're evaluating",
                        "input": {"repo_url": "https://github.com/modelcontextprotocol/servers"},
                    },
                ],
            }
        ],
        "pricing": {
            "free": "0 USDC — POST /v1/scan, no API key, rate-limited",
            "perScan": "$0.10 USDC on Base L2 — POST /v1/scan/pay with X-Payment header",
            "manualAudit": "$5K-30K — see https://compuute.se/audit",
        },
        "agentSafety": {
            "honestFraming": (
                "Every response carries a _disclaimer field stating that findings "
                "are pattern matches, not exploitability claims. Static analysis "
                "cannot determine whether vulnerable code paths are reachable from "
                "attacker-controlled input."
            ),
            "noCodeExecution": (
                "compuute-scan never executes code from the scanned repo. Files are "
                "read as text and pattern-matched against regex rules."
            ),
            "sandboxing": (
                "Clones live in tempfile.TemporaryDirectory() and are wiped after each scan. "
                "git clone uses --depth 1 --filter=blob:limit=10m with a 60s timeout."
            ),
            "dataMinimization": "No scan results stored server-side. Stateless service.",
            "openSource": "Scanner source: https://github.com/Compuute/compuute-scan (MIT). API source: https://github.com/Compuute/compuute-scan-api (MIT).",
        },
    })


@router.get("/.well-known/agent-card.json", include_in_schema=False)
async def a2a_agent_card_alias():
    """Alias of /.well-known/agent.json.

    Some A2A implementations probe the `-card.json` naming convention
    instead of `agent.json`. Both should return identical content.
    """
    return await a2a_agent_card()


@router.get("/.well-known/x402.json", include_in_schema=False)
@router.get("/.well-known/x402", include_in_schema=False)
async def x402_discovery_manifest():
    """x402 payment-discovery manifest.

    Aggregators (Coinbase Agentic.market crawlers, x402 directory bots)
    probe this path to enumerate the paid endpoints we offer. Returns the
    same shape as a per-endpoint 402 response but listed at the domain
    level so agents can discover priced paths without first triggering a
    402.

    Schema mirrors x402 v2 `accepts` blocks. Each entry is one paid endpoint.
    """
    # Import lazily — x402_service has wallet address / price config baked in.
    from api.services.x402_service import (
        BASE_NETWORK,
        PRICE_PER_SCAN_USD,
        USDC_BASE_ADDRESS,
        WALLET_ADDRESS,
        is_x402_configured,
    )

    endpoints = []
    if is_x402_configured():
        endpoints.append({
            "url": f"{_BASE_URL}/v1/scan/pay",
            "method": "POST",
            "contentType": "application/json",
            "description": (
                "Scan a public GitHub MCP-server repo with compuute-scan. "
                "Returns severity counts, score, top findings, and a triage "
                "disclaimer."
            ),
            "category": "security",
            "tags": ["mcp", "static-analysis", "supply-chain", "cve"],
            "accepts": [{
                "scheme": "exact",
                "network": BASE_NETWORK,
                "asset": USDC_BASE_ADDRESS,
                "amount": str(int(PRICE_PER_SCAN_USD * 1_000_000)),
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300,
            }],
        })

    return JSONResponse({
        "x402Version": 2,
        "provider": {
            "name": "Compuute AB",
            "url": "https://compuute.se",
            "homepage": _BASE_URL,
        },
        "endpoints": endpoints,
        "freeEndpoints": [
            {
                "url": f"{_BASE_URL}/v1/scan",
                "method": "POST",
                "description": "Free-tier scan, no payment required, rate-limited.",
            }
        ],
        "documentation": f"{_BASE_URL}/openapi.json",
    })


@router.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def openai_plugin_manifest():
    """OpenAI / ChatGPT plugin manifest for tool discovery."""
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Compuute MCP Security Scanner",
        "name_for_model": "compuute_scan",
        "description_for_human": (
            "Scan any public GitHub MCP-server repo for security issues before "
            "your agent installs or connects to it."
        ),
        "description_for_model": (
            "Static security scanner specifically tuned for MCP servers. Accepts "
            "a public GitHub URL via POST /v1/scan with body {\"repo_url\": \"...\"}. "
            "Returns severity summary, 0-100 score, top 10 findings with file+line, "
            "and provenance fields (scanner.version, data_source). Covers 37 L1 "
            "rules across TS/JS, Python, Go, Rust, C#, Java, Kotlin. Use BEFORE "
            "installing or connecting to an unknown MCP server. Free tier no auth; "
            "paid tier via x402 at /v1/scan/pay."
        ),
        "auth": {"type": "none"},
        "api": {"type": "openapi", "url": f"{_BASE_URL}/openapi.json"},
        "logo_url": "https://compuute.se/favicon.ico",
        "contact_email": "daniel@compuute.se",
        "legal_info_url": "https://compuute.se",
    })


@router.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Allow: /.well-known/\n"
        "Allow: /openapi.json\n"
        "Allow: /mcp\n"
        "Allow: /v1/health\n"
        "Allow: /v1/scan/info\n"
        "Allow: /v1/scan\n"
        "Allow: /v1/scan/pay\n"
        f"Sitemap: {_BASE_URL}/sitemap.xml\n"
    )
    return PlainTextResponse(content=body)


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    urls = [
        ("/", "weekly", "1.0"),
        ("/.well-known/agent.json", "weekly", "1.0"),
        ("/.well-known/agent-card.json", "weekly", "0.9"),
        ("/.well-known/x402.json", "weekly", "0.9"),
        ("/.well-known/ai-plugin.json", "weekly", "0.9"),
        ("/openapi.json", "weekly", "0.9"),
        ("/docs", "weekly", "0.8"),
        ("/v1/health", "daily", "0.7"),
        ("/v1/scan/info", "weekly", "0.6"),
    ]
    entries = "\n".join(
        "  <url>\n"
        f"    <loc>{_BASE_URL}{path}</loc>\n"
        f"    <changefreq>{freq}</changefreq>\n"
        f"    <priority>{prio}</priority>\n"
        "  </url>"
        for path, freq, prio in urls
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")
