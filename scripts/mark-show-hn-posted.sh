#!/usr/bin/env bash
# Mark Show HN as posted — start of T₀ trigger window per
# docs/agent-economy-strategy.md §5.
#
# Run ONLY after you have actually posted on Hacker News. The script
# prompts for the real item URL, validates it, refuses known placeholders,
# verifies the URL responds with HTTP 200, then writes
# docs/launches/show-hn-2026-posted.txt and commits.
#
# Usage:
#   bash scripts/mark-show-hn-posted.sh
#
# Exit codes:
#   0 — marker written and committed
#   1 — bad / placeholder URL, or marker already exists
#   2 — git commit failed
set -uo pipefail

red='\033[0;31m'; green='\033[0;32m'; dim='\033[2m'; reset='\033[0m'
fail() { printf "${red}error:${reset} %s\n" "$*" >&2; exit 1; }

MARKER="docs/launches/show-hn-2026-posted.txt"

if [ -f "$MARKER" ]; then
  echo "Marker already exists: $MARKER"
  echo "Contents:"
  cat "$MARKER"
  echo
  echo "If this is wrong, delete it manually and re-run: git rm $MARKER && git commit -m 'revert marker'"
  exit 1
fi

# Known placeholder values from earlier accidents.
PLACEHOLDER_IDS="XXXXX 12345 41234567 99999999 00000000"

echo "Paste the FULL Hacker News URL of your Show HN post."
echo "Format: https://news.ycombinator.com/item?id=<ID>"
echo "Tip: open the post in a browser, copy the URL from the address bar."
echo
printf "URL: "
read -r URL

# Strip whitespace
URL="$(echo "$URL" | xargs)"

# Pattern check
if ! echo "$URL" | grep -qE '^https://news\.ycombinator\.com/item\?id=[0-9]+$'; then
  fail "URL does not match https://news.ycombinator.com/item?id=<digits>. Got: $URL"
fi

# Extract item id
ID="${URL##*=}"

# Placeholder check
for ph in $PLACEHOLDER_IDS; do
  if [ "$ID" = "$ph" ]; then
    fail "ID '$ID' looks like a placeholder. Use the REAL item-id from the URL bar of your live HN post."
  fi
done

# HN item IDs in 2026 are >40M. Reject anything smaller as suspicious.
if [ "$ID" -lt 40000000 ]; then
  fail "ID '$ID' is unrealistically small for a 2026 HN post. Double-check you copied the right URL."
fi

# Verify the URL actually resolves
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' "$URL")"
if [ "$HTTP_CODE" != "200" ]; then
  fail "HN URL did not return HTTP 200 (got $HTTP_CODE). Confirm the post is live."
fi

# Write marker
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "$MARKER")"
printf '%s  %s\n' "$URL" "$TS" > "$MARKER"

printf "${green}OK:${reset} marker written:\n"
cat "$MARKER"
echo

# Commit
git add "$MARKER" || fail "git add failed"
if ! git -c commit.gpgsign=false commit -m "post: Show HN live [#16]

URL: $URL
Posted (UTC): $TS

This commit starts the T₀ clock per docs/agent-economy-strategy.md §5,
provided at least one of {anthropics/skills#1346,
punkpeye/awesome-mcp-servers#8621} is also merged. Run
\`bash scripts/measure-tiers.sh\` to confirm T₀ status."; then
  fail "git commit failed (exit code $?)"
fi

printf "${green}Committed.${reset} Push with: git push origin main\n"
printf "${dim}Next: sit at HN for ~6h replying to comments per docs/launches/show-hn-2026.md.${reset}\n"
