# Progress log

Append-only daily summary. One section per work session.


## 2026-05-23 18:52 UTC

**Live version:** v0.3.0

**Commits since yesterday:**
- 9b58869 ci: fix release tarball — tar to /tmp to avoid file-changed-as-read (#5)
- 0a977a3 ci: SLSA L3 provenance + SBOM on release (#5)
- 227fa3e build: CycloneDX SBOM generation script + attach to v0.3.0/v0.4.0 (#4)
- 4589bc2 docs: scan-self triage transparency (#2)
- 4b0c318 fix: tighten CORS to explicit origin list (#2)
- 805e303 ci: pytest + ruff + bandit on push/PR (#3)
- 4fb1230 docs: add SECURITY.md with 90-day coordinated disclosure policy (#1)
- 3acb6ef docs: link BACKLOG.md to GitHub Project #6 board (#1)
- dae1563 infra: pre-flight backlog + hallucination guardrails (refs #1 #2 #3 #4 #5 #6)
- 08443c6 v0.4.0: agent + crawler discovery endpoints + MCP Registry server.json
- 2f62a15 chore: bump app.version → 0.3.0 (matches CHANGELOG and tag)
- a31cb78 v0.3.0: x402 pay-per-scan endpoint + comprehensive docs
- cb862b3 docs: agentic.market submission prep — three paths laid out
- efa5a23 fix: allow prod hosts in FastMCP transport_security
- d0581b6 v0.2.0: expose scan_mcp_server as MCP tool at /mcp/
- 77981f7 fix: drop railway.toml startCommand — Dockerfile CMD shells $PORT properly
- 8fb8011 Add Dockerfile + railway.toml for deploy
- 2466bbc Initial commit: compuute-scan-api v0.1.0

**Issues touched:**
  - #23 [CLOSED] [P0-3] Tag GitHub releases v0.3.0 and v0.4.0
  - #22 [OPEN] [P3-5] LinkedIn company page with 200+ followers
  - #21 [OPEN] [P3-4] CNA status (MITRE CVE Numbering Authority)
  - #20 [OPEN] [P3-3] OWASP MCP Security Project editor role
  - #19 [OPEN] [P3-2] ISO 27001 readiness
  - #18 [OPEN] [P3-1] SOC 2 Type II audit ($15-30K, 3 months)
  - #17 [OPEN] [P2-6] First paid pilot (-10K, optional discount or free-against-case-study)
  - #16 [OPEN] [P2-5] Show HN launch — '5K GitHub stars target'
  - #15 [OPEN] [P2-4] CONTRIBUTING.md and CODE_OF_CONDUCT.md
  - #14 [OPEN] [P2-3] Submit conference talk to SEC-T, OWASP Stockholm, BSides
  - #13 [OPEN] [P2-2] SOC 2 Type I readiness statement (signaling)
  - #12 [OPEN] [P2-1] Publish 3 anonymized case studies from nightly-batch
  - #11 [OPEN] [P1-6] Publish FP-rate per rule in CHANGELOG/scanner output
  - #10 [OPEN] [P1-5] First advisory under Compuute name (manual triage of nightly-batch findings)
  - #9 [OPEN] [P1-4] Analytics + conversion-funnel tracking
  - #8 [OPEN] [P1-3] Status page at status.compuute.se
  - #7 [OPEN] [P1-2] Penetration test of own infrastructure
  - #6 [OPEN] [P1-1] Write methodology whitepaper — How compuute-scan detects MCP threats
  - #5 [CLOSED] [P0-6] Add SLSA L2+ build attestation via slsa-github-generator
  - #4 [CLOSED] [P0-5] Generate CycloneDX SBOM on every release
  - #3 [CLOSED] [P0-4] Add .github/workflows/ci.yml — pytest + ruff + bandit on PR
  - #2 [CLOSED] [P0-2] Fix scanner-on-self FP (99 critical on own source code)
  - #1 [CLOSED] [P0-1] Add SECURITY.md with responsible disclosure email

**Tests:** 27 passed, 118 warnings in 1.23s

