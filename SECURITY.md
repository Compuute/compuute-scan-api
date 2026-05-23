# Security Policy

Compuute AB takes the security of `compuute-scan-api` and its consumers seriously. This document describes how to report vulnerabilities, what's in scope, and how we coordinate disclosure.

## Reporting a vulnerability

Email **security@compuute.se** with:

- A description of the issue, including the smallest reproduction steps you have
- Affected version(s) — the deployed live version is reported at `https://scan.compuute.se/v1/health`
- Your name / handle as you'd like it credited (or "anonymous")
- Optional: encrypted via the contact's GPG key — fingerprint will be published on `https://compuute.se/.well-known/security.txt` (forthcoming).

We acknowledge receipt within **3 business days** and provide a triage update within **7 business days**.

Please **do not** open a public GitHub issue for security reports.

## In scope

- The live service at `https://scan.compuute.se` and all its subpaths.
- The MCP endpoint at `https://scan.compuute.se/mcp/`.
- The x402 payment endpoint at `https://scan.compuute.se/v1/scan/pay`.
- Source code in this repository (`Compuute/compuute-scan-api`) on the `main` branch and any released tag.

The bundled scanner (`compuute-scan`) is in its own repository: report scanner-specific issues to that project's `SECURITY.md`.

## Out of scope

- Findings produced by our scanner against third-party MCP servers (those are intended outputs; report content concerns to the affected vendor via their own disclosure process)
- Volumetric DDoS without a novel amplification or bypass vector
- Issues requiring already-compromised client devices or upstream Coinbase Facilitator misuse
- Self-XSS or social-engineering reports without a software defect
- Outdated dependency reports without a working exploit path against this service specifically

## Disclosure policy

We follow a **90-day coordinated disclosure window** by default, modeled on Project Zero's policy:

- Day 0: receipt acknowledged
- Day 1–7: triage and severity classification (CVSS v4 where applicable)
- Day 7–60: fix implemented, validated, deployed
- Day 60–90: coordination on advisory text, CVE request if applicable
- Day 90 (or earlier if fix is live and reporter agrees): public advisory at `docs/advisories/COMPUUTE-YYYY-NNN.md`

If a vulnerability is being actively exploited in the wild we will accelerate this timeline and may publish before day 90 in coordination with the reporter.

## Recognition

We publish a `SECURITY-HALL-OF-FAME.md` listing each reporter who agreed to be named, in the order their report was triaged. Compuute AB does not currently run a paid bug bounty, but we offer:

- Public credit in the advisory and the hall-of-fame file
- A LinkedIn endorsement from Daniel Abbay
- Where applicable, a co-authorship credit on the public write-up

## Supply-chain note

`compuute-scan-api` is intentionally minimal: zero direct dependencies beyond FastAPI, Pydantic, httpx, mcp-sdk, and uvicorn — see `requirements.txt`. The bundled `compuute-scan` is itself zero-dependency. We generate a CycloneDX SBOM for each release (see `BACKLOG.md` issue #4) and ship SLSA L2+ provenance attestation (issue #5).

## Owner

- **Maintainer**: Daniel Abbay — daniel@compuute.se
- **Security contact**: security@compuute.se
- **Public homepage**: https://compuute.se
- **Service status**: `https://scan.compuute.se/v1/health` (planned: `https://status.compuute.se`)

Last updated: 2026-05-23.
