# Changelog

All notable changes to `compuute-scan-api` follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Honesty pin

This scanner is a **pattern-breadth detector with ~90% raw false-positive rate before triage** (validated against `modelcontextprotocol/servers`: 138 raw → 13 confirmed). See [docs/FP-RATES.md](docs/FP-RATES.md) for per-rule transparency. Every API response carries a `_disclaimer` field stating this explicitly. This is by design — we publish broad detection signals and let buyers / agents triage on top.

## [Unreleased]

### Added

- `docs/FP-RATES.md` — per-rule false-positive transparency for the May 2026 batch validation.
- README honesty note above the endpoint table linking to the FP doc.

## [0.4.0] — 2026-05-23

### Added

- Agent + crawler discovery endpoints:
  - `/.well-known/agent.json` (Google A2A Agent Card with skills, pricing, agentSafety)
  - `/.well-known/ai-plugin.json` (OpenAI/ChatGPT plugin manifest)
  - `/robots.txt` and `/sitemap.xml`
- `server.json` for Anthropic MCP Registry submission (`io.github.Compuute/compuute-scan-api`).

### Changed

- Repository flipped to **public** on GitHub for crawler indexing.

## [0.3.0] — 2026-05-23

### Added

- `/v1/scan/pay` — x402 pay-per-scan endpoint (USDC on Base L2). Returns 402 with x402v2 requirements when `X-Payment` header is missing; verifies + scans + settles when present. Free until `X402_WALLET_ADDRESS` env var is set.
- Comprehensive docs: `ARCHITECTURE.md`, `DEVELOPMENT.md`, `STRATEGY.md`, `MONITORING.md`, `agentic-market-submission.md`.
- `scripts/status.sh` — 30-second live health check.

## [0.2.0] — 2026-05-23

### Added

- MCP server at `/mcp/` exposing `scan_mcp_server` tool. Tool description follows Anthropic best practices: WHEN TO USE, WHEN NOT TO USE, EXAMPLES, EXPECTED RESPONSE TIME.
- FastMCP `transport_security.allowed_hosts` explicit allowlist for prod hosts (closes "Invalid Host header" rejection).

## [0.1.0] — 2026-05-22

### Added

- Initial release. `POST /v1/scan` REST endpoint wrapping compuute-scan v0.6.2.
- Strict input validation (GitHub-only HTTPS URLs).
- Idempotency-Key cache (24h).
- ETag + Cache-Control headers.
- X-RateLimit-* headers.
- OpenAPI v3 spec at `/openapi.json`.
- Dockerfile bundling compuute-scan at pinned ref.

[Unreleased]: https://github.com/Compuute/compuute-scan-api/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.4.0
[0.3.0]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.3.0
