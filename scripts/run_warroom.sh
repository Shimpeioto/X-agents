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

if [ "$SESSION" = "morning" ]; then
    env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_warroom.md for the full war room workflow — start with 'How Subagents Work', then 'Discussion Protocol', then 'Morning War Room'.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

This is a MULTI-AGENT DISCUSSION session. You MUST spawn Analyst and Strategist as SUBAGENTS using the Agent tool (subagent_type: general-purpose). Do NOT compose the briefing alone — the value comes from cross-examination between agents.

CRITICAL: Use the Agent tool directly (NOT Agent Teams). Each subagent call blocks and returns its result to you. For Round 1, spawn both in parallel with run_in_background: true. For Rounds 2-3, you can also run them in parallel.

Run the morning war room for ${DATE}.
Yesterday's date: ${YESTERDAY}
Active accounts: ${ACTIVE_ACCOUNTS}
Project directory: ${PROJECT_DIR}

Steps:
1. Gather data file paths (verify what exists)
2. Round 1: Spawn Analyst (model: sonnet) + Strategist (model: opus) as parallel subagents — both prepare independent briefings
3. Round 2: Spawn new subagents for cross-examination (send each agent's findings to the other)
4. Round 3: Spawn new subagents for recommendations (if needed — skip if consensus reached in Round 2)
5. Synthesize discussion into morning_briefing_${DATE_COMPACT}.json
6. Validate and send Telegram with discussion highlights" --dangerously-skip-permissions

elif [ "$SESSION" = "evening" ]; then
    env -u CLAUDECODE claude -p "You are Marc, the COO and Team Leader. Read agents/marc.md for your full instructions.
Read agents/marc_warroom.md for the full war room workflow — start with 'How Subagents Work', then 'Discussion Protocol', then 'Evening War Room'.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

This is a MULTI-AGENT DISCUSSION session. You MUST spawn Analyst and Strategist as SUBAGENTS using the Agent tool (subagent_type: general-purpose). Do NOT compose the briefing alone — the value comes from cross-examination between agents.

CRITICAL: Use the Agent tool directly (NOT Agent Teams). Each subagent call blocks and returns its result to you. For Round 1, spawn both in parallel with run_in_background: true. For Rounds 2-3, you can also run them in parallel.

Run the evening war room for ${DATE}.
Yesterday's date: ${YESTERDAY}
Active accounts: ${ACTIVE_ACCOUNTS}
Project directory: ${PROJECT_DIR}

Steps:
1. Collect metrics for active accounts (analyst.py collect + summary)
2. Round 1: Spawn Analyst (model: sonnet) + Strategist (model: opus) as parallel subagents — Analyst produces daily_report AND post-mortem data; Strategist grades own strategy
3. Validate daily report
4. Round 2: Spawn new subagents for cross-examination
5. Round 3: Spawn new subagents for recommendations for tomorrow
6. Synthesize discussion into strategy_feedback_${DATE_COMPACT}.json — the PDCA bridge
7. Send daily report + discussion highlights via Telegram" --dangerously-skip-permissions
fi
