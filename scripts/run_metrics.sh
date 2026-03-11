#!/bin/bash
# scripts/run_metrics.sh — Collect metrics for posted tweets and generate daily report
#
# DEPRECATED: Metrics collection and daily reporting are now handled by the evening war room.
# Use: ./scripts/run_warroom.sh evening
# This script is kept for manual re-runs only.
#
set -euo pipefail

DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
DATE_COMPACT=$(TZ=Asia/Tokyo date +%Y%m%d)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

# Check claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' CLI not found in PATH. Install Claude Code first."
    exit 1
fi

# Check account status
ACTIVE_ACCOUNTS=$(python3 -c "
import json
with open('config/account_status.json') as f:
    data = json.load(f)
active = [k for k, v in data['accounts'].items() if v.get('active')]
print(' '.join(active))
")

if [ -z "$ACTIVE_ACCOUNTS" ]; then
    echo "No active accounts. Skipping metrics."
    exit 0
fi

# Prevent concurrent runs
LOCK_FILE="$PROJECT_DIR/.metrics.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Metrics already running (lock file exists: $LOCK_FILE)."
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

echo "Starting metrics collection for ${DATE}..."
echo "Active accounts: ${ACTIVE_ACCOUNTS}"

export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_publishing.md, sections 5-8 for the metrics and daily report workflow.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

Collect metrics and generate the daily report for active accounts: ${ACTIVE_ACCOUNTS}
Today's date: ${DATE}
Project directory: ${PROJECT_DIR}

Steps:
1. For each active account: python3 scripts/analyst.py collect --account {account}
2. For each active account: python3 scripts/analyst.py summary --account {account}
3. Validate metrics output
4. Spawn an Analyst teammate (model: sonnet) for the daily report (Intelligence Mode)
5. Validate daily report
6. Send daily report + alerts via Telegram
7. Generate and send HTML report via Telegram" --dangerously-skip-permissions
