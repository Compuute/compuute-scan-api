# Status page setup — `status.compuute.se`

15-minute setup, free tier. Linked from this repo's README and `compuute.se/security`.

## Recommended: BetterStack (formerly Better Uptime)

Free tier covers up to 10 monitors, 3-month incident history, public status page. Sufficient for current scope.

### Step-by-step (Daniel action)

1. **Sign up:** https://betterstack.com/better-uptime
2. **Create monitors** (one per critical endpoint):

| Monitor | URL | Method | Expected | Frequency |
|---------|-----|--------|----------|-----------|
| API liveness | `https://scan.compuute.se/v1/health` | GET | 200 + `scanner_available: true` (use response-body match) | 3 min |
| Scan endpoint | `https://scan.compuute.se/openapi.json` | GET | 200 + valid JSON | 5 min |
| MCP handshake | `https://scan.compuute.se/mcp/` | POST with body `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"betterstack","version":"0.0"}}}` | 200 + body contains `serverInfo` | 5 min |
| x402 endpoint | `https://scan.compuute.se/v1/scan/pay` | POST with body `{"repo_url":"https://github.com/Compuute/compuute-scan"}` | 402 (with x402v2 body) | 5 min |

3. **Configure incident reactions:**
   - Notification channel: email `daniel@compuute.se` + (optionally) Slack/Discord webhook
   - Alert delay: 1 min (don't alert on transient blips)
   - Auto-close after recovery

4. **Status page:**
   - Create public status page at BetterStack: `https://compuute.betteruptime.com` (default)
   - **Add custom domain** in BetterStack settings: `status.compuute.se`
   - BetterStack provides DNS instructions — typically CNAME to `statuspage.betteruptime.com`
   - Add the CNAME at one.com under `compuute.se` DNS records (Host: `status`, Value: `statuspage.betteruptime.com`)
   - Wait 5-15 min for DNS propagation + SSL provisioning

5. **Verify:** `curl -sf https://status.compuute.se && echo ok`

### Add to README

After setup, add this line to the README under "Documentation":

```markdown
| [status.compuute.se](https://status.compuute.se) | Live uptime + incident history |
```

### Acceptance criterion (for issue #8)

```bash
curl -sf https://status.compuute.se >/dev/null && echo ok
```

Output: `ok`.

## Alternative: UptimeRobot (lighter weight)

If you want something even lighter:

- https://uptimerobot.com (free tier: 50 monitors, 5-min intervals)
- Same setup, less polished status page
- No public status page on free tier — would need paid tier or a different public-page provider

BetterStack is preferred because the public page is the credibility artifact.

## Note on infrastructure scope

This status page does NOT replace internal monitoring. It's a **public credibility signal** for enterprise buyers who check `status.compuute.se` as part of their procurement checklist.

Internal monitoring (alerting Daniel during off-hours) is the same monitors but with the alert channel pointed at his phone/email; BetterStack handles both surfaces from one config.
