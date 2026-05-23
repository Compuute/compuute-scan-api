#!/bin/bash
# precheck.sh — run at the START of every work session.
# Verifies live state and surfaces the next item from the backlog.
# Anti-hallucination guardrail: no claims about state without running this.

set -u

cyan='\033[0;36m'; red='\033[0;31m'; green='\033[0;32m'; yellow='\033[1;33m'; reset='\033[0m'
ok()   { printf "${green}✓${reset}  %s\n" "$*"; }
fail() { printf "${red}✗${reset}  %s\n" "$*"; }
warn() { printf "${yellow}!${reset}  %s\n" "$*"; }
info() { printf "${cyan}i${reset}  %s\n" "$*"; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "─── compuute-scan-api precheck ───"
echo ""

# 1. Git state
BRANCH=$(git branch --show-current)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
LAST_COMMIT=$(git log -1 --format='%h %s' 2>/dev/null)
ok "Branch: $BRANCH"
if [ "$DIRTY" != "0" ]; then
  warn "Uncommitted changes: $DIRTY file(s)"
else
  ok "Working tree clean"
fi
info "Last commit: $LAST_COMMIT"

# 2. Tests
if [ -d venv ]; then
  source venv/bin/activate 2>/dev/null
  TEST_RESULT=$(python -m pytest tests/ -q 2>&1 | tail -1)
  if echo "$TEST_RESULT" | grep -q 'passed'; then
    ok "Tests: $TEST_RESULT"
  else
    fail "Tests: $TEST_RESULT"
  fi
fi

# 3. Live endpoint
LIVE_VER=$(curl -s --max-time 10 https://scan.compuute.se/v1/health 2>/dev/null | jq -r .version 2>/dev/null)
if [ -n "$LIVE_VER" ] && [ "$LIVE_VER" != "null" ]; then
  ok "Live: scan.compuute.se v$LIVE_VER"
else
  fail "Live: not reachable"
fi

# 4. Open issues by milestone
echo ""
echo "─── Backlog status ───"
for MS in "P0 — credibility baseline" "P1 — track record" "P2 — adoption acceleration" "P3 — enterprise readiness"; do
  COUNT=$(gh issue list --milestone "$MS" --state open --limit 100 --json number 2>/dev/null | jq length)
  TOTAL=$(gh issue list --milestone "$MS" --state all --limit 100 --json number 2>/dev/null | jq length)
  printf "  ${cyan}%s${reset}  %s open of %s\n" "$(echo "$MS" | cut -d' ' -f1)" "$COUNT" "$TOTAL"
done

# 5. Next P0 issue (highest priority)
echo ""
NEXT=$(gh issue list --milestone "P0 — credibility baseline" --state open --limit 1 --json number,title 2>/dev/null | jq -r '.[0] | "#\(.number)  \(.title)"')
if [ -n "$NEXT" ] && [ "$NEXT" != "null  null" ]; then
  echo "─── Next up ───"
  echo "  $NEXT"
fi

# 6. CLAUDE.md verification rule reminder
echo ""
echo "─── Discipline reminder ───"
echo "  • Every claim about state must be backed by a command output."
echo "  • Branch per issue: git checkout -b fix/issue-N-short-name"
echo "  • Commit message must reference #N (pre-commit hook enforces)."
echo "  • Close issue with the 'Done when' command output in the closing comment."
echo ""
