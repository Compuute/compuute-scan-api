# Analytics setup — usage and conversion-funnel tracking

15-minute setup, free tier. Privacy-preserving (GDPR-default).

## Recommended: Plausible Analytics

- EU-hosted (Frankfurt), cookieless, no PII collection.
- $9/month minimum after trial — there's no permanent free tier.

## Alternative: PostHog (event analytics)

- Self-hostable, EU cloud available, GDPR-compatible.
- Free tier: 1M events/month — generous for current traffic.
- Better for conversion-funnel tracking than Plausible (which is page-view focused).

**Recommendation:** PostHog for now. The free tier handles our volume + supports event tracking which Plausible doesn't (without paid add-on).

### Step-by-step (Daniel action)

1. **Sign up:** https://posthog.com → "EU Cloud" option
2. **Get project token** (looks like `phc_abc123...`)
3. **Set Railway env var:**
   ```bash
   railway variables --set POSTHOG_API_KEY=phc_xxxxxxxxxxxx \
                     --set POSTHOG_HOST=https://eu.i.posthog.com
   ```
4. **Add to `requirements.txt`:**
   ```
   posthog>=3,<4
   ```
5. **Add middleware** (planned file: `api/middleware/analytics.py`):

```python
"""PostHog event-tracking middleware.

Sends one event per /v1/scan call (free or paid), MCP initialize, and
healthcheck. No PII; only request shape + result fields.
"""
from __future__ import annotations
import os
import structlog

logger = structlog.get_logger()

_POSTHOG = None

def init_posthog():
    global _POSTHOG
    api_key = os.environ.get("POSTHOG_API_KEY")
    if not api_key:
        return None
    try:
        from posthog import Posthog
        _POSTHOG = Posthog(
            api_key,
            host=os.environ.get("POSTHOG_HOST", "https://eu.i.posthog.com"),
        )
        logger.info("posthog_initialized")
    except Exception as e:
        logger.warning("posthog_init_failed", error=str(e))
    return _POSTHOG

def track(event: str, properties: dict | None = None, distinct_id: str = "anonymous"):
    if _POSTHOG is None:
        return
    try:
        _POSTHOG.capture(distinct_id, event, properties or {})
    except Exception as e:
        logger.warning("posthog_capture_failed", event=event, error=str(e))
```

6. **Wire from routes** (planned additions to `api/routes/scan.py`):

```python
from api.middleware.analytics import track

# After scan_repo returns:
track("scan_completed", {
    "repo_host": "github",
    "score": result["score"],
    "files_scanned": result["summary"]["files_scanned"],
    "critical": result["summary"]["critical"],
    "high": result["summary"]["high"],
    "scan_seconds": result["performance"]["scan_seconds"],
    "tier": "free",  # or "x402" from scan_x402.py
})
```

Events to track (privacy-preserving — no repo names, no API keys):

| Event | Properties |
|-------|-----------|
| `scan_completed` | tier, score, severity counts, duration |
| `scan_failed` | code, http_status |
| `scan_x402_402_returned` | (signals agent discovery on Agentic.market) |
| `scan_x402_paid` | price_usd |
| `mcp_initialize` | client_name |
| `mcp_tool_called` | tool_name (`scan_mcp_server`) |
| `healthcheck` | (sampled — 1/100) |

7. **Configure conversion funnels in PostHog:**

   - **Funnel A — Free → Paid:** `scan_completed [tier=free]` → `scan_x402_402_returned` → `scan_x402_paid`
   - **Funnel B — MCP discovery:** `mcp_initialize` → `mcp_tool_called` → `scan_completed`
   - **Funnel C — Agentic.market path:** `scan_x402_402_returned` → `scan_x402_paid` (this confirms whether x402 actually converts)

8. **Set up weekly email digest** in PostHog → daniel@compuute.se on Mondays.

### Acceptance criterion (for issue #9)

```bash
curl -s https://scan.compuute.se | grep -qiE 'plausible|posthog' || echo "no analytics in HTML"
```

(Since we don't serve HTML, this acceptance criterion needs adjustment. Real check: after deploy with the middleware, hit `/v1/scan` and verify a PostHog event arrives in the dashboard within 30 seconds. Visible in PostHog's "Live events" view.)

### Privacy notes

PostHog defaults are GDPR-compatible when:

- EU Cloud region selected (no data leaves EU)
- IP anonymization on (default)
- No identified users (we use `distinct_id="anonymous"`)
- No reverse-PII reconstruction possible from our events

Add to `SECURITY.md` and `.well-known/agent.json` once live:

> *"This API uses PostHog (EU cloud, IP-anonymized) for usage analytics. No PII collected. See compuute.se/privacy."*

### Cost projection

PostHog free tier = 1M events/month. At 1 event per scan and expected ≤10K scans/month in first 6 months, we are 2 orders of magnitude under the limit. No cost expected until traffic 100x current baseline.
