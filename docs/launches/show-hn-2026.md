# Show HN: I scanned 19 production MCP servers and triaged what I found

> Drafted 2026-05-25. Daniel posts when ready. See "Posting checklist" at the bottom.

## Recommended posting time

**Tuesday 8:00 ET (14:00 CET)** — the empirically-best window for technical Show HN posts to land on the front page. Avoid Mondays (too much weekend backlog clearing) and Fridays (HN traffic drops after lunch). Avoid posting in the middle of a major OpenAI / Anthropic / Apple release day.

---

## Title (use exactly)

**Show HN: I scanned 19 production MCP servers and triaged what I found**

(80 chars including "Show HN: ". HN truncates around 80; keeps the headline complete.)

## URL field

`https://github.com/Compuute/compuute-scan`

## Body (paste exactly)

In May 2026 I ran a static scan across 19 publicly-available MCP (Model Context Protocol) servers from production vendors — Microsoft Azure DevOps MCP, Cloudflare MCP, the modelcontextprotocol/servers reference repo, several VC-backed agent-runtimes, etc. The scanner produced 3,486 raw findings. After manual triage, about 350 were confirmed exploitable under the Ox Security threat model. Roughly 90% of raw output is false positives — explicitly published per-rule on the project README.

The scanner itself is open-source MIT and built on Node.js built-ins only (zero deps). It runs `npx compuute-scan ./your-mcp-server` and produces a JSON or Markdown report. 37 rules across TS/JS, Python, Go, Rust, C#, Java, Kotlin — every language with an official MCP SDK.

What I think is interesting and probably wrong:

1. **MCP is now where agents discover and use tools, and almost no one has scanned the servers.** Anthropic Registry + Smithery + mcp.so list ~17,000 servers between them. Nearly all are untested by any static analyzer. The first 19 I picked had findings.

2. **The most common high-severity pattern is argument injection via the runner binary** (npx, uvx, pipx). `execFile('npx', userArgs)` looks safe — no shell — but npx interprets its own flags, so `--package=evil-pkg` smuggles attacker-controlled code past allowlists that check the package name. Rule L1-038 was added a week after Ox Security published the vector; the first batch run after the rule landed found a real exploitable instance in trycua/cua.

3. **Pattern detection is wrong without honest framing.** A scanner that reports 3,486 findings and lets the buyer believe they have 3,486 vulnerabilities damages trust on the first 30-second demo. Every API response carries a `_disclaimer` field stating the rule reads syntax, not data provenance. The methodology paper is at `docs/whitepaper/`.

4. **The cleanest big repo I scanned was Microsoft's Azure DevOps MCP** — 44 files, 407 tools exposed, 1 high finding. The noisiest was AWS Labs' multi-package MCP repo — 2,288 files, 66 critical raw (mostly FP due to monorepo test surfaces). Both are findable in the public results.

Hosted version: `POST https://scan.compuute.se/v1/scan` with `{"repo_url": "https://github.com/..."}`. No API key needed. There's a paid tier at $0.10 USDC per scan via x402 for agents without accounts, and a manual audit tier ($5K–$30K) for organizations that want the triage done for them.

Honest disclosures up front:

- The scanner is broad. ~90% raw FP rate. Triage is the product. The README has per-rule FP rates from my validation.
- I am an independent security consultant (Compuute AB, Stockholm). The hosted API exists partly as a lead-magnet for the audit business; the open-source CLI works fine standalone.
- Three case studies (anonymized vendors, real numbers) at `docs/case-studies/`.

I'm interested in: which other MCP server should I scan next, and what should I scan it for that I'm currently missing.

---

## First comment (drop this once the thread is rolling)

If you're skimming the thread for the methodology:

- 90% raw FP rate baseline: anchored on the modelcontextprotocol/servers reference repo, March 2026 (138 raw → 13 confirmed). Per-rule rates in `docs/FP-RATES.md`.
- Threat model: STRIDE adapted for MCP. Five adversaries (tool-description injection, argument injection, supply-chain, network, resource exhaustion). Documented in the whitepaper at `docs/whitepaper/`.
- L1-038 timing: Ox Security published the npx-argument-injection vector early May. compuute-scan v0.6.1 shipped L1-038 within seven days. Real finding surfaced in the next batch run (`docs/advisories/COMPUUTE-2026-001.md`, currently pre-disclosure).

If you want to skip the open-source CLI and just see the API:

    curl -X POST https://scan.compuute.se/v1/scan \
      -H 'Content-Type: application/json' \
      -d '{"repo_url":"https://github.com/<your-mcp-server>"}'

Happy to take feedback on the methodology, the rule set, or which findings I'm probably wrong about.

---

## Pre-flight checklist before posting

- [ ] All three case studies referenced are accessible:
  - https://github.com/Compuute/compuute-scan-api/blob/main/docs/case-studies/01-major-cloud-provider.md
  - https://github.com/Compuute/compuute-scan-api/blob/main/docs/case-studies/02-open-source-mcp-foundation.md
  - https://github.com/Compuute/compuute-scan-api/blob/main/docs/case-studies/03-agent-runtime-startup.md
- [ ] FP-rate doc accessible: https://github.com/Compuute/compuute-scan-api/blob/main/docs/FP-RATES.md
- [ ] Methodology paper accessible: https://github.com/Compuute/compuute-scan-api/blob/main/docs/whitepaper/mcp-security-methodology-v1.pdf
- [ ] Pricing page is live + parses cleanly: https://compuute.se/pricing
- [ ] Live API responds within 2s on a small repo (re-run `bash scripts/status.sh` immediately before posting)
- [ ] If SOC 2 readiness statement (#32) is published, swap the third bullet of "Honest disclosures" to mention it
- [ ] Daniel can sit at HN for the next 6 hours to reply to comments — abandonment kills front-page momentum

## Done-when

```bash
test -f docs/launches/show-hn-2026.md && wc -w docs/launches/show-hn-2026.md | awk '$1 >= 800' && echo PASS
```

(The post body itself is ~700 words; this doc with the wrapping checklists is ≥800.)

## KPI

- **Front-page criterion:** ≥50 upvotes within 3 hours of posting (HN front-page algorithm). Below that = doesn't surface, write off and retry in 4-6 weeks with a different angle.
- **30-day target:** ≥50 GitHub stars on Compuute/compuute-scan-api from non-Compuute accounts. (Stars from the original compuute-scan repo also count.)
- **Conversion target:** ≥1 prospect in the HN thread reaches out by DM/email for a paid engagement within 14 days.

## What we measure if it dies

If the post is not on the front page after 3 hours, **do not retry the same angle immediately**. Wait at least 4 weeks. Probable diagnoses:

1. Wrong timing — try Tuesday 8am ET specifically (most successful window for security posts).
2. Wrong title — "I scanned 19 production MCP servers and triaged what I found" is the strongest version we've drafted; if it underperforms, the next attempt should be tied to a specific newsworthy event (a published Anthropic security incident, a high-profile MCP exploit, etc.).
3. Wrong audience — HN over-indexes on individual engineers; if the audience here doesn't bite, the same content reformatted for a CISO-targeted publication (Risky Business, Dark Reading) is the next channel.
