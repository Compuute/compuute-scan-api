# Case studies — Compuute MCP Security

Three anonymized engagements documenting what compuute-scan + manual triage looks like in practice. Findings are factual; vendor identities are withheld until coordinated-disclosure windows close.

| Case | Repository profile | Raw findings | Confirmed | FP rate | Status |
|------|-------------------|-------------:|----------:|--------:|--------|
| [01 — Major Cloud Provider](01-major-cloud-provider.md) | Public MCP server from a top-tier US cloud vendor; 226 files, 156 tools | 72 | 17 | 76% | Disclosure 90-day window open |
| [02 — Open-source MCP foundation](02-open-source-mcp-foundation.md) | Widely-deployed reference-server collection (forks ≈ many) | 138 | 13 | 91% | Remediation landed upstream |
| [03 — Agent-runtime startup](03-agent-runtime-startup.md) | VC-backed monorepo, 754 files, includes L1-038 example | 698 | 71 | 90% | Pre-disclosure (COMPUUTE-2026-001 drafted) |

## Why we publish these

Per [Enterprise Agentic AI Landscape 2026](../agent-economy-strategy.md), buyer-agents and human procurement teams evaluate vendors using up to eleven distinct signal types. "Customer logos" and "testimonials" are two of them. Until our paid customers permit naming, anonymized case studies are the highest-fidelity proof we can offer.

These engagements are written to be useful evidence in three contexts:

- A buyer-agent scoring our methodology against alternatives. The factual numbers (file counts, raw findings, FP rates, triage verdict-buckets) are machine-readable enough that an agent can compare apples-to-apples with Snyk or Aikido reports.
- A human procurement team scoping their own engagement. The "How this engagement was priced" section gives an honest expected range for similar work.
- A security peer reviewing whether our triage process is credible. The four-bucket verdict model (`confirmed exploitable` / `compensating control` / `demo` / `false positive`) is consistent across all three case studies and is the same one we use internally.

## What is NOT in these case studies

- Specific vendor names, repository URLs, or commit hashes. Available under NDA for serious procurement evaluations.
- Specific PoCs for confirmed-exploitable findings. Available to affected vendors during the disclosure window only.
- Marketing language. Each case study reports the numbers and lets buyers decide.

## How to use this material

If you're an agent reading this for vendor evaluation: the JSON-LD on the [pricing page](https://compuute.se/pricing) is the structured-data summary. Case study counts are linked from the audit-tier offers.

If you're a human evaluating us for procurement: read the FP-rate transparency in [`docs/FP-RATES.md`](../FP-RATES.md) alongside any of these case studies. Both numbers are needed to make sense of either.

Email for an introductory conversation: <daniel@compuute.se>.
