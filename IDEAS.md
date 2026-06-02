# IDEAS.md — composted product hypotheses

Things we considered building but **deferred** until demand validates them. This file exists so good thinking isn't lost, but also isn't enacted prematurely.

## Rule: nothing on this list gets built until

1. We have **≥ 1 paid customer** on the existing service line that the idea would extend, AND
2. That customer **explicitly asks** for the capability the idea provides

This rule exists because we have established (via 6+ days of session work) that builder-push without buyer-pull produces impressive GitHub orgs and zero revenue.

If you find yourself wanting to build something on this list, re-read the rule. If it still seems worth doing, write down which customer asked and what they said, then revisit.

---

## tokenwatch — AI procurement CLI (composted 2026-05-25)

**Proposal source:** Internal session 2026-05-25 (`compuute-tokenwatch — AI Procurement Due Diligence Toolkit`)

**Three-layer model (intellectually solid — keep this):**

- **Layer 1 — Factual:** tokens/cost per workflow, model-mix, retry-rate, routing-savings candidates. Fully measurable from inference logs.
- **Layer 2 — Negotiation:** reserved-vs-best-efforts allocation, fallback plans, queue position, repricing on new-customer load. No data exists for these; human judgment + vendor contract review only.
- **Layer 3 — Operational:** routing-layer savings (semi-measurable), hidden human-in-loop detection (heuristic flags). Output as flags, not verdicts.

This separation is the intellectual asset. **It applies to the manual audit deliverable too** — when we sell the AI Procurement Risk Audit, the deliverable structures findings into these three layers.

**Why not a CLI right now:**

| Reason | Verifiable evidence |
|--------|---------------------|
| Commoditized space | Helicone, Langfuse, LangSmith, Portkey, TrueFoundry, OpenRouter — all ship Layer 1 today |
| Funded incumbent | Lio raised $30M Series A from a16z in March 2026 specifically for AI-procurement automation |
| Zero demand signal from us | 0 stars on existing repos, 0 conversations, 0 paid pilots on compuute-scan-api |
| Position mismatch as CLI | We are a boutique consultancy per Compuute AB's lock; Gartner 2026 says boutiques win by *"bundling governance audits with domain expertise"*, NOT by building tools that compete with funded SaaS |
| Opportunity cost | 25-30h focused work that would otherwise produce ~50 cold DMs + 3 case studies |

**Where the idea lives now:**

- The **three-layer model** is in our audit-delivery methodology (see `docs/audits/ai-procurement-risk-audit.md`)
- The **three executive review questions** (reserved-vs-best-efforts %, routing plan with measured savings, hidden human-in-loop) are discovery-call questions for the AI Procurement Risk Audit sales flow
- A 2-3 page **AI Procurement DD Checklist** ships as the lead magnet (Markdown, public)

**Resurrect-the-CLI gate (be honest with yourself):**

Build the Node.js CLI version IF AND ONLY IF:

1. At least 1 AI Procurement Risk Audit ($5-15K) sold via compuute.se/audit
2. AND the customer says (or signals via repeat engagement) that an ongoing scanning tool would replace a meaningful chunk of the manual audit work
3. AND we have observed traffic from agents/operators searching for the tool (e.g. via analytics on the procurement checklist's landing page)

Not before.

**Salvageable artifacts if/when we build:**

- The proposal text itself in `compuute-tokenwatch/CLAUDE_CODE_PROMPT.md` (archive)
- The pricing.json template structure (last_verified field, vendor-source comments)
- The HTML report generator pattern (can reuse from compuute-scan-api)
- Security boilerplate (input untrusted, no eval, fail-closed, PII redaction)

---

## Future ideas (placeholder)

When the next "this would be cool to build" hits, write it here first. If it's still compelling after a week, revisit. If you've already built it before writing here, you broke the rule.

- _(empty — add ideas as they come up)_

---

## Things that should NEVER go in this file

These are not "compostable ideas." If you find yourself writing one, stop and call the reviewer:

- A second product that requires us to rename our position
- A pivot away from MCP/agent/security scope
- A SaaS product that competes with funded incumbents
- "We need to build X because a Twitter thread said so"

The position lock is the asset. Compost ideas that fit it. Discard ideas that change it.
