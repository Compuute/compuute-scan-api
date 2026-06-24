# Agent-economy strategy

**Version 1.0 — 2026-05-25**

How Compuute navigates the agent-to-agent commerce shift, what we deliberately do NOT build, and what we measure.

> This document is **dynamic**. It updates whenever a16z, Gartner, McKinsey or FinOps research publishes data that materially changes our assumptions. Decision-log at the bottom records each shift.

## 1. The data we're navigating against

| Source | Datapoint | Date |
|--------|-----------|------|
| Coinbase Agent.market launch | 69,000 active agents · 165M txns · ~$50M cumulative volume on x402 | April 2026 |
| a16z Big Ideas 2026 | Power shifts from sellers to buyer-agents; KYA (Know Your Agent) is the critical missing primitive | Jan 2026 |
| a16z 2026 podcast | *"Counterparty AIs negotiate within parameters and flag asymmetries for human review"* — high-value deals still human-ratified | 2026 |
| Google Universal Commerce Protocol (UCP) | Open standard for agent–retail interoperability | Jan 2026 |
| Enterprise Agentic AI Landscape 2026 | Buyer-agents evaluate vendors via 11 signal types | April 2026 |
| McKinsey 2026 | 42% of enterprises rank AI workflow optimization as top priority | 2026 |
| State of FinOps 2026 | 98% of FinOps teams manage AI spend | 2026 |
| Gartner 2026 Hype Cycle | Boutiques win by *"bundling governance audits with domain expertise"* | 2026 |

## 2. The 11 signals buyer-agents evaluate

Per Enterprise Agentic AI Landscape 2026:

1. Product pages
2. Technical documentation
3. Knowledge bases
4. API references
5. Implementation guides
6. Pricing explainers
7. Legal terms
8. **Trust centers (SOC 2, ISO 27001)**
9. **Customer logos**
10. **Testimonials**
11. **Third-party reviews + independent editorial coverage**

Compuute's current coverage:

| Signal | Status | Tracked in |
|--------|:------:|------------|
| 1–5 (technical surface) | ✅ | scan.compuute.se, /openapi.json, docs/ |
| 6 Pricing explainer | ⚠️ Fragmented | Issue #27 — consolidate at /pricing with JSON-LD |
| 7 Legal terms | ⚠️ Partial | MIT license; full ToS deferred to first paid contract |
| 8 Trust center | ❌ | Issue #32 — SOC 2 Type I readiness |
| 9 Customer logos | ❌ | Issue #28 — anonymized case studies first, named logos when contracts permit |
| 10 Testimonials | ❌ | Same as 9 |
| 11 Third-party coverage | ❌ | Issue #31 — Show HN as opening move |

**Score: 5 / 11.** That number is the data-driven proof that build-more is the wrong move; close the trust gap is.

## 3. The two-track strategy

Different tiers have different agent-purchasability today. We build for both, with explicit gates between them.

### Track A — Micropayment tier (x402, $0.10 per scan)

- **Buyer-agent buying autonomously**: works today. We have the infrastructure (x402, well-known/x402.json, Coinbase wallet).
- **Why no transactions yet**: agents that scan MCP servers don't have a *trigger* to invoke us. They aren't configured to do pre-flight security checks. The fix is **being a default in the frameworks where agents are built**, not adding more product.
- **Concrete moves**: Issue #30 (LangChain Hub + CrewAI submission), Issue #31 (Show HN visibility burst).
- **30-day KPI**: ≥100 LangChain installs OR ≥50 GitHub stars from non-Compuute users.

### Track B — Audit tier ($5K–$30K per engagement)

- **Buyer-agent buying autonomously**: NOT today. Per a16z, counterparty AIs negotiate within parameters but flag asymmetries to humans. KYA infrastructure isn't mature enough. Humans still ratify high-value engagements.
- **Why we still build for it**: McKinsey 42% + State of FinOps 98% show enterprise demand exists. Gartner recommends boutiques bundle governance + domain expertise — exactly our shape.
- **What we need is trust signals 8–11**, not more product.
- **Concrete moves**: Issue #27 (pricing), Issue #28 (case studies), Issue #32 (SOC 2 readiness).
- **30-day KPI**: ≥5 booked discovery calls + ≥1 paid LOI or signed audit.

## 4. What we explicitly DO NOT build (and why)

### A "marketing agent" or "selling agent" that closes deals autonomously

**Wrong diagnosis.** a16z's verified position is that the bottleneck is **identity + trust signals**, not seller capacity. Building a sales-automation agent before KYA infrastructure exists adds friction without unlocking conversion. Reconsider when:

- KYA cryptographic credentialing is widely deployed (estimated 2027+)
- We have ≥3 paid audits closed manually (so the agent has a workflow to automate)
- The human-ratification requirement weakens (currently universal for $5K+)

### A second product to compete with Helicone / Langfuse / Lio in observability or FinOps

Composted in [`IDEAS.md`](../IDEAS.md) as `tokenwatch`. Gate: ≥1 paid AI Procurement Risk Audit + customer asks for tooling. We do NOT compete with $30M-Series-A automation on commodity software.

### "Improvement" work on shipped P0/P1 items

P0 (credibility baseline) and P1 (track record) are closed. Touch them only if a buyer-agent signal or paid customer surfaces a real blocker. No proactive polish.

## 5. ROI measurement

Per Daniel's directive: dynamic, data-driven, agile to market trend, ROI-focused.

### What the original trigger got wrong (recorded 2026-06-24)

The first version of this section set a calendar trigger of **2026-06-24, 30 days from doc creation (2026-05-25)**. That clock measured the wrong thing. It assumed we had 30 days of *market exposure*. In reality:

- 2026-05-25 → 2026-06-01 (7d): only basic MCP endpoint live; no `.well-known/x402.json`, no agent-card.json, no llms.txt. Effectively undiscoverable by automated agent crawlers.
- 2026-06-01 → 2026-06-23 (23d): P2.5 sprint added discovery surfaces, but **zero** active distribution work. Sat in place hoping someone would find us.
- 2026-06-24 (the original cutoff): Anthropic Skill PR opened, llms.txt deployed, 2 awesome-list PRs opened. Show HN still not posted.

Honest read: **we had 0 days of active distribution exposure** when the original trigger fired. Daniel flagged this on 2026-06-24 and the trigger is reset to a condition-based, exposure-anchored model below.

### Leading indicators (weekly — the ones that actually move first)

The order matters: a paid scan requires that an agent first *finds* us, then *succeeds* with a free call, then is *configured* to spend. Measure the early steps, not the last one.

| Tier | Metric | Source | Target before escalating to next tier |
|------|--------|--------|---------------------------------------|
| **T0 — Reach** | Unique non-Compuute IPs hitting `/v1/scan`, `/mcp/`, or any `/.well-known/*` per 7-day window | `railway logs --deployment` filtered, excluding 100.64.0.0/10 internal probes and Compuute office IPs | ≥10 unique IPs/week |
| **T0 — Reach** | Anthropic Skill installs (once anthropics/skills#1346 merges) | Skill-marketplace install telemetry | ≥5 installs/week |
| **T0 — Reach** | Awesome-list PRs merged | GitHub | ≥1 merged |
| **T1 — Engagement** | `POST /v1/scan` calls with `repo_url` ≠ a Compuute-owned repo | Railway log grep | ≥20 scans/week |
| **T1 — Engagement** | GitHub stars on compuute-scan + compuute-scan-api from non-Compuute accounts | `gh api repos/.../stargazers` | ≥10 stars |
| **T2 — Conversion** | `POST /v1/scan/pay` attempts (any HTTP code) | Railway log grep | ≥1 attempt |
| **T2 — Conversion** | USDC received on Base L2 wallet | Base RPC `eth_call balanceOf` on `0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67` | ≥$0.10 (the first scan) |
| **T2 — Conversion** | Discovery calls booked | `docs/outreach/calls.md` | ≥1 booked |

T0 must move first. If T0 is dead and T1/T2 also dead, that's a discovery problem (we don't exist to the market). If T0 moves but T1 doesn't, that's a value-prop problem (they find us but the offer doesn't land). Different diagnoses, different fixes.

### Lagging indicators (monthly)

| Metric | Source |
|--------|--------|
| USDC received on Base L2 wallet | https://basescan.org/address/0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67 |
| Paid LOI / signed audit count | Manual |
| MRR / quarterly revenue | Stripe + on-chain |

### Pivot trigger (binding, condition-based)

The pivot question — Track A (micropayment) vs Track B (B2B audit) — is answered by **post-exposure data**, not calendar age of the strategy doc. The trigger clock starts when active distribution is live, defined as:

> **Exposure-start (T₀):** the first day after BOTH of these are true:
> 1. Show HN posted (per `docs/launches/show-hn-2026.md`)
> 2. At least one of {anthropics/skills#1346, punkpeye/awesome-mcp-servers#8621, any successor awesome-list PR} has been merged

From T₀, run a **60-day evaluation window** (not 30 — adoption curves for new agent-tooling categories show a 4–6 week visibility ramp before signals stabilise; 30 days would re-make the same too-short mistake).

**Pivot if, at T₀ + 60 days, ALL THREE of these are true:**

- T0 metrics dead: <10 unique non-Compuute IPs in the trailing 7-day window
- T1 metrics dead: <5 third-party scan calls in trailing 7 days, <5 non-Compuute GitHub stars
- T2 metrics dead: 0 paid scans, 0 booked calls

If all three tiers are dead after 60 days of active exposure, that is a clear "market hasn't signalled interest in this packaging" — pivot to Track B (B2B audit) as primary or compost the open-source-CLI thesis entirely. Decision goes in the log below with the metric snapshot that justified it.

**Soft early-warning at T₀ + 30 days:** if T0 is dead at the half-mark, re-evaluate distribution channels (which marketplaces are we missing, is the Skill description discoverable, is Show HN buried). Channel-add, not strategy-pivot.

**No infinite extensions.** "Let me add one more channel and re-measure" is the failure mode this section exists to prevent. If T₀ keeps slipping because Show HN never gets posted, that itself is the pivot signal — own-flake, not market-flake.

## 6. Why this sequence (issue build-order)

| Order | Issue | Why this slot |
|------:|:-----:|---------------|
| 1 | #27 Pricing page | Foundation — every other item links here. Buyer-agents need machine-readable pricing in 1 fetch. |
| 2 | #28 Case studies | Trust signal underpinning #30 + #31 + #32. Free leverage from already-validated nightly-batch data. |
| 3 | #29 Prospect research | Unlocks 10x DM volume — the single highest-ROI scaling move available now. Daniel still sends; capacity multiplied. |
| 4 | #30 LangChain submission | High-leverage distribution; relies on #27 (pricing) + #28 (case studies) being live for credibility. |
| 5 | #31 Show HN | One-shot visibility burst; needs everything before it live so traffic arriving from HN sees a complete picture. |
| 6 | #32 SOC 2 readiness | Lagging — unlocks B2B-tier procurement gates but takes longest. Start parallel-track once others are running. |

Total focused build time: ~22h spread over 3–5 days.

## 7. What changes in our shipped strategy

| Before this doc | After this doc |
|-----------------|----------------|
| "Distribution-first" was an internal note in STRATEGY.md | Distribution-first is the **dominant** strategy, with measurable cutoffs |
| Tokenwatch CLI composted on intuition | Compostion verified by a16z data + named gate |
| Position-lock at "MCP security" → "AI agent / MCP / procurement security" (May 25) | Same — broadened, not drifted |
| No explicit pivot trigger | **Condition-based trigger anchored on T₀ (first day of active exposure), 60-day window with tiered T0/T1/T2 acceptance criteria** (revised 2026-06-24 after the original calendar trigger was found to measure doc-age, not market-exposure) |
| No explicit "don't build" list | Section 4 above — three categories of work we deliberately don't touch |

## Decision log

| Date | Decision | Source / rationale |
|------|----------|---------------------|
| 2026-05-25 | Adopted two-track strategy (micropayment + audit) with separate KPIs per track | a16z 2026 verified data on agent-economy bottleneck (KYA, not selling agents) |
| 2026-05-25 | Composted tokenwatch CLI permanently to IDEAS.md with named gate | a16z + Lio $30M Series A → commodity software space, boutique should not enter |
| 2026-05-25 | Set 30-day pivot trigger with 3 acceptance criteria | Anti-pattern guard: 6 sessions of build-more without selling. Forcing measurable decision point. |
| 2026-05-25 | Explicit do-not-build list (selling agent, second product, P0/P1 polish) | Same rationale; documented so future sessions can refuse cleanly |
| 2026-05-25 | KPI cadence: leading weekly, lagging monthly, pivot review at day 30 | ROI-focused per Daniel's directive |
| 2026-06-24 | Reset pivot trigger from calendar (2026-06-24) to condition-based (T₀ + 60 days). Restructured leading indicators into T0/T1/T2 tiers. | Daniel flagged on 2026-06-24 that the original 30-day calendar clock measured doc-age, not market-exposure. At the original cutoff we had 0 days of active distribution exposure: Anthropic Skill PR opened same day, llms.txt deployed same day, Show HN unposted. Honest reset: measure post-exposure adoption, not pre-exposure calendar. |
| 2026-06-24 | Adopted T0 (Reach) / T1 (Engagement) / T2 (Conversion) tiered KPI model | Different dead tiers diagnose different failures (discovery vs value-prop vs conversion). The single-metric "first payment" KPI conflated all three. |
