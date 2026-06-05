# Case study: Agent-runtime startup's monorepo

> Anonymized. The vendor builds an agent-runtime platform for desktop automation and has a venture-funded base.

## Context

This is a venture-funded startup building an agent-runtime that lets AI agents drive desktop applications. The MCP server in question is the bot-component the vendor ships to coordinate agent sessions with their cloud control plane. The repository is a public-facing monorepo containing both the agent bot and the docs-generation tooling.

The scan was triggered by Compuute's May 2026 batch run plus a follow-up after compuute-scan released L1-038 (the npx-argument-injection rule) inspired by Ox Security's published research from earlier the same month.

## Scope

- **Target:** the vendor's public monorepo at the commit on `main` as of 2026-05-22.
- **Scanner:** `compuute-scan` v0.6.2.
- **Scope:** L0 + L1, with focus on the L1-038 npx-runner pattern.
- **Files scanned:** 754.

## Raw output

| Severity | Raw findings | Post-triage confirmed |
|----------|-------------:|----------------------:|
| 🔴 Critical | 115 | 11 |
| 🟠 High | 397 | 38 |
| 🟡 Medium | 186 | 22 |
| **Total raw** | **698** | **71 (~10.2%)** |

Largest repo we have scanned. FP rate consistent with the published ~90% baseline.

## The L1-038-specific findings

The newly-published rule fired three times in this codebase. Per the published [methodology](../whitepaper/mcp-security-methodology-v1.md) the triage produced:

| Hit | Location | Verdict |
|----:|:---------|:--------|
| 1 | `libs/cuabot/src/client.ts:234` — `spawn('npx', spawnArgs, …)` where `spawnArgs` includes a value derived from an external setter call | **Confirmed exploitable** under the Ox threat model. Filed with vendor as pre-disclosure draft (see `COMPUUTE-2026-001`). |
| 2 | `scripts/docs-generators/generate-versioned-docs.ts:434` — `spawnSync('npx', ['tsx', tsGenScript, `--sdk=${config.name}`])` | Build-time pattern match. The `config.name` value resolves to internal constants; not attacker-reachable in the threat model. **False positive at runtime, true positive at the syntactic level.** |
| 3 | `scripts/docs-generators/runner.ts:177` — `spawnSync('npx', ['tsx', generatorPath, ...args])` | Same class as #2. Build-time scripting, not runtime surface. **False positive at runtime.** |

This 1-of-3 ratio is the case study we use when illustrating the difference between **pattern detection** (what the scanner does) and **exploitability assertion** (what manual triage does). All three findings are correct as pattern matches; only one is exploitable under the actual threat model.

The full triage and disclosure plan is documented in [`docs/advisories/COMPUUTE-2026-001.md`](../advisories/COMPUUTE-2026-001.md).

## Triage process

Same four-bucket model. Of the 698 raw findings:

- **Confirmed exploitable:** 71.
- **Confirmed pattern but compensating control:** 184 (heavy use of TypeScript type-narrowing and runtime validation libraries).
- **Demo/test code:** 167 (large test surface).
- **Scanner false positive:** 276.

The high test-surface contribution (167) is unusual; most production MCP servers have a much smaller ratio. This vendor invests in test coverage, which appears in the scanner output as "pattern matches in test files" that aren't runtime risks.

## Outcome

- L1-038 finding sent as pre-disclosure on 2026-05-23 (90-day clock running).
- Bulk findings batch filed with the vendor's security contact the same week.
- Vendor responded constructively within 5 business days; remediation plan in motion.
- Coordinated public advisory expected August 2026.

## What buyers should take away

- The L1-038 triage (1 real / 2 syntactic) is **why we don't sell scanner output as "vulnerabilities" — we sell scanner output plus triage as "audits."**
- A 698-finding raw count in a 754-file repo would be terrifying without the triage process. The 71 confirmed findings are tractable to address; the 627 noise is what we filter out for the customer.
- This is also the case study that demonstrates our **threat-intel response cadence**: Ox published the npx-injection vector in early May 2026; compuute-scan v0.6.1 shipped L1-038 within seven days; the rule then surfaced a real finding in the very next batch.

## How this engagement was priced

The scan and triage above ran at zero cost as part of the batch validation. A vendor commissioning this depth of work on a comparable monorepo (~750 files, multiple language ecosystems) should expect $10,000–$15,000 — see [the audit pricing](https://compuute.se/pricing).

---

*Case study prepared by Compuute AB. Scanner version, raw counts, triage verdicts, and disclosure-window status are factual. Vendor identity is withheld until the disclosure window closes. For procurement-level introductions: <daniel@compuute.se>.*
