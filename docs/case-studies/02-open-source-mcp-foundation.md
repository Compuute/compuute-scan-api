# Case study: Open-source MCP foundation reference servers

> Anonymized. The repository in question is a widely-deployed reference implementation used by thousands of developers as the starting template for their own MCP servers.

## Context

Several hundred GitHub repositories list this reference repository as their direct fork-source or template. Whatever pattern lives here propagates widely. We scanned it because a single critical finding in a template multiplies across the ecosystem.

## Scope

- **Target:** the foundation's flagship reference-server collection, default branch, 2026-03 commit (audited during initial nightly-batch validation).
- **Scanner:** `compuute-scan` v0.1.0 at scan time (rule-set was 28 rules + 5 layer-mapped categories; equivalent results today would use v0.6.2's 37-rule set).
- **Scope:** L0 + L1, with full manual triage of every critical finding.

## Raw output

| Severity | Raw findings | Post-triage confirmed |
|----------|-------------:|----------------------:|
| 🔴 Critical | 1 | 0 |
| 🟠 High | 94 | 8 |
| 🟡 Medium | 22 | 5 |
| 🟢 Low | 6 | 7 (negative-check rule promotions) |
| **Total raw** | **138** | **13 (~9.4%)** |

This 138 → 13 ratio is the empirical baseline that anchors our published 90% raw FP rate. It is the single most-cited number in our public methodology and the reason every API response carries a triage disclaimer.

## Confirmed findings (representative)

### Finding A — SSRF via gzip-file-as-resource tool

A tool that fetched user-supplied URLs and decompressed gzipped responses did not validate the URL against private network ranges. An attacker controlling the URL parameter could read cloud-instance metadata (`169.254.169.254`) and have the decompressed contents flow back into the agent context.

**Severity:** High. **Confirmed exploitable** with a 3-line PoC.

**Fix landed:** allow-list of public scheme + host validation before the fetch.

### Finding B — Full `process.env` dump in a demo tool

The "everything-server" example exposed a tool that returned the complete process environment to the caller. Demo code, clearly labeled — but the file was published, the README listed it, and several forks shipped it to production unchanged.

**Severity:** Critical in any deployment that retained it. **Demo-class, but real-world dangerous** because copy-paste-forking is normal in this ecosystem.

**Fix landed:** redacted to a stub with a security note.

### Finding C — Path-traversal validation gaps

The filesystem-server module had a centralized path-validation function (`validatePath()` plus `isPathWithinAllowedDirectories()`) that correctly guarded entry points. **Most of the 63 raw high findings in this module were false positives** — the guards live in a central module our 15-line scanner window doesn't always reach. Three findings represented real gaps where the guard wasn't applied; the rest were defense-in-depth artifacts.

This is the canonical example of why we publish per-rule FP rates honestly: a scanner that scored 63 critical findings here and presented them as 63 confirmed vulnerabilities would have triggered an enormous wasted triage effort. Disclosing that the guards exist but sit outside the window is the product.

## Triage process

Same four-bucket model as Case Study #1. Of the 138 raw findings:

- **Confirmed exploitable:** 8 high + 5 medium = 13.
- **Confirmed pattern but compensating control:** 47 (mostly the filesystem-server guards above).
- **Demo/test code:** 12.
- **Scanner false positive:** 66.

## Outcome

- Findings filed with the foundation's security contact within 72 hours.
- All confirmed-exploitable findings were addressed in upstream patches over the following 6 weeks.
- The "everything-server" demo tool was redacted.
- This batch became the empirical basis for the FP-rate transparency published in [docs/FP-RATES.md](../FP-RATES.md).

## What buyers should take away

- Even an actively-maintained, heavily-reviewed reference implementation had 13 real findings (and ~125 noisy ones).
- The value of a real audit is in **separating the 13 from the 138**, not in producing one of those numbers in isolation.
- If you're forking this repo or one of its derivatives as the base for your own MCP server, run the scan first.

## How this engagement was priced

Initial scan was free (part of methodology validation). Triage and report would price at \$5,000–\$10,000 for a repository this size in a commercial engagement.

---

*Case study prepared by Compuute AB based on a March 2026 batch validation. All counts, ratios, and outcome statements are factual. The repository is anonymized to avoid endorsement implications; identifying details available under NDA for serious procurement evaluations.*
