# Strategy

For someone reading this in 6 months trying to understand why decisions were made.

## Position

**Compuute AB — independent Swedish boutique security consultancy specialising in AI agent / MCP server / procurement-risk audits.**

Per Gartner 2026 Hype Cycle for Agentic AI: *"governance, security and cost-focused profiles emerging alongside core agentic AI technologies"* and *"boutique consultancies capture significant value by bundling governance audits with domain expertise"*. We sit precisely in that bundle.

Three product surfaces, one position:

- **compuute-scan (open source) + scan.compuute.se (hosted)** — MCP-specific static security scanner. Lead magnet + technical credibility surface. Sold via volume / discovery, not direct revenue.
- **L2–L4 MCP Security Audits** — manual review of customer MCP deployments. $5K–$30K SoW.
- **AI Procurement Risk Audit** (added 2026-05-25, see issue #24) — Layer-1 / Layer-2 / Layer-3 vendor due-diligence for organizations buying enterprise AI capacity. $5K–$15K SoW. Aligned to McKinsey 2026 finding (42% of enterprises have AI workflow optimization as top priority) + State of FinOps 2026 (98% of teams manage AI spend) + Gartner boutique-consultancy opportunity above.

Sold to **operators choosing, shipping, or buying MCP/AI capacity** (humans), not to autonomous agents directly. Differentiation is **threat-intel response cadence** (compuute-scan rule L1-038 added within one week of the Ox Security publication) and **honest three-layer framing** (factual / negotiation / operational — see `docs/audits/ai-procurement-risk-audit.md`), not feature count.

What we are NOT:

- Not a generic SCA tool (Snyk, Aikido already do that for the broader npm/PyPI universe).
- Not an agent KYC service (a16z named that gap; a different product).
- Not a CVE-as-API service (Path tried in earlier feat/threat-check; killed because GitHub Advisory is free and we lost the comparison).

## Pricing model — three tiers, separately defensible

| Tier | Audience | Distribution | Price | Status |
|------|----------|-------------|-------|--------|
| Free | Indie devs, agent builders | `npx compuute-scan ./repo` (open-source CLI) | $0 | Live |
| **Per-scan API** | Agents discovering via Agentic.market | `/v1/scan/pay` with x402 | $0.10 USDC | Live (X402_WALLET_ADDRESS set 2026-05-23) |
| **MCP Security Audit (L2–L4)** | Enterprises shipping MCP to production | `compuute.se/audit` discovery call → SoW | $5K–$30K | Existing offering |
| **AI Procurement Risk Audit** | Procurement/CTO/CISO buying enterprise AI capacity | `compuute.se/audit` discovery call → SoW + delivered report structured by Layer 1/2/3 | $5K–$15K | Added 2026-05-25 — see issue #24 + `docs/audits/ai-procurement-risk-audit.md` |

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
| 2026-05-25 | Added AI Procurement Risk Audit ($5–15K) as service line; composted tokenwatch CLI to IDEAS.md | Gartner 2026 Hype Cycle: boutiques win by *"bundling governance audits with domain expertise"*. McKinsey 2026: 42% of enterprises prioritize AI workflow optimization. Lio's $30M Series A from a16z (March 2026) confirms procurement-AI demand. Building as service line (6h) instead of CLI (30h) avoids competing with funded incumbents (Helicone, Langfuse, Lio) on commoditized software and stays in boutique-consultancy sweet spot. See issue #24 (build) and #25 (composted CLI) |
| 2026-05-25 | Position broadened: "MCP security" → "AI agent / MCP / procurement security" | Per Gartner direct recommendation for boutiques to bundle governance + domain expertise. Not drift — deepening into the analyst-named opportunity |
