# AI Procurement Risk Audit — Buyer Checklist

A vendor-independent due-diligence checklist for organizations buying enterprise AI capacity. Produced by Compuute AB.

> **Status:** v1.0 — 2026-05-25. The accompanying paid engagement (`$5,000–$15,000`) walks your specific vendor contracts and inference logs through this checklist and delivers a written risk assessment.

---

## Why this exists

Enterprise AI contracts are now supply contracts in everything but name. HBM and CoWoS scarcity ties every vendor — proprietary or open-weight — to hyperscaler capacity. Public macro data from Epoch AI shows ≈ 90% of AI inference capacity flows through ≈ 12% of the supply chain. That concentration is not visible in a typical AI vendor SLA.

Most procurement teams already track AI cost (FinOps's State of FinOps 2026 shows 98% do). What they lack is an independent third-party assessment of the underlying capacity risk. This checklist makes that assessment legible.

It is organized by **three layers** with different epistemic confidence. You should expect different treatment from your own analysis or any third-party assessment for each layer.

| Layer | Question type | Confidence | What automation can do |
|-------|---------------|-----------|------------------------|
| **L1 Factual** | Hard numbers from inference logs and vendor contracts | High | Fully measurable |
| **L2 Negotiation** | Contract terms, fallback rights, queue position | Low (judgment call) | Cannot automate — review by hand |
| **L3 Operational** | Routing patterns, hidden human-in-loop signals | Medium | Flag-only — interpretation required |

**Read every L2 item as "decide this and write it down."** A spreadsheet that flags an L2 item as "✓ measured" is selling you precision it does not have.

---

## Layer 1 — Factual (audit measures this)

### 1.1 Token economics

- [ ] **What are p50, p95, and max tokens-per-workflow for the top 10 workflows by volume?** If your vendor cannot report this, ask why. If you cannot extract it from your own logs, that is finding #1.
- [ ] **Cost-vs-cheaper-model delta per workflow.** For every workflow served by a frontier model, what would the same workflow cost on the smallest model that can plausibly serve it? The audit produces this table.
- [ ] **Retry rate.** Per-workflow retry-rate above 5% indicates either a brittle prompt or a vendor reliability issue. Both have cost.
- [ ] **Concurrency estimate.** Peak concurrent inference calls during the busiest hour. Drives reserved-capacity math.
- [ ] **Context-length distribution.** P95 context per workflow. Drives the eligible-vendor list (some models do not serve > 100K tokens cost-effectively).

### 1.2 Capacity & dependency mapping

- [ ] **Per-vendor share of your AI spend.** Single-vendor concentration > 70% is a finding. Document the rationale or the migration plan.
- [ ] **Per-vendor share of your AI calls (not spend).** Spend and call-share diverge — both matter for resilience modeling.
- [ ] **Geographic deployment of the model serving you.** If your data residency requires EU, are you actually served from EU regions?
- [ ] **Hyperscaler underneath each vendor.** Most AI vendors run on one of three hyperscalers. Two of your "independent" vendors may share an underlying GPU pool.
- [ ] **HBM / CoWoS supply exposure** — which specific TSMC/Samsung capacity batch is your vendor's reserved instance allocation tied to. Most vendors will not answer this; non-answer is a data point.

### 1.3 Asset depreciation alignment

- [ ] **GPU asset life vs amortization horizon.** Reserved instances priced on H100/H200 hardware: ensure your contract length matches the realistic 3–5y GPU useful life. Paying year-4 prices on year-1 hardware is a hidden margin gift to the vendor.
- [ ] **Repricing clauses on new-customer load.** If the vendor onboards a hyperscale new customer mid-contract, does your unit price adjust or does your latency degrade silently? Both happen.

---

## Layer 2 — Negotiation (no data — decide and write it down)

### 2.1 Allocation type

- [ ] **What percentage of your AI capacity is reserved vs best-efforts?** This is the single most important risk question and has no automatable answer.
- [ ] **Written fallback rights** if reserved capacity is unavailable. Is the vendor obligated to provide alternative capacity, refund, or migrate you? Time-bound?
- [ ] **Right of first refusal on additional capacity** before the vendor offers it to new customers.
- [ ] **SLA-vs-best-efforts language.** "We will use commercially reasonable efforts" ≠ "guaranteed". Almost every AI SLA is the former.

### 2.2 Queue position

- [ ] **Where do you sit in the vendor's customer queue?** Both for support and for new-capacity allocation. Boutique customers behind hyperscaler-owned customers should expect different treatment in a crunch.
- [ ] **What is your contractual position vs the vendor's own first-party products?** When the vendor launches a new feature that uses the same GPU pool, do they prioritize it over your traffic? Most contracts are silent on this. Silence = they prioritize themselves.
- [ ] **Notification window for capacity reductions.** 30 days is common in cloud contracts and absent from most AI contracts.

### 2.3 Exit and portability

- [ ] **Egress costs and data deletion timeline.** If you move off the vendor, what does it cost and how long does it take?
- [ ] **Model continuity.** If the vendor deprecates the specific model version your workflows depend on, are you guaranteed a migration path or grace period?
- [ ] **Fine-tuned-model portability.** If you fine-tuned on the vendor's platform, do you own the weights or just the inference rights?

---

## Layer 3 — Operational (flag-only — interpretation required)

### 3.1 Routing efficiency

- [ ] **Audit flags workflows where a smaller model could serve at < 80% of current cost** with no measurable quality regression on a held-out eval set. These are **routing candidates** — flagging them is automatic, deciding to route them is human.
- [ ] **Mixed-model topology.** If you currently run a single model for everything, the audit will flag this as suboptimal. Implementing a router (or buying one) is a separate engagement.

### 3.2 Hidden human-in-loop detection

- [ ] **Anomalous latency-gap signatures.** Workflows whose latency distribution shows a bimodal pattern (fast machine path + slow human-review path) get flagged. Vendor may be silently routing complex cases to human reviewers and billing as AI. Audit raises the flag; verification is interview-driven.
- [ ] **Low retry rates on high-complexity tasks.** Surprisingly low retry rates on tasks the model should plausibly fail at suggests human review before response. Same epistemic status as above.
- [ ] **Status patterns inconsistent with model-only inference.** Audit flags these; investigation is human.

> All Layer 3 items are **flags requiring interpretation**, never verdicts. The audit raises them; you decide what they mean for your contract.

---

## The three executive review questions

When you finish working through this list, the three questions to bring to the next executive review are:

1. **What percentage of our AI capacity is reserved vs best-efforts, and what is our written fallback if reserved capacity is unavailable?**
2. **What is our routing plan, and what is the measured savings (in dollars and percent) from routing candidates the audit flagged?**
3. **For the workflows where the audit flagged possible hidden human-in-loop, what did the vendor say when we asked?**

If any of these cannot be answered with a number, a written document, or a vendor email, that itself is the finding.

---

## What this audit does NOT decide for you

This is not a recommendation to switch vendors, terminate contracts, or accept any specific risk level. The audit produces:

- A measured Layer 1 baseline (numbers, tables)
- An interpreted Layer 2 status (negotiated terms, gaps)
- A flagged Layer 3 anomaly list (with caveats stated)

The decisions — switch, renegotiate, accept, migrate, route — are yours. We hold the methodology; you hold the relationship with your vendors and your board.

---

## What you get from a paid engagement

- **Kick-off call** (1h): align on scope, identify the workflows in the top-10 by volume
- **Discovery** (3–5 business days): you provide inference logs (redacted of PII), contracts (under NDA), and access to spend dashboards
- **Analysis** (5–10 business days, depending on scale): Layer 1 measured, Layer 2 reviewed, Layer 3 flagged
- **Deliverable**: a written 15–30 page report structured by the three layers, with the three executive review questions answered with your specific data
- **Read-out** (1h): walk-through with your team or board
- **Follow-up window** (30 days): we answer clarifying questions on the findings at no extra cost

Pricing scales with the number of vendors in scope and the volume of inference logs:

- **Single vendor, < 1M inferences/month:** $5,000
- **Single vendor, > 1M inferences/month:** $10,000
- **Multi-vendor (2–3 vendors) or > 10M inferences/month:** $15,000
- **Beyond that scope:** custom quote

---

## How to engage

Email `daniel@compuute.se` with subject **"AI Procurement Risk Audit — <your company>"**. We respond within 2 business days with a 30-minute discovery call to scope.

For an exploratory conversation before committing: book a 30-min free discovery call via the same email — useful if you want to walk through this checklist together against your specific situation before deciding whether to engage.

---

## About Compuute AB

Independent Swedish security consultancy. 18+ years background in independent security work; specializing in AI agent / MCP server / procurement-risk audits in 2026. EU-hosted infrastructure, GDPR-aligned. Companion open-source tools at <https://github.com/Compuute>.

---

*v1.0 — 2026-05-25. This document is updated when our methodology evolves or when material new public data (Epoch AI, State of FinOps, Gartner, McKinsey) reshapes the layer assignments. Current version: <https://github.com/Compuute/compuute-scan-api/blob/main/docs/audits/ai-procurement-risk-audit.md>.*
