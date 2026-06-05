# Case study: Major Cloud Provider's MCP server

> **Anonymized** at vendor request. Findings real, attribution withheld until coordinated disclosure window closes.

## Context

A major US-based cloud provider operates a public MCP server that exposes their cloud control plane to AI agents. The repository is published openly on GitHub and recommended in their official documentation for customers building agents against their platform.

The server is large (226 source files, 156 tools exposed), and the scan was triggered by Compuute's May 2026 batch evaluation of 19 production MCP servers.

## Scope

- **Target:** the vendor's open-source MCP server repository at the commit on the default branch as of 2026-05-22.
- **Scanner:** `compuute-scan` v0.6.2 (37 L1 rules across 8 languages).
- **Scope-limited to:** L0 + L1 rule set (the open-source tier). Layer 2–4 manual triage was performed by Compuute as part of the batch; results below are post-triage.

## Raw output

| Severity | Raw findings | Post-triage confirmed |
|----------|-------------:|----------------------:|
| 🔴 Critical | 43 | 8 |
| 🟠 High | 24 | 6 |
| 🟡 Medium | 5 | 3 |
| 🟢 Low | 0 | 0 |

**False positive rate after triage: 76%** of raw findings did not survive manual review against the threat model. This is consistent with the ~90% historical raw FP rate documented in [docs/FP-RATES.md](../FP-RATES.md) — this repository's slightly lower rate reflects more careful upstream sanitization than the median MCP server.

## Confirmed findings (representative)

We present three of the 17 confirmed findings here. Vendor disclosure window for the full set runs through August 2026.

### Finding A — Tool-description injection vector

One tool accepted a free-text "context" parameter that was concatenated directly into a downstream LLM prompt without sanitization. A malicious caller could embed a prompt-injection payload that survived to the model layer.

**Recommendation accepted by vendor:** wrap user-controllable context fields in clearly-delimited structured blocks (`<user_input>...</user_input>`) and reject contents that contain injection markers.

### Finding B — SSRF in URL-fetching tool

A tool that fetched user-supplied URLs did not validate against private network ranges. An agent could pass `http://169.254.169.254/latest/meta-data` and receive cloud-instance metadata back.

**Recommendation:** validate against IP allowlist + explicit denylist for RFC 1918, link-local, and cloud-metadata endpoints. Vendor confirmed fix is in progress.

### Finding C — Credentials in error messages

When authentication failed, the error body included the partial credential string used for the attempt. An agent that received this error in its context would have the partial credential visible to subsequent reasoning steps.

**Recommendation:** sanitize credentials from error paths. Trivial 1-line fix in vendor's logging middleware.

## Triage process

Each of the 43 raw critical findings was assigned a verdict in one of four buckets:

- **Confirmed exploitable:** path traces from attacker-controlled input to the vulnerable sink, no compensating control blocks it. Count: 8.
- **Confirmed pattern but compensating control:** finding represents a known pattern but a guard upstream prevents exploitation. Count: 19.
- **Demo/test code:** finding is in code paths not reachable at runtime (example fixtures, test scaffolding). Count: 11.
- **Scanner false positive:** regex matched a syntactic shape that isn't actually the dangerous pattern. Count: 5.

This is the standard four-bucket triage we run on every batch — the disclaimer in every API response refers to this process.

## Outcome

- Vendor was contacted via responsible disclosure within 48 hours of the batch run.
- 17 confirmed findings filed with their security team.
- All critical findings either fixed or risk-accepted in writing within the 90-day disclosure window.
- A full public advisory (`COMPUUTE-2026-XXX`) will be published when the window closes; this case study is the redacted preview.

## What buyers should take away

- A 76% raw FP rate on this repo is **better than median** for production MCP servers. The L0 + L1 rule set is broad on purpose — the value is in the triage we apply, not in the raw count.
- 17 confirmed real findings in a heavily-reviewed open-source repo from a top-tier vendor suggests **other MCP servers are probably worse**. Most haven't been triaged at all.
- Time from "click run scan" to "have a triage queue" was under 30 minutes. Manual triage of the 43 critical findings took one senior security engineer about 4 hours.

## How this engagement was priced

This particular scan ran inside Compuute's monthly batch (no engagement fee). A vendor who commissions the same depth of work on their own repository should expect $5,000–$15,000 depending on size and complexity — see [the audit pricing](https://compuute.se/pricing).

---

*Case study prepared by Compuute AB. Scanner version, raw counts, triage verdicts, and remediation status are all factual. Vendor identity withheld until disclosure window closes (estimated August 2026). For questions: <daniel@compuute.se>.*
