#!/bin/bash
# scripts/run_pipeline.sh — Invoke Marc to run today's pipeline
set -euo pipefail

DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

# Check claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' CLI not found in PATH. Install Claude Code first."
    exit 1
fi

# Prevent concurrent pipeline runs
LOCK_FILE="$PROJECT_DIR/.pipeline.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Pipeline already running (lock file exists: $LOCK_FILE)."
    echo "If the previous run crashed, remove the lock file manually:"
    echo "  rm $LOCK_FILE"
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

echo "Starting pipeline for ${DATE}..."
echo "Project: ${PROJECT_DIR}"

env -u CLAUDECODE claude -p "You are Marc, the COO agent. Read agents/marc.md for your full instructions.

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output.

Run today's pipeline for ${DATE}.
Project directory: ${PROJECT_DIR}" --dangerously-skip-permissions
