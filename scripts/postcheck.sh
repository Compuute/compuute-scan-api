#!/bin/bash
# postcheck.sh — run at the END of every work session.
# Verifies clean state, appends a session entry to docs/PROGRESS.md.

set -u

cyan='\033[0;36m'; red='\033[0;31m'; green='\033[0;32m'; yellow='\033[1;33m'; reset='\033[0m'
ok()   { printf "${green}✓${reset}  %s\n" "$*"; }
fail() { printf "${red}✗${reset}  %s\n" "$*"; }
warn() { printf "${yellow}!${reset}  %s\n" "$*"; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p docs

echo ""
echo "─── compuute-scan-api postcheck ───"
echo ""

# 1. Clean git state required
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$DIRTY" != "0" ]; then
  fail "Working tree not clean ($DIRTY uncommitted files). Commit or stash before ending session."
  git status --short
  exit 1
fi
ok "Working tree clean"

# 2. Committer hygiene (CLAUDE.md global rule 4)
COMMITTERS=$(git log --since="24 hours ago" --format='%cn' | sort -u | tr '\n' ',' | sed 's/,$//')
if echo "$COMMITTERS" | grep -qi 'claude\|anthropic\|bot'; then
  fail "Committer hygiene violated. Recent committers: $COMMITTERS"
  fail "Per global CLAUDE.md rule 4, committer must be the human owner."
  exit 1
fi
ok "Committer hygiene OK ($COMMITTERS)"

# 3. Tests still pass
if [ -d venv ]; then
  source venv/bin/activate 2>/dev/null
  TEST_RESULT=$(python -m pytest tests/ -q 2>&1 | tail -1)
  if echo "$TEST_RESULT" | grep -q 'passed'; then
    ok "Tests: $TEST_RESULT"
  else
    fail "Tests: $TEST_RESULT — fix before ending session"
    exit 1
  fi
fi

# 4. Live state
LIVE_VER=$(curl -s --max-time 10 https://scan.compuute.se/v1/health 2>/dev/null | jq -r .version 2>/dev/null)
ok "Live: scan.compuute.se v$LIVE_VER"

# 5. Issue activity today
TODAY=$(date -u +%Y-%m-%d)
ISSUES_TOUCHED=$(gh issue list --state all --search "updated:>=$TODAY" --json number,title,state --limit 50 2>/dev/null | jq -r '.[] | "  - #\(.number) [\(.state)] \(.title)"')

# 6. Append to PROGRESS.md
PROGRESS_FILE="docs/PROGRESS.md"
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Progress log" > "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
  echo "Append-only daily summary. One section per work session." >> "$PROGRESS_FILE"
  echo "" >> "$PROGRESS_FILE"
fi

{
  echo ""
  echo "## $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo ""
  echo "**Live version:** v$LIVE_VER"
  echo ""
  echo "**Commits since yesterday:**"
  git log --since='24 hours ago' --format='- %h %s' 2>/dev/null | head -20
  echo ""
  if [ -n "$ISSUES_TOUCHED" ]; then
    echo "**Issues touched:**"
    echo "$ISSUES_TOUCHED"
    echo ""
  fi
  echo "**Tests:** $TEST_RESULT"
  echo ""
} >> "$PROGRESS_FILE"

ok "Appended session entry to $PROGRESS_FILE"

# 7. Remind to commit progress log
if [ -n "$(git status --porcelain docs/PROGRESS.md)" ]; then
  warn "docs/PROGRESS.md updated — commit it: git add docs/PROGRESS.md && git commit -m 'docs: progress log $TODAY'"
fi

echo ""
echo "─── End of session ───"
echo ""
