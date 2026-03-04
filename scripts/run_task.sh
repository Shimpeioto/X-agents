#!/bin/bash
# scripts/run_task.sh — Invoke Marc to execute an operator task
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: ./scripts/run_task.sh <task_id>"
    echo "Example: ./scripts/run_task.sh 20260304_001"
    exit 2
fi

TASK_ID="$1"
DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_FILE="$PROJECT_DIR/data/tasks/task_${TASK_ID}.json"

cd "$PROJECT_DIR"

# Check claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' CLI not found in PATH. Install Claude Code first."
    exit 1
fi

# Check task file exists
if [ ! -f "$TASK_FILE" ]; then
    echo "ERROR: Task file not found: $TASK_FILE"
    exit 1
fi

# Prevent concurrent runs of the same task
LOCK_FILE="$PROJECT_DIR/.task_${TASK_ID}.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Task already running (lock file exists: $LOCK_FILE)."
    echo "If the previous run crashed, remove the lock file manually:"
    echo "  rm $LOCK_FILE"
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

echo "Starting task ${TASK_ID}..."
echo "Project: ${PROJECT_DIR}"
echo "Task file: ${TASK_FILE}"

env -u CLAUDECODE claude -p "You are Marc, the COO agent. Read agents/marc.md for your full instructions.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

You have received a task from the operator.
Task file: data/tasks/task_${TASK_ID}.json
Today's date: ${DATE}
Project directory: ${PROJECT_DIR}

Read the task file, plan your approach using the Task Handling protocol from your skill file, and execute. Deliver results via Telegram when done." --dangerously-skip-permissions
