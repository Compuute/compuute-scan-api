# compuute-scan-api

**Scan-as-a-Service for MCP servers.** HTTP + MCP wrapper around [compuute-scan](https://github.com/Compuute/compuute-scan) — the MCP-specific static security scanner. Designed for agent-callable consumption.

POST a public GitHub repo URL → get a structured security report scored against 37 MCP-specific rules across 8 languages (TS/JS, Python, Go, Rust, C#, Java, Kotlin).

> **Honesty note (read first):** compuute-scan is a **pattern-breadth detector**, not an exploitability oracle. Historic false-positive rate after manual validation is **~90% on raw output** (verified against [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers): 138 raw findings → 13 confirmed). Every response carries a `_disclaimer` field stating this explicitly. Use findings as a triage queue, not as a list of confirmed vulnerabilities. See [docs/FP-RATES.md](docs/FP-RATES.md) for per-rule transparency.

Live at <https://scan.compuute.se>. Service version reported by `/v1/health`.

---

## Endpoints

### Core scan

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/v1/scan` | Scan a public GitHub MCP-server repo (free tier, rate-limited) | none |
| POST | `/v1/scan/pay` | Same as above via [x402](https://www.x402.org/) micropayment ($0.10 USDC on Base L2) | `X-Payment` header |
| GET | `/v1/scan/info` | Scanner version + limits + supported ecosystems | none |
| GET | `/v1/health` | Liveness + scanner-binary availability | none |

### Machine-readable contracts

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/openapi.json` | OpenAPI v3 spec with per-field descriptions |
| GET | `/docs` | Swagger UI for the OpenAPI spec |

### MCP server (live)

| Endpoint | Tool | Transport |
|----------|------|-----------|
| `/mcp/` | `scan_mcp_server(github_url)` | Streamable HTTP |

Install in Claude Code: `claude mcp add compuute-scan --transport http --url https://scan.compuute.se/mcp/`

### Discovery (`/.well-known/`)

| Path | Format | Consumer |
|------|--------|----------|
| `/.well-known/agent.json` | A2A Agent Card | Google A2A protocol |
| `/.well-known/agent-card.json` | A2A Agent Card (alias) | A2A clients using `-card.json` naming |
| `/.well-known/ai-plugin.json` | OpenAI plugin manifest | ChatGPT / OpenAI tools |
| `/.well-known/x402.json` | x402 payment manifest | Coinbase Agent.market crawlers, x402 aggregators |
| `/.well-known/x402` | Alias of `x402.json` | x402 probes without `.json` suffix |
| `/llms.txt` | markdown summary | LLM-driven agent-search crawlers (Exa, Perplexity-style) per [llmstxt.org](https://llmstxt.org) |
| `/robots.txt` | crawler policy | search engines |
| `/sitemap.xml` | URL index | search engines |

### Example

```bash
curl -X POST https://scan.compuute.se/v1/scan \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 00000000-0000-0000-0000-000000000001' \
  -d '{"repo_url": "https://github.com/modelcontextprotocol/servers"}'
```

Response (truncated):

```json
{
  "repo_url": "https://github.com/modelcontextprotocol/servers",
  "scanner": {"name": "compuute-scan", "version": "0.6.2", "layers_covered": ["L0", "L1"]},
  "summary": {"critical": 1, "high": 94, "medium": 22, "low": 0, "files_scanned": 77},
  "score": 0,
  "recommendation": "AVOID — 1 critical and 94 high finding(s)...",
  "top_findings": [...],
  "performance": {"clone_seconds": 1.2, "scan_seconds": 0.5, "repo_size_bytes": 41234},
  "_disclaimer": "PATTERN MATCH — compuute-scan is a static analyzer..."
}
```

## Agent-shaped API features

| Feature | How |
|---------|-----|
| Idempotent retries (24h cache) | `Idempotency-Key` header |
| HTTP cache | `ETag` + `Cache-Control: public, max-age=1800` |
| Conditional GET | `If-None-Match` → 304 Not Modified |
| Rate-limit headers | `X-RateLimit-Limit/Remaining/Reset` |
| Strict input validation | Pydantic `extra="forbid"`, GitHub-HTTPS-only |
| OWASP security headers | HSTS / X-Frame-Options / X-Content-Type-Options / CSP / Referrer-Policy / Permissions-Policy |
| OpenAPI for discovery | `GET /openapi.json` with descriptions on every field |
| MCP for agent discovery | `/mcp/` exposes `scan_mcp_server` tool |
| x402 for autonomous purchase | `/v1/scan/pay` returns 402 with USDC/Base payment requirements |
| Honest framing | Every response carries `_disclaimer` — pattern match, not exploitability claim |

## Pricing

| Tier | Audience | Price |
|------|----------|-------|
| Open Source CLI | Indie devs, agent builders | $0 — `npx compuute-scan ./repo` |
| Hosted API (free) | Agent operators evaluating MCP servers | $0 — `POST /v1/scan`, rate-limited |
| Hosted API (x402) | Autonomous agents in Agent.market ecosystem | $0.10 USDC/scan — `POST /v1/scan/pay` |
| MCP Security Audit | Enterprises shipping MCP to production | $5K–$30K SoW |
| AI Procurement Risk Audit | CFO/CTO/CISO buying enterprise AI capacity | $5K–$15K SoW |

Full breakdown with JSON-LD: <https://compuute.se/pricing>.

## Local development

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export COMPUUTE_SCAN_PATH=$HOME/compuute-scan/compuute-scan.js
uvicorn main:app --reload
```

## Tests

```bash
pytest tests/ -v
# 34 tests covering scan, x402, MCP, discovery, OpenAPI
```

## Scripts

| Script | What it does |
|--------|-------------|
| `scripts/precheck.sh` | Start-of-session check: branch, working tree, tests, live state, next backlog item |
| `scripts/postcheck.sh` | End-of-session check: committer hygiene, tests, append to `docs/PROGRESS.md` |
| `scripts/status.sh` | 30-second live-state check against scan.compuute.se (4 probes) |
| `scripts/sbom.sh` | Generate CycloneDX SBOM, optionally upload to a GitHub Release |
| `scripts/prospect-research.sh` | Pull qualified prospects from GitHub + Anthropic Registry, draft DM angles |
| `scripts/measure-tiers.sh` | T0/T1/T2 distribution snapshot per [docs/agent-economy-strategy.md](docs/agent-economy-strategy.md) §5 — reach, engagement, conversion measured against Railway logs + Base RPC + GitHub stars |

## Architecture

- `api/services/scan.py` — clone + sandbox + scan + parse. Pure functions.
- `api/services/x402_service.py` — x402 verify / settle via Coinbase facilitator.
- `api/serializers/scan_serializer.py` — Pydantic models, strict validation.
- `api/routes/scan.py` — HTTP layer for `/v1/scan`: idempotency, cache, ETag.
- `api/routes/scan_x402.py` — HTTP layer for `/v1/scan/pay`.
- `api/routes/discovery.py` — `/.well-known/*`, `/robots.txt`, `/sitemap.xml`.
- `api/mcp_server.py` — FastMCP server exposing `scan_mcp_server`.
- `main.py` — FastAPI wiring + middleware (security headers, CORS).

Bundled compuute-scan version is pinned in the Dockerfile (`ARG COMPUUTE_SCAN_REF=v0.6.2`).

## Documentation

| Doc | For |
|-----|-----|
| [docs/agent-economy-strategy.md](docs/agent-economy-strategy.md) | The strategic doc — a16z-verified data, the 11-signal buyer-agent model, two-track strategy, 30-day pivot trigger. Read first if you're trying to understand the company. |
| [docs/STRATEGY.md](docs/STRATEGY.md) | Position, pricing tiers, roadmap, decision log |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Component diagram, request flow, threat model, deployment topology |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local setup, layout, code style, common pitfalls — onboard a new dev in 30 min |
| [docs/MONITORING.md](docs/MONITORING.md) | Endpoints to watch, automated checks, runbook for failures |
| [docs/FP-RATES.md](docs/FP-RATES.md) | Per-rule false-positive transparency |
| [docs/scan-self-triage.md](docs/scan-self-triage.md) | What this scanner reports when run against its own code |
| [docs/whitepaper/](docs/whitepaper/) | MCP Security Methodology v1.0 (Markdown + PDF) |
| [docs/case-studies/](docs/case-studies/) | Three anonymized engagement reports from the May 2026 batch |
| [docs/advisories/](docs/advisories/) | Public advisories under the `COMPUUTE-YYYY-NNN` numbering |
| [docs/security/](docs/security/) | Self-pentest reports (90-day cadence) |
| [docs/audits/](docs/audits/) | The AI Procurement Risk Audit checklist (lead magnet) |
| [docs/compliance/](docs/compliance/) | SOC 2 Type I readiness statement, TSC control mapping |
| [docs/submissions/](docs/submissions/) | LangChain + CrewAI tool wrappers ready for PR/marketplace |
| [skills/compuute-scan/](skills/compuute-scan/) | Claude Skill package (SKILL.md + scan.sh) — submitted to [anthropics/skills#1346](https://github.com/anthropics/skills/pull/1346) |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Contributor Covenant 2.1 |
| [docs/launches/](docs/launches/) | Show HN draft + posting checklist |
| [docs/setup/](docs/setup/) | Status page (BetterStack) + analytics (PostHog) setup guides |
| [docs/agentic-market-submission.md](docs/agentic-market-submission.md) | Three paths to Coinbase Agent.market listing |
| [BACKLOG.md](BACKLOG.md) | GitHub Issues + Project board roadmap |
| [IDEAS.md](IDEAS.md) | Composted product hypotheses with gating rules |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [SECURITY.md](SECURITY.md) | Vulnerability disclosure policy (90-day window) |

## Security

Found a vulnerability? See [SECURITY.md](SECURITY.md) — email `security@compuute.se`. We follow a 90-day coordinated disclosure window.

## License

MIT (matches compuute-scan).

## Author

Compuute AB — `daniel@compuute.se`
