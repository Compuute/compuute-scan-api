# CrewAI marketplace submission

This directory contains the CrewAI-flavored variant of the LangChain integration. Both wrap the same `https://scan.compuute.se/v1/scan` endpoint.

## What's here

- [`compuute_scan_tool.py`](compuute_scan_tool.py) — the `crewai.tools.BaseTool` subclass. ~80 lines.

## Why CrewAI (in addition to LangChain)

CrewAI's positioning is multi-agent crews with clearly-assigned roles. A "pre-flight auditor" agent that runs `compuute_scan_mcp_server` before the crew's installer agent connects to a new MCP server is the natural shape — and CrewAI's tutorial flow already demonstrates this pattern for non-security tools.

CrewAI marketplace (https://app.crewai.com/marketplace) accepts community tools through a submission form rather than a PR. Submission shape:

1. Tool name + description (copy from the docstring)
2. Source URL pointing to the file
3. Install command (we will publish to PyPI as `crewai-compuute-scan` when traffic justifies — for v0 the README points users to drop the file in directly)
4. Example crew showing the auditor-then-installer pattern

## Daniel's submission checklist

1. Sign in at https://app.crewai.com using GitHub
2. Marketplace → Submit Tool
3. Use:
   - **Name:** `compuute_scan_mcp_server`
   - **Description:** copy from the docstring at the top of `compuute_scan_tool.py`
   - **Source URL:** point at the GitHub-raw URL of the file in this repo
   - **Tags:** `security`, `mcp`, `audit`, `pre-flight`
   - **License:** MIT (matches compuute-scan-api)
4. Example snippet for the marketplace listing (paste the auditor-then-installer pattern from the docstring)

## v0 vs v1 plan

- **v0 (now):** users drop the file in their CrewAI project, no PyPI install. Same as the LangChain "drop-in" pattern. Acceptable for early adopters.
- **v1 (when traffic ≥ 100 scans/month from CrewAI agents):** publish as `crewai-compuute-scan` on PyPI. The lift is ~1h: setup.py + GitHub Actions release workflow + first version tag. Gate the lift behind real demand.

## KPI

Same as LangChain submission — Railway logs filtered for `User-Agent: crewai-compuute-scan-tool/1.0` on `POST /v1/scan`. 30-day target: ≥50 invocations across all CrewAI sources (smaller target than LangChain because CrewAI's installed base is smaller in 2026).
