#!/usr/bin/env bash
# Measure T0/T1/T2 distribution tiers per docs/agent-economy-strategy.md §5
# (revised 2026-06-24, condition-based pivot trigger anchored on T0/T1/T2 tiers).
#
# Tier model:
#   T0 — Reach        : do agents find us?
#   T1 — Engagement   : do they actually call /v1/scan with real repos?
#   T2 — Conversion   : do they pay or book?
#
# Snapshot is printed to stdout. Suitable for cron + redirect to a logfile,
# or for ad-hoc inspection before committing changes that affect distribution.
#
# Exit codes:
#   0 — snapshot printed
#   1 — required tool missing (railway / curl / python3 / gh)
set -uo pipefail

for tool in curl python3 gh; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "error: $tool not in PATH" >&2
    exit 1
  fi
done

WALLET="0xBc13c6642e1b7c62D3DB8aD47FBA2908680CAb67"
USDC_BASE="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_RPC="https://mainnet.base.org"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
dim()  { printf "\033[2m%s\033[0m\n" "$*"; }

bold "compuute-scan-api — distribution tier snapshot"
date -u "+UTC %Y-%m-%dT%H:%M:%SZ"
echo

# ---------- T0 — Reach ----------
bold "T0 — Reach"

# T0.a — Anthropic Skill PR + awesome-list PR status
SKILL_PR_STATE="$(gh pr view 1346 --repo anthropics/skills --json state -q .state 2>/dev/null || echo UNKNOWN)"
PUNKPEYE_PR_STATE="$(gh pr view 8621 --repo punkpeye/awesome-mcp-servers --json state -q .state 2>/dev/null || echo UNKNOWN)"
echo "  anthropics/skills#1346       : $SKILL_PR_STATE"
echo "  punkpeye/awesome-mcp-servers#8621 : $PUNKPEYE_PR_STATE"

# T0.b — discovery endpoints alive
for path in /llms.txt /.well-known/agent.json /.well-known/x402.json /.well-known/ai-plugin.json; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "https://scan.compuute.se$path")"
  printf "  %-40s : HTTP %s\n" "$path" "$code"
done

# T0.c — unique non-Compuute IPs hitting discovery+scan paths over last available logs
#   Heuristic: railway logs only retains recent window; this is point-in-time.
#   100.64.0.0/10 is Railway internal probe range — filter it.
if command -v railway >/dev/null 2>&1; then
  UNIQUE_IPS="$(railway logs --deployment 2>/dev/null \
    | grep -oE '([0-9]+\.){3}[0-9]+' \
    | grep -v -E '^100\.64\.' \
    | grep -v -E '^127\.' \
    | sort -u | wc -l | xargs)"
  echo "  unique non-Compuute IPs in recent log window: $UNIQUE_IPS"
  dim "    (point-in-time from railway logs --deployment; not 7-day window)"
else
  dim "  railway CLI not available — skip unique-IP estimate"
fi
echo

# ---------- T1 — Engagement ----------
bold "T1 — Engagement"

# T1.a — GitHub stars (non-Compuute owners)
for repo in Compuute/compuute-scan Compuute/compuute-scan-api; do
  STARS="$(gh api "repos/$repo" --jq .stargazers_count 2>/dev/null || echo '?')"
  printf "  %-35s stars: %s\n" "$repo" "$STARS"
done

# T1.b — POST /v1/scan calls in recent log window (excluding internal probes)
if command -v railway >/dev/null 2>&1; then
  SCAN_CALLS="$(railway logs --deployment 2>/dev/null \
    | grep -c 'POST /v1/scan HTTP' || echo 0)"
  echo "  POST /v1/scan in recent log window: $SCAN_CALLS"
  dim "    (point-in-time; not 7-day window)"
fi
echo

# ---------- T2 — Conversion ----------
bold "T2 — Conversion"

# T2.a — wallet balance + nonce (have we received ANY USDC?)
NONCE_HEX="$(curl -s -X POST "$BASE_RPC" -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionCount\",\"params\":[\"$WALLET\",\"latest\"],\"id\":1}" \
  | python3 -c "import json,sys;print(json.load(sys.stdin).get('result','0x0'))" 2>/dev/null)"
USDC_HEX="$(curl -s -X POST "$BASE_RPC" -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_call\",\"params\":[{\"to\":\"$USDC_BASE\",\"data\":\"0x70a08231000000000000000000000000${WALLET:2}\"},\"latest\"],\"id\":1}" \
  | python3 -c "import json,sys;print(json.load(sys.stdin).get('result','0x0'))" 2>/dev/null)"

NONCE="$(python3 -c "print(int('$NONCE_HEX', 16))" 2>/dev/null || echo '?')"
USDC="$(python3 -c "print(int('$USDC_HEX', 16) / 1_000_000)" 2>/dev/null || echo '?')"
echo "  Base wallet nonce (outgoing tx count) : $NONCE"
echo "  Base wallet USDC balance               : $USDC USDC"

# T2.b — POST /v1/scan/pay attempts
if command -v railway >/dev/null 2>&1; then
  PAY_CALLS="$(railway logs --deployment 2>/dev/null \
    | grep -c 'POST /v1/scan/pay HTTP' || echo 0)"
  echo "  POST /v1/scan/pay in recent log window: $PAY_CALLS"
fi
echo

# ---------- T₀ status ----------
bold "T0 trigger status"
if [ "$SKILL_PR_STATE" = "MERGED" ] || [ "$PUNKPEYE_PR_STATE" = "MERGED" ]; then
  PR_READY="yes (one or more PR merged)"
else
  PR_READY="no (no PR merged yet)"
fi

if [ -f "docs/launches/show-hn-2026-posted.txt" ]; then
  HN_READY="yes (per docs/launches/show-hn-2026-posted.txt)"
else
  HN_READY="no (touch docs/launches/show-hn-2026-posted.txt with the HN URL after posting to record T0 start)"
fi

echo "  Show HN posted     : $HN_READY"
echo "  First PR merged    : $PR_READY"
if [ "$PR_READY" = "yes (one or more PR merged)" ] && [ "${HN_READY:0:3}" = "yes" ]; then
  bold "  → T0 reached. Start 60-day evaluation window."
else
  dim "  → T0 not yet reached. Pivot clock has not started per agent-economy-strategy.md §5."
fi
