# SOC 2 Type I — Readiness Statement

> **Status as of 2026-06-06:** Type I readiness work in progress. Type I audit window targeted Q4 2026. Type II audit window targeted Q2 2027. This document is updated whenever controls change or audit milestones land.

## Purpose

This document publishes Compuute AB's current security control posture mapped to the AICPA Trust Service Criteria (TSC) categories that SOC 2 covers. It exists so that:

1. **Enterprise procurement teams** can complete vendor-onboarding questionnaires today, before Type I is formally signed
2. **Buyer-agents** evaluating us against the [11 signals](../agent-economy-strategy.md#2-the-11-signals-buyer-agents-evaluate) framework see a published trust-center page
3. **Compuute** maintains a single source of truth for what we claim to do and what we actually do

This is a **readiness statement**, not an audit report. We document the control state honestly; the formal attestation lands when a third-party auditor signs off.

## Scope

The SOC 2 boundary covers:

- The hosted service at `scan.compuute.se` (compuute-scan-api)
- The supporting infrastructure on Railway (EU region)
- The build pipeline (GitHub Actions for ci.yml + release.yml producing CycloneDX SBOM + SLSA L3 provenance)
- Source code in `Compuute/compuute-scan` and `Compuute/compuute-scan-api`

Out of scope:

- The lead-enrichment service at `leads.compuute.se` (separate service, separate audit boundary, planned for 2027)
- compuute.se marketing site (Vercel hosting, no customer data, no audit boundary)

## Control mapping (TSC categories)

### CC1 — Control Environment

| Control | State | Evidence |
|---------|:-----:|----------|
| Documented organizational structure | ✅ | Compuute AB is a registered Swedish AB; Daniel Abbay is sole owner and operator. Public LinkedIn record. |
| Documented role responsibilities | ✅ | [CONTRIBUTING.md](../../CONTRIBUTING.md), [AGENTS.md](../../AGENTS.md) |
| Code of conduct | ⏳ Planned | Track in P3 backlog |
| Independence and ethics commitment | ✅ | Independent consultancy; no undisclosed vendor relationships. Documented in [STRATEGY.md](../STRATEGY.md) decision log. |

### CC2 — Communication and Information

| Control | State | Evidence |
|---------|:-----:|----------|
| Security policy publicly documented | ✅ | [SECURITY.md](../../SECURITY.md) — 90-day coordinated disclosure window |
| Incident response process | ⚠️ Partial | Disclosure process documented; internal incident response runbook is informal (single-operator scale) |
| Vulnerability reporting channel | ✅ | security@compuute.se published; advisories tracked in `docs/advisories/` |
| Customer-facing change notifications | ⏳ Planned | When first paying customer lands; not in current scope |

### CC3 — Risk Assessment

| Control | State | Evidence |
|---------|:-----:|----------|
| Threat model documented | ✅ | [docs/whitepaper/mcp-security-methodology-v1.md](../whitepaper/mcp-security-methodology-v1.md) §1 + [docs/ARCHITECTURE.md](../ARCHITECTURE.md) Threat model section |
| Risk-acceptance process | ✅ | Documented per-finding in [docs/security/own-pentest-2026-q2.md](../security/own-pentest-2026-q2.md) |
| Periodic re-assessment | ✅ | Self-pentest cadence is 90 days; next 2026-08-23 |

### CC4 — Monitoring Activities

| Control | State | Evidence |
|---------|:-----:|----------|
| Logging | ✅ | structlog throughout the codebase; Railway log retention |
| Continuous monitoring of production | ⚠️ Partial | Railway healthcheck + on-demand `scripts/status.sh`. Status page (P1-3) pending sign-up |
| Alerting on availability incidents | ⏳ Planned | Tied to status page work — BetterStack setup queued |
| Self-pentest review | ✅ | 90-day cadence; one full pass done (2026-05-23) |

### CC5 — Control Activities (Software development)

| Control | State | Evidence |
|---------|:-----:|----------|
| Source-code version control | ✅ | GitHub, all commits via authenticated Compuute identity |
| Code review before merge | ⚠️ Partial | Solo author; review is single-eye + CI checks. Multi-eye review when first contractor onboards |
| CI pipeline running tests + lint + security checks | ✅ | `.github/workflows/ci.yml` runs pytest + ruff + bandit on every PR |
| Reproducible builds | ✅ | Dockerfile pins `COMPUUTE_SCAN_REF=v0.6.2`; vendored at build time |
| Software bill of materials (SBOM) | ✅ | CycloneDX 1.5 generated via `scripts/sbom.sh`, attached to every GitHub Release |
| Build provenance / supply-chain attestation | ✅ | SLSA L3 provenance attached to v0.4.0 via `.github/workflows/release.yml` |

### CC6 — Logical and Physical Access Controls

| Control | State | Evidence |
|---------|:-----:|----------|
| Authentication for source code (GitHub) | ✅ | 2FA required on Compuute org; SSO planned when first team member joins |
| Authentication for production infrastructure (Railway) | ✅ | 2FA on Railway account |
| Authentication for payment infrastructure (Coinbase wallet, Stripe) | ✅ | Hardware-key 2FA on both |
| Least-privilege on hosting | ✅ | Railway service-token per-service scope |
| Encryption in transit | ✅ | TLS 1.2+, HSTS `max-age=63072000; includeSubDomains` |
| Encryption at rest | ✅ | Railway-managed; per their security documentation |
| Physical access controls | ✅ | Inherited from Railway data-center providers (Hetzner, AWS) |

### CC7 — System Operations

| Control | State | Evidence |
|---------|:-----:|----------|
| Capacity planning | ⚠️ Partial | Single-instance MVP; horizontal scale plan documented in [ARCHITECTURE.md](../ARCHITECTURE.md). Not yet exercised. |
| Backup and recovery | N/A | Stateless service; no customer data stored. Source code backed up via GitHub. |
| Vulnerability management | ✅ | compuute-scan runs against this codebase periodically (self-scan documented in `docs/scan-self-triage.md`) |
| Change management | ✅ | Branch + PR + CI gate for every change; deploys via Railway auto-deploy on merge |

### CC8 — Change Management

| Control | State | Evidence |
|---------|:-----:|----------|
| Documented release process | ✅ | `docs/whitepaper/`, `CHANGELOG.md`, `BACKLOG.md` |
| Tagged immutable releases | ✅ | v0.3.0, v0.4.0; per global CLAUDE.md rule 3, released tags never move |
| Rollback capability | ✅ | Railway Instant Rollback (single click); git history is the source of truth |

### CC9 — Risk Mitigation

| Control | State | Evidence |
|---------|:-----:|----------|
| Insurance | ⏳ Planned | Professional liability quote requested; documented when bound |
| Disaster recovery plan | ⚠️ Partial | Stateless service; recovery = re-deploy from git. Documented but not exercised. |
| Vendor risk assessment | ✅ | Vendor list: Railway, GitHub, Cloudflare (DNS), Coinbase, Anthropic. Each evaluated; documented in this file's appendix on first audit cycle. |

## Additional Trust Service Categories (planned for Type II)

| Category | Plan |
|----------|------|
| Availability (A) | Will commit to a 99.5% uptime SLO once status.compuute.se is live and we have 90 days of measured uptime data |
| Confidentiality (C) | Stateless service stores no customer data; confidentiality posture is straightforward |
| Processing Integrity (PI) | Triage disclaimer + per-rule FP-rate transparency are our processing-integrity commitments; documented and enforced |
| Privacy (P) | Out of scope for Type I; will revisit if we add customer-data-handling features |

## Roadmap to Type I attestation

1. **Q3 2026** — Sign up to Vanta or Drata for evidence-collection automation (Daniel-action; queued)
2. **Q3 2026** — Close the ⏳ Planned items above; promote ⚠️ Partial items to ✅ where feasible at single-operator scale
3. **Q3 2026** — Select auditor; budget approximately $15K for first-year Type I engagement
4. **Q4 2026** — Type I audit window opens; results published in this document
5. **Q1 2027** — Type II observation window opens (3-month minimum)
6. **Q2 2027** — Type II report published

## How to use this document

**Procurement teams**: this is the answer to "send us your security questionnaire." Most TSC categories are addressed; mark our state honestly and request the auditor attestation when it lands. Email `security@compuute.se` for follow-up.

**Buyer-agents**: this page is the "trust center" signal in the [11-signal evaluation framework](../agent-economy-strategy.md). It is linked from the [pricing page](https://compuute.se/pricing).

**Future Compuute team members or contractors**: this is the binding statement of what we claim. If you discover a control is weaker than what's documented here, that is a finding — file an issue and we will fix it or update the doc.

## Honesty pin

This is a **readiness statement, not an audit report.** Specifically:

- We have ✅ in 23 of 31 controls documented above. That is honest single-operator scale.
- We have ⚠️ Partial in 5, ⏳ Planned in 3.
- The Type I attestation does not exist yet. It will when a third-party auditor signs.

Compuute AB does not claim to be SOC 2 certified, SOC 2 attested, or SOC 2 audited until that audit lands. Anyone reading marketing copy that says otherwise should email `daniel@compuute.se` so we can fix the marketing copy.

---

*Last updated: 2026-06-06. Next review: when first ⚠️ Partial or ⏳ Planned item changes state, OR 2026-09-06, whichever comes first.*
