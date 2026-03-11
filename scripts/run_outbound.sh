#!/bin/bash
# scripts/run_outbound.sh — Invoke Marc to run daily outbound engagement
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

# Check account status — only run for active accounts
ACTIVE_ACCOUNTS=$(python3 -c "
import json
with open('config/account_status.json') as f:
    data = json.load(f)
active = [k for k, v in data['accounts'].items() if v.get('active')]
print(' '.join(active))
")

if [ -z "$ACTIVE_ACCOUNTS" ]; then
    echo "No active accounts. Skipping outbound."
    python3 scripts/telegram_send.py "Outbound skipped — no active accounts" 2>/dev/null || true
    exit 0
fi

# Check if strategy exists for today (or most recent)
STRATEGY_FILE="data/strategy_${DATE_COMPACT}.json"
if [ ! -f "$STRATEGY_FILE" ]; then
    # Fall back to most recent strategy
    STRATEGY_FILE=$(ls -t data/strategy_2026*.json 2>/dev/null | head -1)
    if [ -z "$STRATEGY_FILE" ]; then
        echo "ERROR: No strategy file found."
        exit 1
    fi
    echo "Using most recent strategy: $STRATEGY_FILE"
fi

# Prevent concurrent runs
LOCK_FILE="$PROJECT_DIR/.outbound.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Outbound already running (lock file exists: $LOCK_FILE)."
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

echo "Starting outbound for ${DATE}..."
echo "Active accounts: ${ACTIVE_ACCOUNTS}"
echo "Strategy: ${STRATEGY_FILE}"

export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_publishing.md, section '3. Outbound Engagement' for the outbound workflow.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

Run today's outbound engagement for active accounts: ${ACTIVE_ACCOUNTS}
Today's date: ${DATE}
Strategy: ${STRATEGY_FILE}
Project directory: ${PROJECT_DIR}

For each active account:
1. Spawn an Outbound teammate (model: sonnet) with the standard prompt from marc_publishing.md
2. After completion, check outbound log for failed_replies
3. If failed replies exist, send Telegram message with manual reply instructions
4. Send a brief outbound summary via Telegram when done" --dangerously-skip-permissions
