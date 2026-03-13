#!/usr/bin/env bash
# Phase 5 — Phase D: Full E2E Tests (live API + posting)
# CAUTION: Tests 19 posts real tweets!
#
# Usage:
#   bash scripts/run_phase5_tests_d.sh [test]
#   test: 18 | 19 | 20
set -euo pipefail
cd "$(dirname "$0")/.."

TEST="${1:-help}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC} — Test $1: $2"; }
fail() { echo -e "${RED}FAIL${NC} — Test $1: $2"; }

# ============================================================
# Test 18: Full pipeline with Scout Intelligence
# ============================================================
run_test_18() {
  echo "=========================================="
  echo "Test 18: Full Pipeline with Scout Intelligence"
  echo "=========================================="
  echo ""
  echo "This runs the full daily pipeline (Scout → Strategist → Creator)."
  echo "Scout will use Intelligence Mode (Claude subagent + --raw --compact)."
  echo ""
  echo "Command:"
  echo "  bash scripts/run_pipeline.sh"
  echo ""
  echo "After pipeline completes, verify:"
  echo "  bash scripts/run_phase5_tests_d.sh verify_18"
}

verify_test_18() {
  # Find today's date files
  TODAY=$(date +%Y%m%d)
  SCOUT="data/scout/scout_report_${TODAY}.json"

  echo "Checking pipeline output for date: ${TODAY}"

  if [ ! -f "$SCOUT" ]; then
    fail 18 "Scout report not found: $SCOUT"
    return
  fi

  # Check scout report has analysis section
  echo ""
  echo "Test 18a: Scout report has analysis section"
  if python3 scripts/validate.py scout_analysis "$SCOUT" 2>/dev/null; then
    pass 18 "Scout report has valid analysis section"
  else
    echo -e "${YELLOW}WARN${NC} — Scout may have fallen back to legacy mode (no analysis)"
    python3 scripts/validate.py scout "$SCOUT" && echo "  Legacy scout validation: PASS"
  fi

  # Check Strategist produced valid strategy
  STRATEGY="data/strategy/strategy_${TODAY}.json"
  echo ""
  echo "Test 18b: Strategist produced valid strategy"
  if [ -f "$STRATEGY" ]; then
    if python3 scripts/validate.py strategist "$STRATEGY"; then
      pass 18 "Strategist output valid"
    else
      fail 18 "Strategist validation failed"
    fi
  else
    fail 18 "Strategy file not found: $STRATEGY"
  fi
}

# ============================================================
# Test 19: Full publishing with Smart Outbound + Analyst Intelligence
# ============================================================
run_test_19() {
  echo "=========================================="
  echo "Test 19: Full Publishing with Intelligence"
  echo "=========================================="
  echo ""
  echo "WARNING: This test posts REAL tweets!"
  echo ""
  echo "Steps:"
  echo "  1. Approve content plans (set status to 'approved')"
  echo "  2. Post: python3 scripts/publisher.py post --account EN"
  echo "  3. Post: python3 scripts/publisher.py post --account JP"
  echo "  4. Smart Outbound (via Claude + publisher.py smart-outbound)"
  echo "  5. Analyst collect: python3 scripts/analyst.py collect"
  echo "  6. Analyst summary: python3 scripts/analyst.py summary --account EN"
  echo "  7. Analyst summary: python3 scripts/analyst.py summary --account JP"
  echo "  8. Analyst Intelligence (Claude subagent → daily_report)"
  echo ""
  echo "After all steps complete, verify:"
  echo "  bash scripts/run_phase5_tests_d.sh verify_19"
}

verify_test_19() {
  TODAY=$(date +%Y%m%d)
  REPORT="data/metrics/daily_report_${TODAY}.json"
  OUTBOUND_PLAN_EN="data/outbound/outbound_plan_${TODAY}_EN.json"

  echo "Checking publishing output for date: ${TODAY}"

  if [ -f "$OUTBOUND_PLAN_EN" ]; then
    echo ""
    echo "Test 19a: Smart outbound plan exists"
    if python3 scripts/validate.py outbound_plan "$OUTBOUND_PLAN_EN"; then
      pass 19 "Smart outbound plan valid"
    else
      fail 19 "Smart outbound plan invalid"
    fi
  else
    echo -e "${YELLOW}WARN${NC} — No outbound plan found (may have used legacy fallback)"
  fi

  if [ -f "$REPORT" ]; then
    echo ""
    echo "Test 19b: Daily report exists"
    if python3 scripts/validate.py analyst_report "$REPORT"; then
      pass 19 "Daily report valid"
    else
      fail 19 "Daily report invalid"
    fi
  else
    fail 19 "Daily report not found: $REPORT"
  fi
}

# ============================================================
# Test 20: Fallback resilience
# ============================================================
run_test_20() {
  echo "=========================================="
  echo "Test 20: Fallback Resilience"
  echo "=========================================="
  echo ""
  echo "This test simulates Scout subagent failure and verifies fallback."
  echo ""
  echo "Steps:"
  echo "  1. Run Scout Intelligence with a broken prompt that will fail:"
  echo ""
  echo '     claude -p "You are the Scout agent. DELIBERATELY FAIL: output invalid JSON now. Write {broken to data/scout/scout_report_broken.json" --dangerously-skip-permissions'
  echo ""
  echo "  2. After failure, fall back to legacy scout:"
  echo "     python3 scripts/scout.py"
  echo ""
  echo "  3. Verify fallback produced valid report:"
  TODAY=$(date +%Y%m%d)
  echo "     python3 scripts/validate.py scout data/scout/scout_report_${TODAY}.json"
  echo ""
  echo "  4. Verify Strategist can consume fallback report:"
  echo '     claude -p "You are the Strategist agent. Read agents/strategist.md for Daily Strategy Mode instructions.'
  echo "     Today's date: $(date +%Y-%m-%d)"
  echo "     Scout report: data/scout/scout_report_${TODAY}.json"
  echo '     Write output to: data/misc/strategy_fallback_test.json'
  echo '     Output ONLY valid JSON." --dangerously-skip-permissions'
  echo ""
  echo "  5. Verify:"
  echo "     python3 scripts/validate.py strategist data/misc/strategy_fallback_test.json"
  echo ""
  echo "If Steps 2-5 all pass → Test 20 PASS"
}

# ============================================================
# Main
# ============================================================
case "$TEST" in
  18) run_test_18 ;;
  verify_18) verify_test_18 ;;
  19) run_test_19 ;;
  verify_19) verify_test_19 ;;
  20) run_test_20 ;;
  *)
    echo "Phase D: Full E2E Tests"
    echo ""
    echo "Usage: bash scripts/run_phase5_tests_d.sh [18|verify_18|19|verify_19|20]"
    echo ""
    echo "  18        — Instructions for full pipeline test"
    echo "  verify_18 — Verify pipeline output"
    echo "  19        — Instructions for full publishing test (POSTS REAL TWEETS)"
    echo "  verify_19 — Verify publishing output"
    echo "  20        — Instructions for fallback resilience test"
    ;;
esac
