# Changelog

All notable changes to `compuute-scan-api` follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Honesty pin

This scanner is a **pattern-breadth detector with ~90% raw false-positive rate before triage** (validated against `modelcontextprotocol/servers`: 138 raw → 13 confirmed). See [docs/FP-RATES.md](docs/FP-RATES.md) for per-rule transparency. Every API response carries a `_disclaimer` field stating this explicitly. This is by design — we publish broad detection signals and let buyers / agents triage on top.

## [Unreleased]

## [0.5.1] — 2026-08-25

### Added

- **`X402_NETWORK`** — selects the payment network by CAIP-2 id. Defaults to
  `eip155:8453` (Base mainnet); set `eip155:84532` to rehearse the full
  payment chain on Base Sepolia with free testnet USDC. The CDP facilitator
  serves both, so a testnet run exercises the real CDP API-key auth path.
- `/v1/health` now reports an `x402` block (`enabled`, `network`,
  `network_label`, `testnet`), so the active payment mode is visible in one
  fetch instead of requiring someone to read the deployed env vars.
- Seven tests covering network selection, including a regression guard that
  the two networks' EIP-712 domains never converge.

### Fixed

- Asset address and EIP-712 domain are now selected together from one
  `NETWORKS` table rather than being independent constants. Base mainnet USDC
  signs as `"USD Coin"` while Base Sepolia USDC signs as `"USDC"` — changing
  the network without changing the domain would fail every client signature,
  reporting an error that reads like a bad API key. An unknown or blank
  `X402_NETWORK` logs an error and falls back to mainnet, so a typo can never
  silently quote prices in worthless testnet USDC.

## [0.5.0] — 2026-08-25

### Fixed

- **x402 facilitator wire format** — verify/settle previously sent
  `{"payload": <raw header string>, "requirements": …}`; the x402 v2 protocol
  requires `{"x402Version": 2, "paymentPayload": <decoded object>,
  "paymentRequirements": …}` with the base64 `X-Payment` header decoded first.
  A paying agent could never complete a purchase. Now built on the official
  `x402` Python SDK (`HTTPFacilitatorClient` + schemas), so the wire format
  tracks the spec instead of a hand-rolled approximation.
- **Facilitator targeted testnet** — default facilitator was
  `https://x402.org/facilitator`, which serves Base Sepolia only. Mainnet
  USDC payments could not verify there. Default is now the CDP facilitator
  (`https://api.cdp.coinbase.com/platform/v2/x402`) with CDP API-key JWT auth
  (`CDP_API_KEY_ID` / `CDP_API_KEY_SECRET`), implemented locally with
  PyJWT + cryptography to avoid the full `cdp-sdk` dependency tree.
- **Missing EIP-712 domain in payment requirements** — `accepts[].extra` now
  carries `{"name": "USD Coin", "version": "2"}` (Base USDC's EIP-712 domain),
  without which clients cannot sign EIP-3009 transfers.

### Added

- **Bazaar discovery extension** — 402 responses from `/v1/scan/pay` (and the
  `/.well-known/x402.json` manifest) now carry `extensions.bazaar`
  (info + JSON Schema per the x402 bazaar extension spec), so facilitators
  that support it — the CDP facilitator feeds Coinbase's Bazaar catalog —
  index the endpoint once a payment carrying the declaration settles.
- Settlement receipt returned to payers via `PAYMENT-RESPONSE` header
  (plus `X-PAYMENT-RESPONSE` alias) on successful paid scans.
- Contract tests asserting the exact JSON sent to the facilitator's
  /verify and /settle endpoints (transport-level mock, no internal mocking).

### Changed

- **A2A Agent Card regenerated against the A2A v1.0 schema** (Linux
  Foundation): `supportedInterfaces` replaces the old top-level
  `url`/`authentication` fields; skills `examples` are strings; canonical
  well-known path is `/.well-known/agent-card.json` with `agent.json` kept
  as alias (previously the roles were reversed). Interfaces are declared
  honestly as MCP streamable-HTTP + OpenAPI custom bindings — this service
  does not implement A2A JSON-RPC messaging.
- Version metadata synced: app, `server.json`, and Agent Card all report
  0.5.0 (previously 0.4.0 / 0.3.0 / 0.3.0), and rule-count claims corrected
  to 38 L1 rules (L1-001–L1-038 in compuute-scan v0.6.2, of which two are
  whole-codebase negative checks).

### Added (docs)

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

[Unreleased]: https://github.com/Compuute/compuute-scan-api/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.5.1
[0.5.0]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.5.0
[0.4.0]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.4.0
[0.3.0]: https://github.com/Compuute/compuute-scan-api/releases/tag/v0.3.0
