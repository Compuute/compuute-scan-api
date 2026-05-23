#!/bin/bash
# scripts/status.sh — 30-second project status check.
# Verifies live endpoint, scanner availability, MCP, OpenAPI, upstream drift.
# No deps beyond curl, jq, gh, git. Exits 0 if everything green.

set -u

URL="${SCAN_URL:-https://scan.compuute.se}"
RC=0

cyan='\033[0;36m'
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
reset='\033[0m'

ok()    { printf "${green}✓${reset}  %s\n" "$*"; }
fail()  { printf "${red}✗${reset}  %s\n" "$*"; RC=1; }
warn()  { printf "${yellow}!${reset}  %s\n" "$*"; }
info()  { printf "${cyan}i${reset}  %s\n" "$*"; }

echo ""
echo "─── compuute-scan-api status ───"
echo "Target: ${URL}"
echo ""

# 1. Health
HC=$(curl -sS -m 10 -o /tmp/_h.json -w "%{http_code}" "$URL/v1/health" 2>/dev/null || echo "000")
if [ "$HC" = "200" ]; then
  SCANNER_OK=$(jq -r '.scanner_available' /tmp/_h.json 2>/dev/null)
  if [ "$SCANNER_OK" = "true" ]; then
    ok "Health: 200, scanner_available"
  else
    fail "Health: 200 but scanner_available=$SCANNER_OK"
  fi
else
  fail "Health: HTTP $HC"
fi

# 2. OpenAPI
OAS=$(curl -sS -m 10 -o /tmp/_o.json -w "%{http_code}" "$URL/openapi.json" 2>/dev/null || echo "000")
if [ "$OAS" = "200" ] && jq -e '.paths' /tmp/_o.json >/dev/null 2>&1; then
  PATHS=$(jq -r '.paths | keys | length' /tmp/_o.json)
  ok "OpenAPI: $PATHS paths"
else
  fail "OpenAPI: HTTP $OAS or invalid JSON"
fi

# 3. MCP
MCP=$(curl -sS -m 10 -o /tmp/_m.txt -w "%{http_code}" -X POST "$URL/mcp/" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"status","version":"0.0"}}}' 2>/dev/null || echo "000")
if [ "$MCP" = "200" ] && grep -q "serverInfo" /tmp/_m.txt; then
  ok "MCP: initialize OK"
else
  fail "MCP: HTTP $MCP or bad payload"
fi

# 4. End-to-end scan (against compuute-scan itself — small repo, ~1s)
E2E=$(curl -sS -m 30 -o /tmp/_e.json -w "%{http_code}" -X POST "$URL/v1/scan" \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/Compuute/compuute-scan"}' 2>/dev/null || echo "000")
if [ "$E2E" = "200" ]; then
  VER=$(jq -r '.scanner.version' /tmp/_e.json)
  TIME=$(jq -r '.performance.scan_seconds + .performance.clone_seconds' /tmp/_e.json)
  ok "End-to-end scan: scanner v$VER, ${TIME}s total"
else
  fail "End-to-end scan: HTTP $E2E"
fi

# 5. Upstream version drift (if gh + git available)
if command -v gh >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
  if [ -f "$REPO_ROOT/Dockerfile" ]; then
    BUNDLED=$(grep -oE "COMPUUTE_SCAN_REF=v?[0-9.]+" "$REPO_ROOT/Dockerfile" | head -1 | cut -d= -f2)
    LATEST=$(gh release view --repo Compuute/compuute-scan --json tagName -q .tagName 2>/dev/null || echo "")
    if [ -n "$LATEST" ] && [ "$BUNDLED" != "$LATEST" ]; then
      warn "Upstream drift: bundled=$BUNDLED, latest=$LATEST. Bump COMPUUTE_SCAN_REF in Dockerfile."
    elif [ -n "$LATEST" ]; then
      ok "Upstream: bundled=$BUNDLED matches latest"
    else
      info "Could not fetch upstream release tag"
    fi
  fi
else
  info "gh not installed — skipping upstream drift check"
fi

echo ""
if [ $RC -eq 0 ]; then
  printf "${green}All checks passed.${reset}\n"
else
  printf "${red}One or more checks failed. See above.${reset}\n"
fi
exit $RC
