# LangChain Hub submission

This directory contains the LangChain integration for compuute-scan, ready to submit as a PR against `langchain-ai/langchain-community`.

## What's here

- [`compuute_scan_tool.py`](compuute_scan_tool.py) — the `BaseTool` subclass. ~110 lines.
- [`test_compuute_scan_tool.py`](test_compuute_scan_tool.py) — 7 unit tests covering metadata, schema validation, happy path, and error paths.

## Why this should ship in langchain-community

LangChain agents that install or connect to third-party MCP servers today have no built-in security check. The most common pattern in agent codebases is:

```python
from langchain_mcp import MCPToolkit

toolkit = MCPToolkit(server_url="https://random-mcp-server.example.com/mcp")
```

That URL is trusted by default. With agents now installing tools from public registries (Anthropic MCP Registry, Smithery, mcp.so — 17,000+ entries between them), the risk of pulling in a malicious or vulnerable server is real and growing.

`CompuuteScanTool` is the cheapest pre-flight check available: free tier, no API key, ~1-2 second response. The agent calls it once per new MCP server URL and gets back severity counts + top findings + a triage disclaimer.

## Honesty pin in the tool description

Per LangChain's [tool-design best practices](https://docs.langchain.com/docs/contributing/tools), tools should clearly state what they do AND what they don't.

The tool description embeds:

- What it does: scan + score + top findings
- What it doesn't: assert exploitability (it's a pattern detector with ~90% raw FP rate)
- When to use: BEFORE installing/connecting to an unknown MCP server
- Cost / latency expectations: free, 1-2s typical, 60s hard timeout

LLMs that read this description correctly will treat the tool output as a triage queue, not as a list of confirmed vulnerabilities.

## Proposed PR text

**Title:**

> feat(community/tools): add CompuuteScanTool for MCP-server security pre-flight

**Body:**

```
Adds a thin LangChain BaseTool wrapper around the open-source
compuute-scan project's hosted API (https://scan.compuute.se/v1/scan).

Use case: agents that install or connect to third-party MCP servers
should perform a security pre-flight check before trusting the
endpoint. compuute-scan is MCP-specific (37 rules covering MCP attack
surfaces across TS/JS, Python, Go, Rust, C#, Java, Kotlin) and
publishes a transparent ~90% raw false-positive rate, so the tool
description correctly frames findings as a triage queue.

API: free tier, no key required, ~1-2s typical latency, 60s hard
timeout. Source code is MIT-licensed at github.com/Compuute/compuute-scan-api.

Tests: 7 unit tests cover input validation, happy path, and the four
error paths (422 / 504 / 5xx / network error).

Honesty note matches LangChain's tool-design best practices: tool
description states what it does, what it does NOT (assert
exploitability), when to use it (BEFORE installing), and the cost
expectations.
```

## Daniel's submission checklist

When you're ready to submit:

1. Fork [`langchain-ai/langchain`](https://github.com/langchain-ai/langchain) (or `langchain-community` if separated by the time of submission)
2. Copy `compuute_scan_tool.py` to `libs/community/langchain_community/tools/compuute_scan/`
3. Copy `test_compuute_scan_tool.py` to `libs/community/tests/unit_tests/tools/test_compuute_scan.py`
4. Run their CI checklist locally: `make format && make lint && make test`
5. Open the PR with the text above
6. Reply to maintainer review within 3 days; this is a small enough surface that approval typically lands in 2-4 weeks

## CrewAI equivalent

CrewAI also accepts tool contributions but their integration shape is slightly different (Tool class inherits from `crewai.tools.BaseTool`). The Python class can be adapted in ~20 lines — see `../crewai/` for the parallel submission.

## KPI we're measuring against

The closest KPI we can verify externally is GitHub stars on `Compuute/compuute-scan-api`. Indirectly, LangChain downloads of `langchain-community` are a leading indicator.

30-day target: ≥100 invocations of the tool in the wild. Measured indirectly via Railway logs filtering for `User-Agent: langchain-compuute-scan-tool/1.0` on `POST /v1/scan`.
