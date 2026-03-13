#!/usr/bin/env bash
# Phase 5 E2E Test Battery
# Usage: bash scripts/run_phase5_tests.sh [phase]
# Phases: A, B, C, D (default: A)
set -euo pipefail
cd "$(dirname "$0")/.."

PHASE="${1:-A}"
DATE="20260305"
RESULTS_FILE="data/phase5_test_results.json"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC} — Test $1: $2"; }
fail() { echo -e "${RED}FAIL${NC} — Test $1: $2"; }
skip() { echo -e "${YELLOW}SKIP${NC} — Test $1: $2"; }

# ============================================================
# PHASE A: Pure Python — No API, No Claude
# ============================================================
run_phase_a() {
  echo "=========================================="
  echo "Phase A: Pure Python Tests (no API, no Claude)"
  echo "=========================================="
  echo ""

  # --- Test 8: Scout --raw --compact file size ---
  echo "--- Test 8: Scout --raw --compact file size ---"
  python3 scripts/scout.py --dry-run --raw --compact
  COMPACT_FILE="data/scout/scout_compact_${DATE}.json"
  RAW_FILE="data/scout/scout_raw_${DATE}.json"

  if [ ! -f "$COMPACT_FILE" ]; then
    fail 8 "Compact file not created: $COMPACT_FILE"
  else
    COMPACT_SIZE=$(wc -c < "$COMPACT_FILE" | tr -d ' ')
    RAW_SIZE=$(wc -c < "$RAW_FILE" | tr -d ' ')
    echo "  Compact size: ${COMPACT_SIZE} bytes"
    echo "  Raw size: ${RAW_SIZE} bytes"

    # Verify valid JSON
    if python3 -c "import json; json.load(open('$COMPACT_FILE'))"; then
      echo "  Compact file: valid JSON"
    else
      fail 8 "Compact file is not valid JSON"
    fi
    if python3 -c "import json; json.load(open('$RAW_FILE'))"; then
      echo "  Raw file: valid JSON"
    else
      fail 8 "Raw file is not valid JSON"
    fi

    if [ "$COMPACT_SIZE" -lt 51200 ]; then
      pass 8 "Compact file ${COMPACT_SIZE} bytes < 50KB (raw was ${RAW_SIZE} bytes)"
    else
      fail 8 "Compact file ${COMPACT_SIZE} bytes >= 50KB"
    fi
  fi
  echo ""

  # --- Test 15: Rate limit enforcement ---
  echo "--- Test 15: Rate limit enforcement (smart-outbound dry-run) ---"
  echo "Pre-seeded rate limits: likes=28/30, replies=9/10, follows=4/5"
  echo ""

  python3 scripts/publisher.py --dry-run smart-outbound \
    --account EN \
    --plan data/misc/test_outbound_plan_rate_limit_EN.json 2>&1 | tee /tmp/test15_output.txt

  echo ""
  # Check that rate limits were respected
  FINAL_LIKES=$(python3 -c "
import json
d = json.load(open('data/pipeline/rate_limits_${DATE}.json'))
print(d['EN']['likes']['used'])
")
  FINAL_REPLIES=$(python3 -c "
import json
d = json.load(open('data/pipeline/rate_limits_${DATE}.json'))
print(d['EN']['replies']['used'])
")
  FINAL_FOLLOWS=$(python3 -c "
import json
d = json.load(open('data/pipeline/rate_limits_${DATE}.json'))
print(d['EN']['follows']['used'])
")

  echo "  Final counters: likes=${FINAL_LIKES}/30, replies=${FINAL_REPLIES}/10, follows=${FINAL_FOLLOWS}/5"

  T15_PASS=true
  if [ "$FINAL_LIKES" -gt 30 ]; then
    fail 15 "Likes exceeded limit: ${FINAL_LIKES}/30"
    T15_PASS=false
  fi
  if [ "$FINAL_REPLIES" -gt 10 ]; then
    fail 15 "Replies exceeded limit: ${FINAL_REPLIES}/10"
    T15_PASS=false
  fi
  if [ "$FINAL_FOLLOWS" -gt 5 ]; then
    fail 15 "Follows exceeded limit: ${FINAL_FOLLOWS}/5"
    T15_PASS=false
  fi

  # Also verify log shows rate limit warnings
  if grep -q "Rate limit\|limit reached" /tmp/test15_output.txt; then
    echo "  Rate limit warnings found in log output"
  else
    echo "  WARNING: No rate limit warnings in log — may not have hit limits"
  fi

  if [ "$T15_PASS" = true ]; then
    pass 15 "All counters within limits (likes=${FINAL_LIKES}, replies=${FINAL_REPLIES}, follows=${FINAL_FOLLOWS})"
  fi
  echo ""

  # Reset rate limits for Test 15 verification (don't contaminate other tests)
  # Restore original near-limit state
  cat > "data/pipeline/rate_limits_${DATE}.json" << 'RESET_EOF'
{
  "EN": {
    "likes": {"used": 28, "limit": 30},
    "replies": {"used": 9, "limit": 10},
    "follows": {"used": 4, "limit": 5}
  },
  "JP": {
    "likes": {"used": 0, "limit": 30},
    "replies": {"used": 0, "limit": 10},
    "follows": {"used": 0, "limit": 5}
  }
}
RESET_EOF

  # --- Test 16: Legacy outbound fallback ---
  echo "--- Test 16: Legacy outbound fallback ---"
  python3 scripts/publisher.py --dry-run outbound --account EN 2>&1 | tee /tmp/test16_output.txt
  T16_EXIT=$?

  if [ "$T16_EXIT" -eq 0 ]; then
    pass 16 "Legacy outbound completed with exit code 0"
  else
    fail 16 "Legacy outbound failed with exit code ${T16_EXIT}"
  fi
  echo ""

  echo "=========================================="
  echo "Phase A Complete"
  echo "=========================================="
}

# ============================================================
# PHASE B: API Only — No Claude
# ============================================================
run_phase_b() {
  echo "=========================================="
  echo "Phase B: API-Only Tests"
  echo "=========================================="
  echo ""

  # --- Test 12: Publisher outbound data helper ---
  echo "--- Test 12: Publisher outbound data — valid JSON output ---"
  python3 scripts/publisher_outbound_data.py --account EN --targets "@sessypuuh" 2>/dev/null | tee /tmp/test12_output.json

  if python3 -c "
import json, sys
d = json.load(open('/tmp/test12_output.json'))
targets = d.get('targets', [])
if not targets:
    print('FAIL: empty targets array')
    sys.exit(1)
t = targets[0]
required = ['handle', 'user_id', 'followers', 'recent_tweets']
missing = [f for f in required if f not in t]
if missing:
    print(f'FAIL: missing fields: {missing}')
    sys.exit(1)
tweets = t.get('recent_tweets', [])
if not tweets:
    print(f'FAIL: no recent_tweets')
    sys.exit(1)
print(f'OK: handle={t[\"handle\"]}, user_id={t[\"user_id\"]}, followers={t[\"followers\"]}, tweets={len(tweets)}')
"; then
    pass 12 "Valid JSON with target info and recent tweets"
  else
    fail 12 "Invalid output from publisher_outbound_data.py"
  fi
  echo ""

  echo "=========================================="
  echo "Phase B Complete"
  echo "=========================================="
}

# ============================================================
# Main
# ============================================================
case "$PHASE" in
  A|a) run_phase_a ;;
  B|b) run_phase_b ;;
  C|c)
    echo "Phase C requires Claude subagent invocations."
    echo "Run individual test commands from scripts/run_phase5_tests_c.sh"
    ;;
  D|d)
    echo "Phase D requires full pipeline run (live API + posting)."
    echo "See scripts/run_phase5_tests_d.sh for instructions."
    ;;
  *)
    echo "Usage: bash scripts/run_phase5_tests.sh [A|B|C|D]"
    exit 1
    ;;
esac
