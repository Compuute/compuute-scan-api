# Architecture

## Purpose

`compuute-scan-api` is an HTTP + MCP wrapper around [compuute-scan](https://github.com/Compuute/compuute-scan) (a Node.js static analyzer for MCP servers). It exposes the scanner over three surfaces:

- **REST**  `POST /v1/scan` — for human-operated tools and dashboards
- **MCP**   `/mcp/` with `scan_mcp_server` tool — for autonomous AI agents
- **x402**  `POST /v1/scan/pay` — for pay-per-use without API keys (Agentic.market-compatible)

The scanner itself is unchanged. This service exists because compuute-scan is a single-file CLI with zero deps, while real consumption needs idempotency, caching, rate limits, payment, and machine-readable metadata.

## Component diagram

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                Railway (production)                       │
                    │                                                           │
  Public HTTPS      │   ┌─────────────────────────────────────────────────┐   │
  scan.compuute.se ─┼──▶│  FastAPI (uvicorn, single instance)             │   │
                    │   │                                                   │   │
                    │   │  /v1/scan       ─── api/routes/scan.py          │   │
                    │   │  /v1/scan/pay   ─── api/routes/scan_x402.py     │   │
                    │   │  /v1/scan/info  ─┐                              │   │
                    │   │  /v1/health     ─┤                              │   │
                    │   │  /openapi.json  ─┘                              │   │
                    │   │                                                   │   │
                    │   │  /mcp/          ─── api/mcp_server.py (FastMCP) │   │
                    │   │                                                   │   │
                    │   │             ▼ (all routes delegate)              │   │
                    │   │  api/services/scan.py    ── pure functions       │   │
                    │   │  api/services/x402_*.py  ── payment helpers      │   │
                    │   └──────────┬──────────────────────────────────────┘   │
                    │              │                                            │
                    │              ▼ subprocess                                 │
                    │   ┌─────────────────────────────────────────────────┐   │
                    │   │  node /opt/compuute-scan/compuute-scan.js       │   │
                    │   │  (vendored at v0.6.2, see Dockerfile build-arg) │   │
                    │   └──────────┬──────────────────────────────────────┘   │
                    │              │                                            │
                    │              ▼ git clone (--depth 1 --filter)             │
                    │   ┌─────────────────────────────────────────────────┐   │
                    │   │  tempfile.TemporaryDirectory()                  │   │
                    │   │  cleaned up after every scan                     │   │
                    │   └─────────────────────────────────────────────────┘   │
                    └──────────────────────────────────────────────────────────┘

                                          │  (verify, settle)
                                          ▼
                            ┌──────────────────────────────┐
                            │  Coinbase x402 Facilitator   │  (only for /v1/scan/pay)
                            │  https://x402.org/facilitator│
                            └──────────────────────────────┘
```

## Request flow — POST /v1/scan

```
client ─┬─▶ FastAPI ─▶ route (scan.py) ─▶ idempotency check (in-mem LRU)
        │                              │
        │                              ├─ HIT  ─▶ return cached + ETag/Cache-Control
        │                              │
        │                              └─ MISS ─▶ scan_repo(url)
        │                                          │
        │                                          ├─ validate_repo_url (regex)
        │                                          ├─ tempfile.TemporaryDirectory()
        │                                          ├─ git clone --depth 1 --filter
        │                                          ├─ node compuute-scan.js --json --output
        │                                          ├─ json.load(output_file)
        │                                          ├─ compute_score / top_findings
        │                                          └─ return structured dict
        │                              │
        │                              ├─ ETag = sha256(canonical JSON)
        │                              ├─ Cache-Control: public, max-age=1800
        │                              ├─ Idempotency-Key cache (24h)
        │                              └─ return 200
        ▼
   response
```

## Module responsibilities

| Module | Layer | Responsibility |
|--------|-------|----------------|
| `api/routes/scan.py` | HTTP | Idempotency-Key cache, ETag, Cache-Control, error mapping |
| `api/routes/scan_x402.py` | HTTP | 402 challenge, X-Payment header verify, settle |
| `api/mcp_server.py` | MCP | FastMCP wrapper exposing `scan_mcp_server` tool; same service-layer below |
| `api/services/scan.py` | Service | URL validation, clone, scanner subprocess, score, parse — **pure** |
| `api/services/x402_service.py` | Service | Build x402 requirements, verify+settle via facilitator |
| `api/serializers/scan_serializer.py` | Serialisation | Pydantic request + response models, OpenAPI schemas |
| `main.py` | Wiring | FastAPI app, lifespan, CORS, mount MCP, register routes |

Service-layer modules are pure Python with no FastAPI dependency. They can be reused as a library outside this HTTP service if needed.

## Data flow — no persistence

The service is **stateless** by design:

- No database.
- No user accounts (for `/v1/scan/pay`).
- Idempotency cache is in-process LRU (1000 entries) — survives only for the lifetime of the worker.
- Cloned repos live in `tempfile.TemporaryDirectory()` and are wiped after each scan.
- No telemetry sent anywhere except Railway's log collector.

This is intentional: matches compuute-scan's "no network, no state" design and keeps the threat surface small.

## Bundled vs runtime dependencies

| Dependency | Where | Why |
|------------|-------|-----|
| `compuute-scan` v0.6.2 | Vendored in Docker image at `/opt/compuute-scan` | Reproducible, no network at scan time |
| Node.js 20 | Apt-installed in Docker image | Runs the scanner |
| `git` | Apt-installed | Clones target repos |
| Python 3.12 + FastAPI + Pydantic + MCP SDK | pip in venv inside container | HTTP + MCP surface |

Compuute-scan version is pinned in the Dockerfile via a build-arg:

```Dockerfile
ARG COMPUUTE_SCAN_REF=v0.6.2
```

Bump via:

```bash
docker build --build-arg COMPUUTE_SCAN_REF=v0.6.3 -t compuute-scan-api .
railway up
```

## Deployment topology

- **Platform**: Railway (Hobby plan, single instance, single region).
- **Domain**: `scan.compuute.se` (Custom domain via Railway, DNS at one.com — CNAME → `p50wflxw.up.railway.app` + TXT `_railway-verify.scan` for ownership).
- **SSL**: Let's Encrypt, auto-provisioned by Railway.
- **Default port (Railway)**: 8080. Container `EXPOSE 8000` but listens on `$PORT` injected by Railway.
- **Build**: Dockerfile (single-stage, ~600 MB image).
- **CI**: pre-deploy `pytest tests/` runs locally; Railway rebuilds on `git push origin main`.

## Threat model

| Threat | Mitigation |
|--------|------------|
| User submits malicious repo URL | Strict regex (`github.com` HTTPS only), max 256 chars |
| Cloned repo executes code | We never execute — scanner reads files as text; no `npm install`, no `python setup.py`, no `make` |
| Repo too large fills disk | `git clone --filter=blob:limit=10m`, post-clone size cap (200 MB), wipe after scan |
| Clone or scan hang | `subprocess.run(timeout=60s clone / 120s scan)` — kills child if exceeded |
| Scanner JSON >64 KB truncates over pipe | `--output <file>` writes to disk; we `json.load(file)` |
| Privilege escalation in container | Run as non-root `scanner` user; no docker socket mount; no host volumes |
| DNS rebinding attack | FastMCP `transport_security.allowed_hosts` allowlist |
| Replay of x402 payment | Facilitator handles nonce + on-chain verification |
| Cache poisoning via Idempotency-Key | Cache key includes API-key-id-equivalent + URL + payload hash |

Future hardening (not in v0.2.x):

- Run the scanner inside a Docker-in-Docker sandbox with `--network none, --read-only, --cap-drop ALL` (already supported by upstream compuute-scan's `scan.sh`).
- Redis for distributed Idempotency-Key cache (today: per-worker in-mem).
- Per-IP rate limiting (today: relies on Railway-level abuse protection).
