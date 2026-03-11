#!/bin/bash
# scripts/install_cron.sh — Install/update cron schedule for X-agents
#
# Usage:
#   ./scripts/install_cron.sh          # Install cron jobs
#   ./scripts/install_cron.sh --remove # Remove all X-agents cron jobs
#   ./scripts/install_cron.sh --show   # Show current schedule
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MARKER="# X-AGENTS-CRON"

show_schedule() {
    echo "=== Current X-agents cron schedule ==="
    crontab -l 2>/dev/null | grep "$MARKER" || echo "(no X-agents jobs found)"
    echo ""
    echo "=== Schedule explained ==="
    echo "Pipeline : 06:00 JST daily — Scout → Strategist → Creator → Preview"
    echo "Outbound : 14:00 JST daily — Likes, replies, follows for active accounts"
    echo "Metrics  : 22:00 JST daily — Collect post metrics, generate daily report"
}

remove_jobs() {
    echo "Removing X-agents cron jobs..."
    crontab -l 2>/dev/null | grep -v "$MARKER" | crontab - 2>/dev/null || true
    echo "Done. All X-agents cron jobs removed."
}

install_jobs() {
    # Remove existing X-agents jobs first
    EXISTING=$(crontab -l 2>/dev/null | grep -v "$MARKER" || true)

    # Schedule (all times in JST = UTC+9):
    #
    # Pipeline at 06:00 JST (21:00 UTC previous day)
    #   - Runs overnight content generation
    #   - Operator reviews content preview over morning coffee
    #
    # Outbound at 14:00 JST (05:00 UTC)
    #   - Midday engagement when targets are active
    #   - After operator has had time to approve content
    #
    # Metrics at 22:00 JST (13:00 UTC)
    #   - Evening collection, 8+ hours after typical posting
    #   - Daily report delivered before operator sleeps

    NEW_JOBS="
0 21 * * * ${PROJECT_DIR}/scripts/cron_wrapper.sh pipeline ${MARKER}
0 5 * * * ${PROJECT_DIR}/scripts/cron_wrapper.sh outbound ${MARKER}
0 13 * * * ${PROJECT_DIR}/scripts/cron_wrapper.sh metrics ${MARKER}
"

    echo "${EXISTING}${NEW_JOBS}" | crontab -

    echo "=== X-agents cron jobs installed ==="
    echo ""
    show_schedule
    echo ""
    echo "Logs: ${PROJECT_DIR}/logs/cron_*.log"
    echo "Remove: ./scripts/install_cron.sh --remove"
}

case "${1:-install}" in
    --show|-s)
        show_schedule
        ;;
    --remove|-r)
        remove_jobs
        ;;
    install|--install|-i)
        install_jobs
        ;;
    *)
        echo "Usage: $0 [--install|--remove|--show]"
        exit 1
        ;;
esac
