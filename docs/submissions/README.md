# Framework submissions

Ready-to-submit integrations for the major agent frameworks.

| Framework | Path | Status |
|-----------|------|--------|
| LangChain | [`langchain/`](langchain/) | Drafted; awaiting Daniel's PR against `langchain-ai/langchain` |
| CrewAI | [`crewai/`](crewai/) | Drafted; awaiting Daniel's marketplace form submission |
| AutoGen | (planned) | Not started; gated by ≥50 GitHub stars on this repo first |
| Cursor / Goose / Claude Desktop MCP-recommendations | (planned) | Each maintains a list; submissions are issue/PR-based, batch when traffic justifies |

## Why this directory exists

Per [agent-economy-strategy.md](../agent-economy-strategy.md), Spår A (micropayment-tier) wins by becoming a default in the frameworks where agents are built. Each subdirectory here is one shot at that — fully drafted so Daniel only has to file the PR or form.

The code is identical in shape across the wrappers (thin HTTP wrapper around `POST /v1/scan`). The differences are framework-specific Tool-class plumbing and submission-flow ceremony.

## Tracking

Submissions land via Daniel's GitHub identity (langchain) or his CrewAI account (crewai). Once accepted, we measure traffic via `User-Agent` headers on the upstream `/v1/scan` endpoint, with one per framework.
