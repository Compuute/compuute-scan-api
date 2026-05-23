# Development guide

For a new developer joining the project. Optimized for "get productive in 30 minutes."

## Prereqs

- Python 3.12+
- Node.js 20+ (for running compuute-scan locally)
- Docker Desktop (for testing the production image)
- Railway CLI (for deploys): `brew install railwayapp/cli/railway`
- A local clone of [compuute-scan](https://github.com/Compuute/compuute-scan) at `~/compuute-scan` — set `COMPUUTE_SCAN_PATH` env var if elsewhere

## Local setup (5 min)

```bash
git clone git@github.com:Compuute/compuute-scan-api.git
cd compuute-scan-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
export COMPUUTE_SCAN_PATH=$HOME/compuute-scan/compuute-scan.js
uvicorn main:app --reload --port 8000
```

Open:

- http://localhost:8000/docs — interactive OpenAPI explorer
- http://localhost:8000/v1/health — liveness check
- http://localhost:8000/openapi.json — machine-readable spec

Test a scan:

```bash
curl -X POST http://localhost:8000/v1/scan \
  -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/Compuute/compuute-scan"}'
```

## Run tests

```bash
pytest tests/ -v
```

All tests are pure or mock the service layer — no live network or Docker required. CI-friendly.

## Test the Docker image locally

```bash
docker build -t csa:test .
docker run --rm -p 18000:8000 csa:test
curl http://localhost:18000/v1/health
```

## Project layout

```
compuute-scan-api/
├── Dockerfile               # Production image: Python 3.12 + Node 20 + git + compuute-scan
├── railway.toml             # Railway config (no startCommand — Dockerfile CMD handles $PORT)
├── requirements.txt         # FastAPI, MCP SDK, httpx, pytest
├── main.py                  # FastAPI app, lifespan, route registration
├── api/
│   ├── routes/
│   │   ├── scan.py          # POST /v1/scan + GET /v1/scan/info
│   │   └── scan_x402.py     # POST /v1/scan/pay (x402 pay-per-scan)
│   ├── mcp_server.py        # FastMCP server with scan_mcp_server tool
│   ├── services/
│   │   ├── scan.py          # clone + run compuute-scan + parse — pure
│   │   └── x402_service.py  # x402 verify/settle via Coinbase facilitator
│   └── serializers/
│       └── scan_serializer.py  # Pydantic models, strict validation
├── tests/                   # pytest, no live deps
└── docs/                    # this directory
```

## Adding a new endpoint

1. **Define the request/response models** in `api/serializers/`.
2. **Add the route** in `api/routes/`. Reuse the cache + ETag helpers from `scan.py`.
3. **Add tests** in `tests/`. Mock `scan_repo` or other service calls — don't hit live.
4. **Register the router** in `main.py`.
5. **Update the MCP tool** in `api/mcp_server.py` if agents should be able to call it.
6. **Run `pytest`** locally. Then push — Railway redeploys on `git push origin main`.

## Adding a new compuute-scan version

1. Pin the new ref in `Dockerfile`:
   ```
   ARG COMPUUTE_SCAN_REF=v0.6.3
   ```
2. Bump the `version` field in `main.py` and any tests that pin it.
3. Push. Railway rebuilds; verify with `curl https://scan.compuute.se/v1/health`.

## Deploy

```bash
railway login           # interactive, browser-based
railway link            # link to existing project if not already
railway up              # builds + deploys
```

Or just push to `main` — Railway has GitHub-trigger deploys configured.

Verify deploy:

```bash
URL=https://scan.compuute.se
curl $URL/v1/health
curl -X POST $URL/v1/scan -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/Compuute/compuute-scan"}'
```

## Environment variables

| Var | Default | Purpose |
|-----|---------|---------|
| `PORT` | 8000 | Injected by Railway; uvicorn binds here |
| `COMPUUTE_SCAN_PATH` | `~/compuute-scan/compuute-scan.js` | Path to compuute-scan binary |
| `SCAN_CLONE_TIMEOUT` | 60 | Max seconds for `git clone` |
| `SCAN_TIMEOUT` | 120 | Max seconds for compuute-scan subprocess |
| `SCAN_MAX_REPO_SIZE_MB` | 200 | Reject larger repos with 413 |
| `X402_WALLET_ADDRESS` | (empty) | Coinbase wallet for USDC settlement. Empty → `/v1/scan/pay` returns 503 |
| `X402_PRICE_USD` | `0.10` | Price per scan via /v1/scan/pay |
| `X402_FACILITATOR_URL` | `https://x402.org/facilitator` | Override for self-hosted facilitator |

Set on Railway: `railway variables set X402_WALLET_ADDRESS=0x...`

## Common pitfalls

1. **`Cache-Control: no-store` overrides our route headers.** We don't ship a global security middleware that forces `no-store` (unlike lead-enrich-api). Don't add one without making `/v1/scan` an exception.
2. **`${PORT}` in `railway.toml` startCommand doesn't expand** — Railway runs that command without a shell. Use Dockerfile `CMD ["sh", "-c", "... ${PORT}"]` instead.
3. **FastMCP DNS-rebinding protection** defaults to localhost-only. Production hosts must be in `mcp_app.settings.transport_security.allowed_hosts`. See `api/mcp_server.py`.
4. **compuute-scan stdout truncates at ~64 KB pipe buffer.** We use `--output <file>` and read from disk. Don't change to capture stdout.
5. **The scanner exits non-zero when findings exist.** That's expected — don't `check=True` in subprocess.run.

## Code style

- `from __future__ import annotations` at the top of every Python file.
- Pydantic v2 (`ConfigDict`, `Field(..., description=...)`).
- Type hints on public functions.
- Docstrings on services and routes (they go into OpenAPI).
- No emojis in code or comments (per global CLAUDE.md rules).
- `structlog` for logging — never `print`, never `logging.info`.

## Code review checklist

Before merging a PR:

- [ ] `pytest tests/` passes
- [ ] OpenAPI lists the new endpoint with description + examples
- [ ] MCP tool description follows Anthropic best practices (WHEN/WHEN NOT/EXAMPLES) if exposed to agents
- [ ] No private imports from other modules (no `_underscore_name` cross-module)
- [ ] No hardcoded secrets — use env vars
- [ ] `_disclaimer` field present in any new response shape, matching L1-038 honest-framing pattern
