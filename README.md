# compuute-scan-api

**Scan-as-a-Service for MCP servers.** HTTP + MCP wrapper around [compuute-scan](https://github.com/Compuute/compuute-scan) — the MCP-specific static security scanner. Designed for agent-callable consumption.

POST a public GitHub repo URL → get a structured security report scored against 37 MCP-specific rules across 8 languages (TS/JS, Python, Go, Rust, C#, Java, Kotlin).

---

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/scan` | Scan a public GitHub MCP-server repo |
| GET | `/v1/scan/info` | Scanner version, limits, capabilities |
| GET | `/v1/health` | Liveness + scanner-binary check |
| GET | `/openapi.json` | OpenAPI v3 spec (for agent discovery) |
| /mcp/ | (planned) | MCP server with `scan_mcp_server` tool |

## Example

```bash
curl -X POST https://scan.compuute.se/v1/scan \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 00000000-0000-0000-0000-000000000001' \
  -d '{"repo_url": "https://github.com/modelcontextprotocol/servers"}'
```

Response (truncated):

```json
{
  "repo_url": "https://github.com/modelcontextprotocol/servers",
  "scanner": {"name": "compuute-scan", "version": "0.6.2", "layers_covered": ["L0", "L1"]},
  "summary": {"critical": 1, "high": 94, "medium": 22, "low": 0, "files_scanned": 77},
  "score": 0,
  "recommendation": "AVOID — 1 critical and 94 high finding(s)...",
  "top_findings": [...],
  "performance": {"clone_seconds": 1.2, "scan_seconds": 0.5, "repo_size_bytes": 41234},
  "_disclaimer": "PATTERN MATCH — compuute-scan is a static analyzer..."
}
```

## Agent-shaped API features

| Feature | How |
|---------|-----|
| Idempotent retries (24h cache) | `Idempotency-Key` header |
| HTTP cache | `ETag` + `Cache-Control: public, max-age=1800` |
| Conditional GET | `If-None-Match` → 304 Not Modified |
| Strict input validation | Pydantic `extra="forbid"`, GitHub-HTTPS-only |
| OpenAPI for discovery | `GET /openapi.json` with descriptions on every field |
| Honest framing | Every response carries `_disclaimer` — pattern match, not exploitability claim |

## Local development

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export COMPUUTE_SCAN_PATH=$HOME/compuute-scan/compuute-scan.js
uvicorn main:app --reload
```

## Tests

```bash
pytest tests/ -v
```

## Architecture

- `api/services/scan.py` — clone + sandbox + scan + parse. Pure functions.
- `api/serializers/scan_serializer.py` — Pydantic models, strict validation.
- `api/routes/scan.py` — HTTP layer: idempotency, cache, ETag.
- `main.py` — FastAPI wiring.

Bundled compuute-scan version is configured via `COMPUUTE_SCAN_PATH` env var.

## Productisation roadmap

| Tier | Audience | Price |
|------|----------|-------|
| Free | Indie devs, agent builders | 3 scans/day |
| Pro | Teams shipping MCP to production | TBD |
| Audit | Manual L2-L4 audit by Compuute AB | $5K-30K — see [compuute.se/audit](https://compuute.se/audit) |

## License

MIT (matches compuute-scan).

## Author

Compuute AB — daniel@compuute.se
