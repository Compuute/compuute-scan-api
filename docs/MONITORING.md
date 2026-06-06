# Monitoring + automated progress checks

Goal: a single command answers "is anything broken, what's the trend, what do I need to act on?"

## The 30-second check

```bash
bash scripts/status.sh
```

(See script below; commit it to the repo so a new dev or a cron job can run it.)

Reports:

- Is `scan.compuute.se` returning 200 on `/v1/health`?
- Is the scanner binary present?
- Is the OpenAPI spec retrievable?
- Is `/mcp/` responding to initialize?
- Last 5 calls + their HTTP codes (from Railway logs).
- Latest GitHub release of `compuute-scan` vs version bundled in the deployed image.

## Live endpoints to bookmark

### Service health

| URL | What it tells you |
|-----|-------------------|
| https://scan.compuute.se/v1/health | Liveness + `scanner_available` flag + version |
| https://scan.compuute.se/v1/scan/info | Scanner version + limits + supported ecosystems |
| https://scan.compuute.se/openapi.json | Surface area — should always parse as valid JSON |
| https://scan.compuute.se/docs | Swagger UI render — visual sanity check |

### Discovery surfaces (verify these stay reachable; Smithery / Anthropic Registry / Coinbase Agent.market probe them)

| URL | Probe expected from |
|-----|---------------------|
| https://scan.compuute.se/.well-known/agent.json | Google A2A clients |
| https://scan.compuute.se/.well-known/agent-card.json | A2A clients using `-card.json` naming |
| https://scan.compuute.se/.well-known/ai-plugin.json | OpenAI ChatGPT |
| https://scan.compuute.se/.well-known/x402.json | Coinbase Agent.market crawlers, x402 aggregators |
| https://scan.compuute.se/.well-known/x402 | x402 probes without `.json` suffix |
| https://scan.compuute.se/robots.txt | Google / Bing |
| https://scan.compuute.se/sitemap.xml | Same |

### Public listings (broken-link checks worth running monthly)

| URL | Purpose |
|-----|---------|
| https://registry.modelcontextprotocol.io/v0/servers?search=compuute-scan-api | Anthropic Registry entry |
| https://smithery.ai/servers/daniel-abbay/compuute-scan-api | Smithery listing |
| https://mcp.so/server/compuute-scan-api | mcp.so listing |
| https://compuute.se/pricing | Pricing page (JSON-LD must validate against schema.org) |

### Infrastructure

| URL | What it tells you |
|-----|-------------------|
| https://railway.com/project/e464f658-f3c0-4b34-85cc-1ace8dbccbfe | Railway metrics + logs |
| https://github.com/Compuute/compuute-scan-api | Repo state |
| https://github.com/Compuute/compuute-scan | Upstream scanner releases |
| https://basescan.org/address/0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67 | x402 wallet balance + tx history |

## Railway built-in monitoring

- **Logs**: `railway logs --deployment` (live tail) or `railway logs --deployment | tail -200`
- **Metrics**: in the Railway dashboard → service → Metrics tab (CPU, memory, request rate, response time)
- **Healthcheck**: configured in `railway.toml` to hit `/v1/health` post-deploy

## Recommended automated checks

### A — Synthetic uptime probe (already free)

UptimeRobot or BetterStack on:

- `GET https://scan.compuute.se/v1/health` — expect 200
- Frequency: every 5 min
- Alert channel: email + Slack (whatever Compuute AB uses)

Setup time: 10 min, $0 free tier.

### B — Daily smoke scan (cron job on your laptop or a free GitHub Action)

```yaml
# .github/workflows/daily-smoke.yml
name: Daily smoke scan
on:
  schedule:
    - cron: '0 7 * * *'   # 07:00 UTC daily
  workflow_dispatch:
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -fsS https://scan.compuute.se/v1/health | jq -e '.scanner_available == true'
          curl -fsS -X POST https://scan.compuute.se/v1/scan \
            -H 'Content-Type: application/json' \
            -d '{"repo_url":"https://github.com/Compuute/compuute-scan"}' \
            | jq -e '.scanner.version'
```

Alerts if the smoke scan ever fails.

### C — Upstream version drift check

Notify when `Compuute/compuute-scan` releases a new tag and the deployed image is behind:

```bash
DEPLOYED=$(curl -s https://scan.compuute.se/v1/scan/info | jq -r '.supported_ecosystems' >/dev/null 2>&1
            && curl -s https://scan.compuute.se/v1/health | jq -r '.scanner_path')
LATEST=$(gh release view --repo Compuute/compuute-scan --json tagName -q .tagName)
# Compare LATEST against Dockerfile's COMPUUTE_SCAN_REF
grep -o "COMPUUTE_SCAN_REF=[^ ]*" Dockerfile
```

This catches: "L1-038-style fix shipped upstream but our image is stale."

## Logging conventions

All structured via `structlog`. Key event names:

| Event | When | Useful fields |
|-------|------|---------------|
| `scan_complete` | Successful scan | `repo`, `score`, `critical`, `high`, `files` |
| `scan_failed` | Service-layer ScanError | `code`, `repo`, `message` |
| `scan_unhandled` | Unexpected exception | `repo`, `error` |
| `scan_idempotent_hit` | Idempotency-Key cache hit | `idempotency_key`, `repo` |
| `scan_x402_complete` | Paid scan succeeded | `repo`, `score`, `critical`, `high` |
| `x402_payment_verified` | Facilitator confirmed payment | `price_usd` |
| `x402_payment_invalid` | Facilitator rejected payment | `result` |
| `mcp_scan_failed` | MCP tool returned an error | `code`, `repo` |
| `mcp_server_mounted` | At startup, MCP successfully attached | — |

Search Railway logs by event name to triage:

```bash
railway logs --deployment | grep '"event": "scan_failed"' | tail
```

## Failure-mode runbook

| Symptom | Likely cause | First fix |
|---------|--------------|-----------|
| `/v1/health` returns 5xx | Container crashed | `railway logs --deployment | tail -50`; look for Python traceback |
| `scanner_available: false` | Dockerfile build dropped compuute-scan | Re-deploy. If persists: `docker build` locally + inspect `/opt/compuute-scan` |
| `/mcp/` returns "Invalid Host header" | New custom domain added without updating `transport_security.allowed_hosts` | Add host to `api/mcp_server.py`, redeploy |
| `clone_timeout` for every repo | Outbound network blocked or facilitator down | Check Railway egress; try a known small repo via `railway shell` |
| `scanner_bad_json` | New compuute-scan release changed output format | Pin Dockerfile to previous `COMPUUTE_SCAN_REF`; file upstream issue |
| Cache headers missing on response | Middleware ordering changed | `pytest tests/test_scan.py::test_post_scan_happy_path_carries_cache_headers` |
| Tests fail locally but pass on CI (or vice versa) | Python version drift | Check `python --version` matches 3.12 |

## When something breaks

1. Check `/v1/health` first — if it's 5xx, the service is down.
2. `railway logs --deployment | tail -100` — look for Python traceback or `ERROR` events.
3. Run `pytest tests/` locally — confirms code paths still work in isolation.
4. If recent deploy: `git log --oneline -5` — bisect by reverting commits.
5. Worst case: roll back via Railway dashboard → Deployments → previous → Redeploy.

## Progress dashboards we don't need

These would be nice-to-have but are not built (and shouldn't be until demand justifies it):

- Custom Grafana / Datadog — Railway's built-in metrics are enough at this scale.
- Per-customer usage dashboards — no per-customer auth yet (free tier).
- Revenue dashboard — x402 not enabled; when it is, Coinbase wallet UI is enough.

Add these only when traffic ≥ 100 calls/day **and** at least one paid customer asks for usage data.
