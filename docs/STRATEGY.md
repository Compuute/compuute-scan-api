# Strategy

For someone reading this in 6 months trying to understand why decisions were made.

## Position

**Compuute MCP Security Scan-as-a-Service.**

- Wraps the open-source `compuute-scan` (37 MCP-specific L1 rules, 8 languages).
- Sold to **operators choosing or shipping MCP servers** (humans), not to autonomous agents directly.
- Differentiation is the **scanner's MCP-specific rule set + threat-intel response cadence**, not the CVE database (that's commoditized — GitHub Advisory, OSV, OSS Index are free).

What we are NOT:

- Not a generic SCA tool (Snyk, Aikido already do that for the broader npm/PyPI universe).
- Not an agent KYC service (a16z named that gap; a different product).
- Not a CVE-as-API service (Path tried in earlier feat/threat-check; killed because GitHub Advisory is free and we lost the comparison).

## Pricing model — three tiers, separately defensible

| Tier | Audience | Distribution | Price | Status |
|------|----------|-------------|-------|--------|
| Free | Indie devs, agent builders | `npx compuute-scan ./repo` (open-source CLI) | $0 | Live |
| **Per-scan API** | Agents discovering via Agentic.market | `/v1/scan/pay` with x402 | $0.10 USDC | Wired, not yet enabled (`X402_WALLET_ADDRESS` unset) |
| **Manual audit** | Enterprises shipping MCP to production | `compuute.se/audit` discovery call → SoW | $5K–$30K (L2–L4) | Existing offering |

The per-scan API is the **entry funnel** for the audit business. An agent that gets `score: 35, critical: 12` will trigger its operator to ask "who scans this for me properly?" — and that's a manual audit lead.

## Why x402 + Agentic.market matters

- 480K active agents on x402 (Q1 2026 data).
- $50M+ cumulative volume.
- Agentic.market is the discovery surface; auto-indexes endpoints once first x402 payment is processed.
- We need to BE on Agentic.market because that's where agents shop — not because the per-scan revenue itself is meaningful (it's $0.10 micropayments; the real revenue is upstream).

## Why NOT GitLab/Bitbucket support in v1

- 70%+ of MCP servers are on GitHub (publicly visible).
- Supporting more hosts triples the testing surface without proportional buyer demand.
- Buyer signal first, then expand. Default response to "do you support X?" is "not in v1; what's your specific repo so I can manually validate it would work."

## Why FREE per-scan in MVP (rather than $0.10 from day 1)

- Validate that anyone calls the endpoint at all.
- Agents calling it for free → free advertising on Agentic.market once we flip x402 on.
- Renato DM and similar warm intros need a "click here to try" link with zero friction.
- Cost of running the scanner: ~$0.0001 per scan in Railway compute. Free tier is sustainable.

When we flip x402 on:

1. Observed traffic >100 calls/day for 7 days.
2. At least one prospect explicitly asks "how do I pay for this?"
3. Per-scan revenue projected to cover ≥1 month Railway costs.

## Why MCP tool, not just REST

- 78% of enterprise AI teams have MCP-backed agents in production (Q1 2026 data).
- An MCP-callable security tool is **discoverable by Claude Code, Cursor, Goose, and other MCP clients** without code changes.
- Distribution-by-discovery, not distribution-by-marketing.
- Tool description (in `api/mcp_server.py`) is the actual "sales copy" — agents read it and decide whether to invoke.

## Roadmap — strictly demand-driven, not feature-driven

### v0.2 (current) — done

- REST `/v1/scan` with idempotency, ETag, rate-limit headers
- MCP `/mcp/` with `scan_mcp_server` tool
- x402 `/v1/scan/pay` wired (disabled by default)
- Live at `scan.compuute.se`

### v0.3 — IF Renato or similar prospect asks

- Authentication for usage tracking (API keys + monthly quotas, copy from lead-enrich-api)
- SARIF output format (`?format=sarif`) for CI/CD integration
- Redis-backed Idempotency-Key cache (move off in-memory LRU)

### v0.4 — IF Path A (x402 launch) is taken

- Enable `X402_WALLET_ADDRESS` env var (use same Coinbase wallet as lead-enrich-api)
- First x402 payment test via `x402-fetch` SDK
- Submit to Agentic.market (auto-indexes after first payment)

### v0.5 — IF an enterprise buyer asks

- Webhook delivery (POST scan results to a customer-controlled URL)
- Custom rule injection (`POST /v1/scan` with `extra_rules: [...]` body field)
- Private-repo scan via short-lived OAuth or PAT

### Never (or until very specific demand)

- GitLab/Bitbucket support
- Sub-second scan caching across users (premature optimization)
- A web dashboard (Railway logs + `/v1/scan/info` is enough)
- Multi-region deploy (single region serves agents fine)

## Defensibility

- **Moat 1 — MCP-specific rule set.** The 37 L1 rules in compuute-scan are MCP-specific (e.g., L1-038 catches Ox Security's `npx -c` injection). Adding a new rule when a threat is published takes ~1 day (proven with L1-038).
- **Moat 2 — threat-intel cadence.** Compuute AB has 18 years of security background. Renato-level prospects buy "the people who respond to threat-intel within a week", not "the people who have a scanner."
- **Moat 3 — open-source + paid funnel.** The free CLI builds trust + word-of-mouth; the paid API + audits capture commercial value.

What's **NOT a moat**:

- The CVE database (free competitors exist: GitHub Advisory, OSV).
- The hosting infrastructure (Railway is commodity).
- The x402 integration (anyone can wire it).

## Success metrics (review monthly)

| Metric | 30 days target | 90 days target |
|--------|---------------|---------------|
| Calls to `/v1/scan` | 50 | 500 |
| GitHub stars on `compuute-scan` | 25 | 200 |
| Renato-tier prospects in conversation | 1 | 5 |
| Paid audits delivered | 0 (validation phase) | 1 |
| Agentic.market listing | not yet | listed |
| x402 revenue | $0 | TBD |

**Mätningar är inte mål — de är diagnos.** Om vi inte når 500 calls/månad i kvartal 1 är frågan: är distributionen för svag, eller är produkten fel? Inte: bygg fler features.

## Decision log

| Date | Decision | Why |
|------|----------|-----|
| 2026-05-23 | Built scan-as-a-service instead of CVE-lookup-API | Data showed CVE-API is commoditized; MCP scanner is differentiated. See [agentic-market-submission.md](agentic-market-submission.md) for details |
| 2026-05-23 | Free tier in MVP, x402 wired but disabled | Validate before charging; Renato-DM needs zero-friction link |
| 2026-05-23 | GitHub-only, no GitLab/Bitbucket | 70%+ of MCP servers are on GitHub; testing surface multiplier not justified |
| 2026-05-23 | Vendored compuute-scan in Docker via build-arg | Reproducible builds; no network at scan time |
| 2026-05-23 | Single Railway region, no DB | Stateless service; horizontal scaling later if needed |
