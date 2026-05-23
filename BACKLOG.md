# Backlog — compuute-scan-api

Single-glance roadmap. Each item links to a GitHub Issue with an acceptance criterion (a runnable command that proves it's done).

**Reading order:** P0 → P1 → P2 → P3. Don't skip levels — each unlocks the credibility for the next.

Last reviewed: 2026-05-23 (initial creation).

---

## 🔴 P0 — Credibility baseline

> Must-do before any cold outreach. Without these, any prospect doing 5 minutes of due diligence sees an indie project and bounces.

**Milestone:** [P0 — credibility baseline](https://github.com/Compuute/compuute-scan-api/milestone/1)

| # | Title | Estimate |
|---|-------|---------:|
| [#1](https://github.com/Compuute/compuute-scan-api/issues/1) | Add SECURITY.md with responsible disclosure email | S (15m) |
| [#2](https://github.com/Compuute/compuute-scan-api/issues/2) | Fix scanner-on-self FP (99 critical on own code) | M (1h) |
| [#3](https://github.com/Compuute/compuute-scan-api/issues/3) | Tag GitHub releases v0.3.0 and v0.4.0 | S (5m) |
| [#4](https://github.com/Compuute/compuute-scan-api/issues/4) | Add .github/workflows/ci.yml — pytest + ruff + bandit | S (30m) |
| [#5](https://github.com/Compuute/compuute-scan-api/issues/5) | Generate CycloneDX SBOM on every release | M (20m) |
| [#6](https://github.com/Compuute/compuute-scan-api/issues/6) | Add SLSA L2+ build attestation | M (30m) |

**Total:** ~2.5h focused work. Unlocks: cold outreach without procurement-checklist-fail.

---

## 🟡 P1 — Track record

> Build credibility evidence buyers can verify independently.

**Milestone:** [P1 — track record](https://github.com/Compuute/compuute-scan-api/milestone/2)

| # | Title | Estimate |
|---|-------|---------:|
| [#7](https://github.com/Compuute/compuute-scan-api/issues/7) | Methodology whitepaper — MCP threat detection | L (4-8h) |
| [#8](https://github.com/Compuute/compuute-scan-api/issues/8) | Penetration test of own infrastructure | L (6h) |
| [#9](https://github.com/Compuute/compuute-scan-api/issues/9) | Status page at status.compuute.se | S (30m) |
| [#10](https://github.com/Compuute/compuute-scan-api/issues/10) | Analytics + conversion-funnel tracking | S (30m) |
| [#11](https://github.com/Compuute/compuute-scan-api/issues/11) | First advisory under Compuute name | L (90d window) |
| [#12](https://github.com/Compuute/compuute-scan-api/issues/12) | Publish FP-rate per rule | M (1h) |

**Total:** ~15h focused + 90-day disclosure window. Unlocks: response to "show me your methodology".

---

## 🟢 P2 — Adoption acceleration

> Once track record exists, drive demand.

**Milestone:** [P2 — adoption acceleration](https://github.com/Compuute/compuute-scan-api/milestone/3)

| # | Title | Estimate |
|---|-------|---------:|
| [#13](https://github.com/Compuute/compuute-scan-api/issues/13) | 3 anonymized case studies | M (4h) |
| [#14](https://github.com/Compuute/compuute-scan-api/issues/14) | SOC 2 Type I readiness statement | L (8h init) |
| [#15](https://github.com/Compuute/compuute-scan-api/issues/15) | Submit talks to SEC-T, OWASP, BSides | M (1h) |
| [#16](https://github.com/Compuute/compuute-scan-api/issues/16) | CONTRIBUTING.md and CODE_OF_CONDUCT.md | S (30m) |
| [#17](https://github.com/Compuute/compuute-scan-api/issues/17) | Show HN launch — 100+ star target | M (4h + day-of) |
| [#18](https://github.com/Compuute/compuute-scan-api/issues/18) | First paid pilot ($1-10K) | variable |

**Total:** ~18h focused + sales cycle. Unlocks: revenue.

---

## 🔵 P3 — Enterprise readiness

> Long-tail. Only after P0-P2 proven.

**Milestone:** [P3 — enterprise readiness](https://github.com/Compuute/compuute-scan-api/milestone/4)

| # | Title | Estimate |
|---|-------|---------:|
| [#19](https://github.com/Compuute/compuute-scan-api/issues/19) | SOC 2 Type II audit | XL (3mo, $15-30K) |
| [#20](https://github.com/Compuute/compuute-scan-api/issues/20) | ISO 27001 readiness | XL (6mo) |
| [#21](https://github.com/Compuute/compuute-scan-api/issues/21) | OWASP MCP Security Project editor role | M (1h apply) |
| [#22](https://github.com/Compuute/compuute-scan-api/issues/22) | CNA status (MITRE CVE Numbering Authority) | XL (3-6mo) |

**Total:** 6+ months calendar time. Unlocks: enterprise procurement at >250-employee companies.

---

## How to work this backlog

1. **Start each session with `bash scripts/precheck.sh`** — confirms live state + lists active issues
2. **One issue at a time.** Don't grab P1 if P0 is open.
3. **Branch per issue:** `git checkout -b fix/issue-N-short-name`
4. **Commit with issue ref:** message must contain `#N` (pre-commit hook enforces)
5. **Close issue with proof:** the closing comment must contain the `Done when:` command output
6. **End each session with `bash scripts/postcheck.sh`** — appends a daily entry to `docs/PROGRESS.md`

## Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-23 | Created backlog with 22 issues across 4 milestones | After data-driven multi-hat review scored project at 4.5/10. P0-P3 are the gap to 8+/10. |
| 2026-05-23 | Per-issue acceptance criteria = runnable command | Prevents subjective "I think it's done" claims. Mechanical verification only. |
| 2026-05-23 | No labels added (gh CLI rejected non-default labels) | Will retry via gh api when needed; not blocking. |
