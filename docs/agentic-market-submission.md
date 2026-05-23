# Agentic.market submission prep

Coinbase Agentic.market discovers services through the CDP Facilitator processing
x402 payments on endpoints with the Bazaar discovery extension enabled. There is
no traditional application form. Manual curation exists for premium placement.

## Path A — auto-index via x402

**Prerequisites**

- `/v1/scan` returns `402 Payment Required` for unauthenticated requests, with an
  x402 challenge in the response body and headers.
- Payment lands on a Coinbase wallet via the Base L2 USDC contract.
- The CDP Facilitator processes the payment and indexes the endpoint automatically.

**Implementation outline (compuute-scan-api)**

1. Add an x402 middleware that checks for the `X-PAYMENT` header. If missing or
   invalid → 402 with a JSON body containing the resource description.
2. Configure the wallet address that will receive USDC payments.
3. Set per-scan price (suggested: $0.10 = 100_000 wei USDC).
4. Add Bazaar discovery metadata in the 402 response:
   ```json
   {
     "x402Version": 1,
     "accepts": [{
       "scheme": "exact",
       "network": "base",
       "maxAmountRequired": "100000",
       "resource": "https://scan.compuute.se/v1/scan",
       "description": "Scan a public GitHub MCP-server repo. Returns severity counts, score, top findings.",
       "mimeType": "application/json",
       "payTo": "<COINBASE_WALLET_ADDRESS>",
       "maxTimeoutSeconds": 180,
       "asset": "USDC",
       "extra": {
         "name": "compuute-scan",
         "version": "0.6.2",
         "category": "security",
         "tags": ["mcp", "static-analysis", "cve", "supply-chain"]
       }
     }]
   }
   ```
5. After deploy, send a test payment using `x402-fetch` SDK to trigger indexing.
6. Within ~24h: search for `compuute-scan` on agentic.market.

**Required from Daniel**

- Decide price per scan (default: $0.10 USDC).
- Confirm Coinbase wallet address to receive USDC on Base.
  - Existing one from leads.compuute.se x402 setup: `0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67`
- Decide tier strategy: x402-only, or x402 alongside a free-tier with quota.

**Engineering effort**: 2-3 hours (route middleware, env var, redeploy, test payment).

## Path B — manual curation outreach

If we don't want to add payment yet, we can email Agentic.market for manual
listing as a "free / utility" service. This is lower visibility but no
engineering cost.

**Email template**

> **To:** agentic-market@coinbase.com
>
> **Subject:** Free agent-callable utility — MCP security scanner — request manual listing
>
> Hi,
>
> I'm building [compuute-scan-api](https://scan.compuute.se), an agent-callable
> static security scanner for MCP servers. It wraps the open-source
> [compuute-scan](https://github.com/Compuute/compuute-scan) (37 MCP-specific
> rules, 8 languages: TS/JS/Python/Go/Rust/C#/Java/Kotlin).
>
> The endpoint is currently free (no x402 challenge yet) and intended to help
> agents do pre-install due-diligence on third-party MCP servers before
> connecting. I'd like to request a manual listing on Agentic.market under
> Security/Compliance.
>
> - Service URL: `https://scan.compuute.se`
> - REST endpoint: `POST /v1/scan` with `{"repo_url": "https://github.com/..."}`
> - MCP endpoint: `https://scan.compuute.se/mcp/` (tool: `scan_mcp_server`)
> - OpenAPI: `https://scan.compuute.se/openapi.json`
> - Operator: Compuute AB (Sweden), 18+ years security background
> - Future: will add x402 paid tier once usage is validated
>
> The threat-intel-response cadence: when Ox Security published the
> npx-argument-injection vector earlier this month, the detection was
> added to compuute-scan v0.6.2 within the same week (rule L1-038).
> See [CHANGELOG](https://github.com/Compuute/compuute-scan/blob/main/CHANGELOG.md).
>
> Happy to provide whatever metadata format you need for the listing.
>
> Best,
> Daniel Abbay — Compuute AB
> daniel@compuute.se

**Engineering effort**: 0. Just send the email.

**Realistic outcome**: low-priority listing or no response.

## Path C — defer

Skip Agentic.market until we have:

- Validated demand via DM responses (Renato, etc.).
- A pricing model decision based on observed willingness-to-pay.
- An MRR or LOI signal that justifies x402 implementation effort.

This is the most honest path if revenue from existing channels (manual audits,
fractional CISO retainers) is the realistic 90-day target.

## Recommendation

**Path C until first paid audit lands**, then **Path A** once we have evidence
that an x402 paid tier matches observed buyer behavior. Path B is a one-day
fallback if a buyer specifically asks "are you on Agentic.market".

The Renato DM is the unblocking event for any path. Until that or another
DM lands a paid engagement, Agentic.market is premature optimization.
