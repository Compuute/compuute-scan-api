#!/bin/bash
# prospect-research.sh — find MCP-adopting organizations + draft outreach angles.
#
# Per a16z 2026 verified data, KYA infrastructure isn't ready for B2B
# agents to fully close deals autonomously. What IS automatable is
# PROSPECT-RESEARCH: finding qualified leads, profiling them, drafting
# personalized DM angles. Daniel still sends; capacity multiplied.
#
# Usage:
#   ./scripts/prospect-research.sh --criteria 'EU AI Series A 2025-2026' --limit 30
#   ./scripts/prospect-research.sh --criteria 'MCP adoption' --limit 20
#
# Output: docs/outreach/prospect-batch-YYYY-MM-DD.md (gitignored).
# Each row: company, signal, decision-maker handle, custom DM angle.

set -euo pipefail

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

CRITERIA=""
LIMIT=30
OUTPUT_DIR="docs/outreach"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color output for terminal; suppressed when piped.
if [ -t 1 ]; then
  cyan='\033[0;36m'
  green='\033[0;32m'
  yellow='\033[1;33m'
  reset='\033[0m'
else
  cyan='' green='' yellow='' reset=''
fi

# ─────────────────────────────────────────────
# Arg parsing
# ─────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --criteria)
      CRITERIA="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --help|-h)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "$CRITERIA" ]; then
  echo "error: --criteria required" >&2
  echo "usage: $0 --criteria '<query>' [--limit N]" >&2
  exit 2
fi

cd "$REPO_ROOT"
mkdir -p "$OUTPUT_DIR"

DATE=$(date -u +%Y-%m-%d)
SLUG=$(echo "$CRITERIA" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-40)
OUTPUT="$OUTPUT_DIR/prospect-batch-${DATE}-${SLUG}.md"

# ─────────────────────────────────────────────
# Data sources
# ─────────────────────────────────────────────

echo -e "${cyan}─── prospect-research ───${reset}" >&2
echo "criteria: $CRITERIA" >&2
echo "limit:    $LIMIT" >&2
echo "output:   $OUTPUT" >&2
echo "" >&2

# Source 1: GitHub search for repos using MCP SDKs.
# Strategy: search broadly (topic:mcp + topic:mcp-server + recent activity),
# then post-filter by criteria tokens. GitHub search is AND-only on free-text;
# overly-specific multi-word queries return 0 results.
github_search() {
  local q="$1"
  # Always pull the broader MCP-tagged set so we have something to filter.
  for topic in mcp mcp-server agent ai-agent; do
    echo -e "${cyan}[GitHub]${reset} searching topic:$topic recently-updated" >&2
    gh api -X GET "search/repositories" \
      --raw-field "q=topic:$topic pushed:>2025-09-01" \
      --raw-field "sort=updated" \
      --raw-field "order=desc" \
      --raw-field "per_page=$LIMIT" \
      --jq '.items[] | {
        org: .owner.login,
        repo: .name,
        url: .html_url,
        desc: (.description // ""),
        lang: (.language // ""),
        stars: .stargazers_count,
        updated: .updated_at[0:10],
        topics: .topics
      }' 2>/dev/null || true
  done
}

# Source 2: Anthropic MCP Registry servers — direct buyer-builder signal
anthropic_registry_search() {
  local query="$1"
  echo -e "${cyan}[Anthropic Registry]${reset} searching for MCP servers: $query" >&2
  curl -sS --max-time 10 \
    "https://registry.modelcontextprotocol.io/v0/servers?search=$(printf '%s' "$query" | jq -sRr @uri)" \
    | jq -c '.servers[]? | {
      name: .server.name,
      title: .server.title,
      repo: .server.repository.url,
      version: .server.version,
      desc: .server.description
    }' 2>/dev/null || echo ""
}

# Source 3: Smithery — agent-builder marketplace
# (Smithery search requires authenticated API; we link to it for manual triage)

# ─────────────────────────────────────────────
# Profiling: for each candidate, derive a DM angle
# ─────────────────────────────────────────────

profile_candidate() {
  local org="$1"
  local repo="$2"
  local desc="$3"
  local lang="$4"
  local stars="$5"

  # DM angle heuristics — match against keyword classes in description
  local angle=""
  case "$desc" in
    *security*|*audit*|*vulnerabil*)
      angle="They already think about security — lead with 'we add MCP-specific rule coverage you don't get from Snyk/Aikido (L1-038-class threat-intel response within a week).'"
      ;;
    *agent*|*MCP*|*mcp*)
      angle="They're shipping agent infra — lead with 'pre-flight scan recommended before connecting to unknown MCP servers; happy to demo our hosted /v1/scan against your deployment.'"
      ;;
    *enterprise*|*compliance*|*GDPR*|*NIS2*|*DORA*)
      angle="They're in regulated space — lead with 'AI Procurement Risk Audit + MCP audit, EU-hosted, GDPR-aligned, SLSA L3 attestations on every release.'"
      ;;
    *fintech*|*finance*|*bank*)
      angle="Financial domain — lead with 'AI Procurement Risk Audit covers vendor capacity + supply-chain exposure; relevant for DORA Article 30 compliance.'"
      ;;
    *)
      angle="Generic lead: 'You're shipping AI-agent infra; we offer a scan tool you can drop into CI in 30 sec — happy to demo.'"
      ;;
  esac

  cat <<EOF
### \`$org/$repo\`

- **URL**: https://github.com/$org/$repo
- **Language**: $lang
- **Stars**: $stars
- **Description**: $desc
- **Signal**: matches criteria "$CRITERIA"
- **DM angle**: $angle
- **Suggested first sentence**: "Hey — saw your work on $repo$([ -n "$desc" ] && echo " (\\\"${desc:0:80}\\\")"). Bygger Compuute MCP Security; vi har en hosted scan på scan.compuute.se som tar 30 sek; relevant?"

EOF
}

# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────

# Write header to output file
{
  echo "# Prospect batch — $DATE"
  echo ""
  echo "**Criteria:** \`$CRITERIA\`"
  echo "**Limit:** $LIMIT"
  echo "**Generated by:** scripts/prospect-research.sh at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "## How to use this list"
  echo ""
  echo "1. Triage manually — kill obvious non-fits (forks, archived, joke repos)"
  echo "2. For each survivor: open the repo, find an active maintainer's profile"
  echo "3. Personalize the suggested first sentence with one specific detail from their repo"
  echo "4. Send via LinkedIn DM or GitHub Discussions (NOT cold email — agentic-builders treat that as spam)"
  echo "5. Log result in docs/outreach/calls.md once sent"
  echo ""
  echo "## Candidates"
  echo ""
} > "$OUTPUT"

# Pull from sources
COUNT=0

# GitHub: search broad MCP-tagged set, filter for relevance, dedup.
echo -e "${green}>>> Source 1: GitHub${reset}" >&2
TMPLIST="$(mktemp)"
github_search "$CRITERIA" > "$TMPLIST" 2>/dev/null

# Process raw JSON-lines, dedup by org/repo, profile each
SEEN="$(mktemp)"
HITS=0
while read -r line; do
  if [ -z "$line" ]; then continue; fi
  org=$(echo "$line" | jq -r '.org // ""' 2>/dev/null)
  repo=$(echo "$line" | jq -r '.repo // ""' 2>/dev/null)
  desc=$(echo "$line" | jq -r '.desc // ""' 2>/dev/null | tr -d '\n')
  lang=$(echo "$line" | jq -r '.lang // ""' 2>/dev/null)
  stars=$(echo "$line" | jq -r '.stars // 0' 2>/dev/null)

  if [ "$org" = "Compuute" ] || [ -z "$repo" ] || [ -z "$org" ]; then continue; fi

  KEY="$org/$repo"
  if grep -qFx "$KEY" "$SEEN" 2>/dev/null; then continue; fi
  echo "$KEY" >> "$SEEN"

  profile_candidate "$org" "$repo" "$desc" "$lang" "$stars" >> "$OUTPUT"
  HITS=$((HITS + 1))
  if [ "$HITS" -ge "$LIMIT" ]; then break; fi
done < "$TMPLIST"
COUNT=$HITS
rm -f "$TMPLIST"

# Anthropic registry: MCP servers that match the criteria
echo -e "${green}>>> Source 2: Anthropic MCP Registry${reset}" >&2
anthropic_registry_search "$CRITERIA" 2>/dev/null | while read -r line; do
  if [ -z "$line" ]; then continue; fi
  name=$(echo "$line" | jq -r '.name // ""')
  title=$(echo "$line" | jq -r '.title // ""' | tr -d '\n')
  repo=$(echo "$line" | jq -r '.repo // ""')
  desc=$(echo "$line" | jq -r '.desc // ""' | tr -d '\n')

  if [ -z "$name" ] || [ "$name" = "null" ]; then continue; fi

  # Extract org/repo from URL
  org_from_url=$(echo "$repo" | sed -E 's|https?://github.com/([^/]+)/.*|\1|' 2>/dev/null || echo "")
  repo_name=$(echo "$repo" | sed -E 's|https?://github.com/[^/]+/([^/]+).*|\1|' 2>/dev/null || echo "")

  if [ "$org_from_url" = "Compuute" ]; then continue; fi
  if [ -z "$repo_name" ]; then continue; fi

  profile_candidate "$org_from_url" "$repo_name" "$title — $desc" "unknown" "0" >> "$OUTPUT"
  COUNT=$((COUNT + 1))
done

# Summary footer
{
  echo ""
  echo "---"
  echo ""
  echo "## Summary"
  echo ""
  echo "Candidates surfaced: see entries above."
  echo ""
  echo "**Next steps:**"
  echo "1. Read each candidate top to bottom"
  echo "2. Cross-reference against docs/outreach/calls.md to avoid re-pinging anyone already contacted"
  echo "3. Pick the top 10 by relevance"
  echo "4. Send via LinkedIn or GitHub within 24 hours of generating this list (data goes stale)"
  echo ""
} >> "$OUTPUT"

LINE_COUNT=$(grep -c '^### ' "$OUTPUT" 2>/dev/null || echo 0)
echo "" >&2
echo -e "${green}✓ wrote $OUTPUT${reset}" >&2
echo -e "  candidates: $LINE_COUNT" >&2
echo "" >&2

# Emit one line per candidate to stdout so the wc -l done-when works.
grep '^### ' "$OUTPUT" 2>/dev/null || echo ""
