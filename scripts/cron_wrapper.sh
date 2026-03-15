#!/bin/bash
# scripts/cron_wrapper.sh — Wrapper for cron-triggered tasks
# Handles environment setup, logging, and error notification.
#
# Usage:
#   ./scripts/cron_wrapper.sh pipeline
#   ./scripts/cron_wrapper.sh outbound
#   ./scripts/cron_wrapper.sh metrics
#   ./scripts/cron_wrapper.sh morning_warroom
#   ./scripts/cron_wrapper.sh evening_warroom
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
        pipeline)
            # Daily content pipeline: Scout → Strategist → Creator → Preview
            ./scripts/run_pipeline.sh >> "$LOG_FILE" 2>&1
            ;;
        outbound)
            # Daily outbound engagement for active accounts
            ./scripts/run_outbound.sh >> "$LOG_FILE" 2>&1
            ;;
        metrics)
            # Collect metrics for posted tweets (run 1h+ after publishing)
            # DEPRECATED: Use evening_warroom instead (metrics absorbed into evening war room)
            ./scripts/run_metrics.sh >> "$LOG_FILE" 2>&1
            ;;
        morning_warroom)
            # Morning briefing: review yesterday's results, send operator briefing
            ./scripts/run_warroom.sh morning >> "$LOG_FILE" 2>&1
            ;;
        evening_warroom)
            # Evening war room: collect metrics, daily report, strategy feedback
            ./scripts/run_warroom.sh evening >> "$LOG_FILE" 2>&1
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
