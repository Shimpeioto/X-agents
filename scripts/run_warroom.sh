#!/bin/bash
# scripts/run_warroom.sh — Invoke Marc for morning or evening war room
#
# Usage:
#   ./scripts/run_warroom.sh morning   # Morning briefing (05:30 JST)
#   ./scripts/run_warroom.sh evening   # Evening metrics + feedback (22:00 JST)
#
set -euo pipefail

DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
DATE_COMPACT=$(TZ=Asia/Tokyo date +%Y%m%d)
YESTERDAY=$(TZ=Asia/Tokyo date -v-1d +%Y-%m-%d 2>/dev/null || TZ=Asia/Tokyo date -d "yesterday" +%Y-%m-%d)
YESTERDAY_COMPACT=$(TZ=Asia/Tokyo date -v-1d +%Y%m%d 2>/dev/null || TZ=Asia/Tokyo date -d "yesterday" +%Y%m%d)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION="${1:-}"

cd "$PROJECT_DIR"

if [ -z "$SESSION" ]; then
    echo "Usage: $0 {morning|evening}"
    exit 1
fi

if [ "$SESSION" != "morning" ] && [ "$SESSION" != "evening" ]; then
    echo "ERROR: Unknown session '${SESSION}'. Use 'morning' or 'evening'."
    exit 1
fi

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
    echo "No active accounts. Skipping war room."
    exit 0
fi

# Prevent concurrent runs
LOCK_FILE="$PROJECT_DIR/.warroom_${SESSION}.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: War room (${SESSION}) already running (lock file exists: $LOCK_FILE)."
    echo "If the previous run crashed, remove the lock file manually:"
    echo "  rm $LOCK_FILE"
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

echo "Starting ${SESSION} war room for ${DATE}..."
echo "Active accounts: ${ACTIVE_ACCOUNTS}"

export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

if [ "$SESSION" = "morning" ]; then
    env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_warroom.md, section 'Morning War Room' for the morning briefing workflow.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

Run the morning war room for ${DATE}.
Yesterday's date: ${YESTERDAY}
Active accounts: ${ACTIVE_ACCOUNTS}
Project directory: ${PROJECT_DIR}

Review yesterday's results and send the operator a morning briefing via Telegram." --dangerously-skip-permissions

elif [ "$SESSION" = "evening" ]; then
    env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_warroom.md, section 'Evening War Room' for the evening workflow.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

Run the evening war room for ${DATE}.
Yesterday's date: ${YESTERDAY}
Active accounts: ${ACTIVE_ACCOUNTS}
Project directory: ${PROJECT_DIR}

Steps:
1. Collect metrics for active accounts
2. Generate metric summaries
3. Spawn Analyst teammate (model: sonnet) for daily report
4. Generate strategy feedback (data/strategy_feedback_${DATE_COMPACT}.json) — the PDCA bridge
5. Send daily report + alerts via Telegram
6. Generate and send HTML reports via Telegram" --dangerously-skip-permissions
fi
