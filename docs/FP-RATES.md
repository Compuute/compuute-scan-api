# False-positive rate transparency

A scanner that hides its false-positive rate is selling precision it doesn't have. This document publishes what we know about compuute-scan's FP behaviour so a buyer can decide what triage capacity they need.

Last validation: 2026-05-22 — methodology described below.

## Headline number

**~90% raw FP rate** when running compuute-scan against production MCP repos *without* triage. After manual validation against a threat model, the confirmed-findings rate is ~10% of raw output.

This is the historical figure from auditing the [`modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers) repository in March 2026:

- 138 raw findings
- 13 confirmed after manual review (9.4%)
- 125 false positives or non-exploitable patterns

Same rate range is consistent with similar broad-pattern detectors (e.g. Semgrep's community rules report 70–95% raw FP rate when applied without project-specific tuning).

## Why we accept this rate

It's a deliberate design choice for the L0 + L1 tier of compuute-scan:

- **Broad coverage > narrow precision.** Catching a real critical finding in 1 of 10 noisy matches beats missing the critical with a quieter scanner. The disclaimer explains the contract.
- **Defense in depth is invisible to regex.** A finding like `eval(user_input)` in a file where the variable is sanitized 5 lines earlier is technically a true pattern match but functionally an FP. Static analysis cannot see that without dataflow analysis (an L2+ capability we don't claim).
- **Triage is the buyer's problem we can help with.** L2–L4 manual audits at [compuute.se/audit](https://compuute.se/audit) are where we apply dataflow review on top of L0–L1 output.

## Per-rule FP-rate snapshot (May 2026)

Based on triage of `.nightly-work` batch scan (19 production MCP servers, 3 813 source files, 3 486 raw findings). Validation is partial — full validation is a P1 deliverable. These are the rules where we have sample triage data:

| Rule | Title | Severity | Sample size | Confirmed-rate |
|------|-------|----------|------------:|---------------:|
| `L1-001` | `eval()` with non-literal argument | critical | 22 hits | ~25% (5 confirmed; rest are sanitized) |
| `L1-002` | Shell command execution (exec/spawn) | critical | 18 hits | ~15% (3 confirmed; many `execFile` with literal-only args) |
| `L1-009` | Dynamic import with variable path | high | 11 hits | **~10%** (most are multi-line `from X import (...)` static imports — known regex over-match) |
| `L1-017` | Python CORS wildcard | high | 9 hits | **~85%** (high precision — wildcard CORS is usually real) |
| `L1-038` | npx/uvx runner-arg injection | high | 3 hits | **~33%** (1 runtime TP / 2 build-time pattern matches — see [scan-self-triage.md](scan-self-triage.md)) |

The `L1-009` row in particular is a known upstream over-match. Tracked at [`Compuute/compuute-scan` issues](https://github.com/Compuute/compuute-scan/issues) (forthcoming) once a reproducer test case is filed.

## How findings carry FP context in the response

Each finding includes a `confidence` field (planned for compuute-scan v0.7+) and the response-level `_disclaimer` field today:

```json
{
  "summary": {"critical": 1, "high": 94, "medium": 22},
  "score": 0,
  "_disclaimer": "PATTERN MATCH — compuute-scan is a static analyzer. Findings indicate that a vulnerable pattern is present in the source; exploitability depends on whether the affected code path is actually reachable from an attacker-controlled input. Manual dataflow review required for production decisions."
}
```

A consumer that displays the disclaimer correctly will never present findings as "you have 94 confirmed vulnerabilities" — only as "you have 94 patterns worth triaging".

## What we measure FP-rate **against**

Not against "would this scanner find anything Snyk would find?" That's a different scanner with a different design.

We measure against the **Ox Security threat model for MCP servers**: an attacker who can influence MCP tool descriptions, tool arguments, or registered tool URLs and wants to either (a) execute code on the agent operator's host or (b) exfiltrate secrets from the agent context. A finding is "confirmed" if there exists a plausible attack path under that model, and "false positive" if static analysis matched the pattern but the threat model rules out exploitation.

## How a buyer should use this number

- For **CISO / pen-test buyers**: expect to spend 30–60 minutes triaging the raw output of a single scan. We provide compuute-scan as a tool that accelerates that triage, not as a replacement for it.
- For **agent operators choosing a third-party MCP server**: use the `score` field as a coarse risk signal. A score of 0 with 90 high findings warrants a second look; a score of 95 with 2 mediums probably doesn't.
- For **auditors / compliance**: use the per-rule fields and the `data_source` field to provide audit-trail-ready evidence that a scan was performed and what its limits are.

## Roadmap for tightening these numbers

These are P1+ work items in the project backlog:

- Per-rule unit tests with labelled FP / TP fixtures (target: ≥10 fixtures per rule)
- Confidence fields in per-finding output (low / medium / high)
- L1-009 multi-line-import false-positive class fix (upstream)
- Dataflow analysis as an opt-in L2 mode (future major release)
