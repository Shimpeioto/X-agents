#!/bin/bash
# scripts/cron_wrapper.sh — Wrapper for cron/launchd-triggered tasks
# Handles environment setup, logging, and error notification.
#
# v5 (Session 49) primary tasks:
#   ./scripts/cron_wrapper.sh create     # Daily Meruru content plan (06:00 JST)
#   ./scripts/cron_wrapper.sh balance    # Optional feed check
#
# Legacy v4 (kept temporarily for fallback):
#   ./scripts/cron_wrapper.sh pipeline
#
# Removed in v5:
#   morning_warroom, evening_warroom (war room flow removed — operator never reviewed outputs)
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
DATE_COMPACT=$(TZ=Asia/Tokyo date +%Y%m%d)
TASK="$1"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/cron_${TASK}_${DATE_COMPACT}.log"

mkdir -p "$LOG_DIR"

# --- Environment Setup ---
# Cron runs with minimal PATH. Source shell profile for claude CLI, python3, etc.
if [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc" 2>/dev/null || true
elif [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi

# Ensure claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [ERROR] claude CLI not found in PATH" >> "$LOG_FILE"
    cd "$PROJECT_DIR" && python3 scripts/telegram_send.py "⚠️ Cron ${TASK} failed: claude CLI not found in PATH" 2>/dev/null || true
    exit 1
fi

# --- NOTE on auth ---
# This script is invoked by macOS launchd (LaunchAgents), which runs in the
# user's login session with full Keychain access. No special auth setup needed.
# Do NOT use cron — cron cannot access macOS Keychain (different security session).

# --- Log Start ---
echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [INFO] Starting ${TASK} for ${DATE}" >> "$LOG_FILE"

# --- Execute Task ---
cd "$PROJECT_DIR"

run_task() {
    case "$TASK" in
        create)
            # v5 — Meruru creates 6 candidate posts for today (zero API)
            python3 scripts/orchestrator.py create --account EN >> "$LOG_FILE" 2>&1
            ;;
        balance)
            # v5 — Meruru reads feed and recommends what to post next (zero API)
            python3 scripts/orchestrator.py balance --account EN >> "$LOG_FILE" 2>&1
            ;;
        pipeline)
            # LEGACY v4 fallback — Strategist → Creator → Marc Review (zero API)
            echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [WARN] Running legacy v4 pipeline. v5 'create' is the primary command." >> "$LOG_FILE"
            python3 scripts/orchestrator.py pipeline >> "$LOG_FILE" 2>&1
            ;;
        morning_warroom|evening_warroom)
            # REMOVED in v5 — war room flow eliminated
            echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [ERROR] ${TASK} removed in v5 (Session 49). The war room flow was eliminated. Use './scripts/cron_wrapper.sh create' instead." >> "$LOG_FILE"
            exit 1
            ;;
        *)
            echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [ERROR] Unknown task: ${TASK}" >> "$LOG_FILE"
            exit 1
            ;;
    esac
}

if run_task; then
    echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [INFO] ${TASK} completed successfully" >> "$LOG_FILE"
else
    EXIT_CODE=$?
    echo "[$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S')] [CRON] [ERROR] ${TASK} failed with exit code ${EXIT_CODE}" >> "$LOG_FILE"
    # Notify operator of failure
    python3 scripts/telegram_send.py "⚠️ Cron ${TASK} failed (exit ${EXIT_CODE}). Check logs/cron_${TASK}_${DATE_COMPACT}.log" 2>/dev/null || true
    exit "$EXIT_CODE"
fi
