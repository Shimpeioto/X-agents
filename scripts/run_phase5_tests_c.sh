#!/usr/bin/env bash
# Phase 5 — Phase C: Claude Subagent Tests
# Run each test group separately, verify output between groups.
#
# Usage:
#   bash scripts/run_phase5_tests_c.sh [test_group]
#   test_group: analyst | scout | scout_compat | outbound | all
set -euo pipefail
cd "$(dirname "$0")/.."

GROUP="${1:-all}"
DATE="20260304"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}PASS${NC} — Test $1: $2"; }
fail() { echo -e "${RED}FAIL${NC} — Test $1: $2"; }

# ============================================================
# Tests 1-5: Analyst Intelligence
# ============================================================
run_analyst() {
  echo "=========================================="
  echo "Tests 1-5: Analyst Intelligence"
  echo "=========================================="
  echo ""
  echo "Running Claude subagent for Analyst Intelligence Mode..."
  echo "Command:"
  echo ""
  cat << 'PROMPT_EOF'
claude -p "You are the Analyst agent. Read agents/analyst.md, section 'Intelligence Mode' for your instructions.

Today's date: 2026-03-04
Raw metrics: data/metrics_20260304_EN.json, data/metrics_20260304_JP.json
Strategy: data/strategy_20260304.json
Pipeline state: data/pipeline_state_20260304.json
Outbound log: data/outbound_log_20260304.json
Content plans: data/content_plan_20260304_EN.json, data/content_plan_20260304_JP.json
Yesterday's report: does not exist (first run — skip trend comparison)

IMPORTANT NOTES:
- EN account: followers=6, followers_change=-1. That is a 16.7% drop (abs(-1)/6 = 0.167 > 0.10). This MUST trigger anomaly=true.
- EN ab_test: variant A has 3 posts (EN_20260304_01,02,03), variant B has 1 post (EN_20260304_04). Both under 3 per variant → verdict must be 'insufficient_data'.
- JP ab_test: variant A has 2 posts, variant B has 2 posts. Both under 3 → verdict must be 'insufficient_data'.
- The outbound_log shows dry-run actions only for EN (no JP outbound).

Analyze all data, detect anomalies, evaluate A/B tests, and produce the daily report.
Write output to: data/daily_report_20260304.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
PROMPT_EOF

  echo ""
  echo "After running the command above, run verification:"
  echo "  bash scripts/run_phase5_tests_c.sh verify_analyst"
}

verify_analyst() {
  echo "--- Verifying Analyst Intelligence output ---"
  REPORT="data/daily_report_${DATE}.json"

  if [ ! -f "$REPORT" ]; then
    fail 1 "File not found: $REPORT"
    return
  fi

  # Test 1: Valid JSON + validate.py
  echo ""
  echo "Test 1: validate.py analyst_report"
  if python3 scripts/validate.py analyst_report "$REPORT"; then
    pass 1 "Analyst report valid JSON, all required fields present"
  else
    fail 1 "validate.py analyst_report failed"
  fi

  # Test 2: Anomaly detection
  echo ""
  echo "Test 2: Anomaly detection catches follower drop"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
en = d['accounts']['EN']
if en.get('anomaly') is True:
    detail = en.get('anomaly_detail', '')
    print(f'  EN anomaly=true, detail: {detail}')
    # Check that detail mentions the percentage
    if '14' in detail or '16' in detail or '17' in detail or '%' in detail:
        print('  Detail mentions percentage — PASS')
    else:
        print('  WARNING: Detail does not mention percentage')
    sys.exit(0)
else:
    print(f'  EN anomaly={en.get(\"anomaly\")} — expected true')
    sys.exit(1)
"
  if [ $? -eq 0 ]; then pass 2 "EN anomaly detected"; else fail 2 "EN anomaly not detected"; fi

  # Also check JP is NOT anomaly (followers=140, change=0)
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
jp = d['accounts']['JP']
if jp.get('anomaly') is False:
    print('  JP anomaly=false (correct)')
else:
    print(f'  JP anomaly={jp.get(\"anomaly\")} — expected false')
"

  # Test 3: Category breakdown complete
  echo ""
  echo "Test 3: Category breakdown complete"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
en_cats = d['accounts']['EN'].get('category_breakdown', {})
expected = {'portrait', 'fashion', 'artistic', 'trend_reactive'}
actual = set(en_cats.keys())
missing = expected - actual
if missing:
    print(f'  Missing categories: {missing}')
    sys.exit(1)
else:
    print(f'  EN categories: {sorted(actual)}')
    for cat, data in en_cats.items():
        print(f'    {cat}: {data}')
    sys.exit(0)
"
  if [ $? -eq 0 ]; then pass 3 "All 4 EN categories present in breakdown"; else fail 3 "Missing categories"; fi

  # Test 4: A/B test insufficient data
  echo ""
  echo "Test 4: A/B test insufficient data verdict"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
en_ab = d['accounts']['EN'].get('ab_test_status', {})
verdict = en_ab.get('verdict', '')
print(f'  EN ab_test verdict: {verdict}')
if 'insufficient' in verdict.lower():
    sys.exit(0)
else:
    print(f'  Expected verdict containing \"insufficient\", got \"{verdict}\"')
    sys.exit(1)
"
  if [ $? -eq 0 ]; then pass 4 "A/B test verdict is insufficient_data"; else fail 4 "Wrong A/B test verdict"; fi

  # Test 5: Telegram report size
  echo ""
  echo "Test 5: Telegram report size check"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
report = d.get('telegram_report', '')
length = len(report)
print(f'  telegram_report length: {length} chars')
if length == 0:
    print('  EMPTY — FAIL')
    sys.exit(1)
elif length > 1000:
    print(f'  Over 1000 chars — FAIL')
    sys.exit(1)
else:
    print(f'  Content preview: {report[:200]}...')
    sys.exit(0)
"
  if [ $? -eq 0 ]; then pass 5 "telegram_report non-empty and under 1000 chars"; else fail 5 "telegram_report size issue"; fi

  # Check telegram_alerts
  python3 -c "
import json
d = json.load(open('$REPORT'))
alerts = d.get('telegram_alerts', [])
print(f'  telegram_alerts count: {len(alerts)}')
for a in alerts:
    print(f'    - {a}')
"

  echo ""
  echo "Tests 1-5 verification complete."
}

# ============================================================
# Tests 6-7, 9, 11: Scout Intelligence
# ============================================================
run_scout() {
  echo "=========================================="
  echo "Tests 6-7, 9, 11: Scout Intelligence"
  echo "=========================================="
  echo ""

  # Step 1: Generate compact from existing data
  echo "Step 1: Generating compact file from existing scout_report_20260304.json..."
  python3 -c "
import json, sys, copy
sys.path.insert(0, 'scripts')
from scout import compute_pre_analysis, compact_report

# Load existing full report
with open('data/scout_report_${DATE}.json') as f:
    report = json.load(f)

# Write as 'raw' (it already is the full file)
with open('data/scout_raw_${DATE}.json', 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f'Wrote scout_raw_${DATE}.json ({len(json.dumps(report))} bytes)')

# Generate compact
compact = compact_report(report)
with open('data/scout_compact_${DATE}.json', 'w') as f:
    json.dump(compact, f, indent=2, ensure_ascii=False)
compact_size = len(json.dumps(compact))
print(f'Wrote scout_compact_${DATE}.json ({compact_size} bytes)')
"

  echo ""
  echo "Step 2: Run Claude subagent for Scout Intelligence Mode (analysis only)..."
  echo "Command:"
  echo ""
  cat << 'PROMPT_EOF'
claude -p "You are the Scout agent. Read agents/scout.md, section 'Daily Intelligence Mode' for your instructions.

Today's date: 2026-03-04

SKIP Step 1 (data collection) — raw and compact files already exist:
- Raw file: data/scout_raw_20260304.json (full report, ~450KB)
- Compact file: data/scout_compact_20260304.json (~30KB, with _pre_analysis stats)

Proceed directly to Step 2 (Read and Analyze):
- Read data/scout_compact_20260304.json for analysis input
- Use the _pre_analysis section for reply contamination, impression engagement, trending, and hashtag usage stats
- Filter new_accounts_discovered to quality accounts

Then Step 3 (Write Enriched Report):
- Read data/scout_raw_20260304.json as the base (copy ALL fields)
- ADD your analysis section
- Do NOT include _pre_analysis in the final output
- Write to: data/scout_report_enriched_test.json

Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
PROMPT_EOF

  echo ""
  echo "After running the command above, run verification:"
  echo "  bash scripts/run_phase5_tests_c.sh verify_scout"
}

verify_scout() {
  echo "--- Verifying Scout Intelligence output ---"
  REPORT="data/scout_report_enriched_test.json"

  if [ ! -f "$REPORT" ]; then
    fail 6 "File not found: $REPORT"
    return
  fi

  # Test 6: Backward compatibility — existing scout validation passes
  echo ""
  echo "Test 6: Scout backward compatibility (validate.py scout)"
  if python3 scripts/validate.py scout "$REPORT"; then
    pass 6 "Enriched report passes existing scout validation"
  else
    fail 6 "Enriched report fails backward compatibility"
  fi

  # Test 7: Analysis section present (validate.py scout_analysis)
  echo ""
  echo "Test 7: Analysis section present (validate.py scout_analysis)"
  if python3 scripts/validate.py scout_analysis "$REPORT"; then
    pass 7 "Analysis section present and valid"
  else
    fail 7 "scout_analysis validation failed"
  fi

  # Test 9: Reply contamination > 0
  echo ""
  echo "Test 9: Reply contamination > 0"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
rcr = d.get('analysis', {}).get('data_quality', {}).get('reply_contamination_rate', -1)
print(f'  reply_contamination_rate: {rcr}')
if rcr > 0:
    sys.exit(0)
else:
    print('  Expected > 0')
    sys.exit(1)
"
  if [ $? -eq 0 ]; then pass 9 "Reply contamination rate > 0"; else fail 9 "Reply contamination is 0 or missing"; fi

  # Test 11: Executive summary meaningful
  echo ""
  echo "Test 11: Executive summary meaningful"
  python3 -c "
import json, sys
d = json.load(open('$REPORT'))
es = d.get('analysis', {}).get('executive_summary', [])
print(f'  executive_summary entries: {len(es)}')
if len(es) < 3:
    print('  Need >= 3 entries')
    sys.exit(1)

all_good = True
for i, entry in enumerate(es):
    length = len(entry)
    has_numbers = any(c.isdigit() for c in entry)
    print(f'  [{i+1}] ({length} chars, has_numbers={has_numbers}): {entry[:100]}...')
    if length < 50:
        print(f'    WARNING: Entry too short (<50 chars)')
        all_good = False

if all_good:
    sys.exit(0)
else:
    sys.exit(1)
"
  if [ $? -eq 0 ]; then pass 11 "Executive summary has 3+ entries, each >50 chars"; else fail 11 "Executive summary issues"; fi

  echo ""
  echo "Tests 6-7, 9, 11 verification complete."
}

# ============================================================
# Test 10: Backward Compatibility — Strategist consumes enriched report
# ============================================================
run_scout_compat() {
  echo "=========================================="
  echo "Test 10: Backward Compatibility"
  echo "=========================================="
  echo ""

  ENRICHED="data/scout_report_enriched_test.json"
  if [ ! -f "$ENRICHED" ]; then
    echo "ERROR: Run scout tests first to create $ENRICHED"
    return
  fi

  echo "Running Strategist with enriched scout report as input..."
  echo "Command:"
  echo ""
  cat << 'PROMPT_EOF'
claude -p "You are the Strategist agent. Read agents/strategist.md for your instructions in 'Daily Strategy Mode'.

Today's date: 2026-03-04
Scout report: data/scout_report_enriched_test.json
Previous strategy: does not exist (produce from scratch)

Read the scout report and produce a daily growth strategy for both EN and JP accounts.
Write output to: data/strategy_test_enriched.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
PROMPT_EOF

  echo ""
  echo "After running the command above, run verification:"
  echo "  bash scripts/run_phase5_tests_c.sh verify_scout_compat"
}

verify_scout_compat() {
  echo "--- Verifying Test 10: Backward Compatibility ---"
  STRATEGY="data/strategy_test_enriched.json"
  ENRICHED="data/scout_report_enriched_test.json"

  if [ ! -f "$STRATEGY" ]; then
    fail 10 "File not found: $STRATEGY"
    return
  fi

  echo ""
  echo "Test 10a: Strategist output valid (validate.py strategist)"
  if python3 scripts/validate.py strategist "$STRATEGY"; then
    pass 10 "Strategist produces valid strategy from enriched scout report"
  else
    fail 10 "Strategist validation failed"
  fi

  echo ""
  echo "Test 10b: Cross-validation (validate.py cross)"
  if python3 scripts/validate.py cross "$ENRICHED" "$STRATEGY"; then
    echo -e "${GREEN}PASS${NC} — Test 10b: Cross-validation passes"
  else
    echo -e "${YELLOW}WARN${NC} — Test 10b: Cross-validation issues (may be non-blocking)"
  fi

  echo ""
  echo "Test 10 verification complete."
}

# ============================================================
# Tests 13-14, 17: Publisher Smart Outbound
# ============================================================
run_outbound() {
  echo "=========================================="
  echo "Tests 13-14, 17: Publisher Smart Outbound"
  echo "=========================================="
  echo ""
  echo "Running Claude subagent for Publisher Smart Outbound Mode..."
  echo "Command:"
  echo ""
  cat << 'PROMPT_EOF'
claude -p "You are the Publisher agent. Read agents/publisher.md, section 'Smart Outbound Mode' for your instructions.

Today's date: 2026-03-04
Account: EN
Strategy path: data/strategy_20260304.json
Content plan path: data/content_plan_20260304_EN.json

Generate a smart outbound engagement plan.

The strategy's outbound_strategy.target_accounts are: @sessypuuh, @yuumispm, @baharaykin, @Ava_starz, @bluebunny996

Step 2: Fetch target data by running:
python3 scripts/publisher_outbound_data.py --account EN --targets \"@sessypuuh,@yuumispm,@baharaykin,@Ava_starz,@bluebunny996\"

Then analyze the output and create the outbound plan.

Write plan to: data/outbound_plan_20260304_EN.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
PROMPT_EOF

  echo ""
  echo "After running the command above, run verification:"
  echo "  bash scripts/run_phase5_tests_c.sh verify_outbound"
}

verify_outbound() {
  echo "--- Verifying Publisher Smart Outbound output ---"
  PLAN="data/outbound_plan_${DATE}_EN.json"

  if [ ! -f "$PLAN" ]; then
    fail 13 "File not found: $PLAN"
    return
  fi

  # Test 13: Valid plan JSON
  echo ""
  echo "Test 13: validate.py outbound_plan"
  if python3 scripts/validate.py outbound_plan "$PLAN"; then
    pass 13 "Smart outbound plan valid JSON, all required fields present"
  else
    fail 13 "outbound_plan validation failed"
  fi

  # Test 17: No @ prefix in reply text
  echo ""
  echo "Test 17: No @ prefix in reply text"
  python3 -c "
import json, sys
d = json.load(open('$PLAN'))
issues = []
for i, t in enumerate(d.get('targets', [])):
    if t.get('skip'):
        continue
    reply = t.get('reply_to')
    if reply is None:
        print(f'  target[{i}] ({t.get(\"handle\")}): no reply_to (partial plan)')
        continue
    text = reply.get('reply_text', '')
    if text.lstrip().startswith('@'):
        issues.append(f'target[{i}] ({t.get(\"handle\")}): reply starts with @: {text[:50]}')
    else:
        print(f'  target[{i}] ({t.get(\"handle\")}): reply OK: {text[:80]}')
if issues:
    for issue in issues:
        print(f'  FAIL: {issue}')
    sys.exit(1)
else:
    sys.exit(0)
"
  if [ $? -eq 0 ]; then pass 17 "No reply text starts with @"; else fail 17 "Reply text starts with @"; fi

  # Test 14: Contextual reply references tweet content (manual check)
  echo ""
  echo "Test 14: Contextual reply references tweet content (manual review)"
  python3 -c "
import json
d = json.load(open('$PLAN'))
for t in d.get('targets', []):
    if t.get('skip'):
        print(f'  {t.get(\"handle\")}: SKIPPED — {t.get(\"skip_reason\", \"?\")}')
        continue
    reply = t.get('reply_to')
    if reply is None:
        print(f'  {t.get(\"handle\")}: no reply (partial plan)')
        continue
    print(f'  {t.get(\"handle\")}:')
    print(f'    Reply to tweet: {reply.get(\"tweet_id\")}')
    print(f'    Reply text: {reply.get(\"reply_text\")}')
    print(f'    Reasoning: {reply.get(\"reasoning\")}')
    print()
"
  echo "  >>> Review above: Do replies reference specific tweet content?"
  echo "  >>> If yes: Test 14 PASS. If generic/template-like: Test 14 FAIL."

  echo ""
  echo "Tests 13-14, 17 verification complete."
}

# ============================================================
# Main dispatcher
# ============================================================
case "$GROUP" in
  analyst)       run_analyst ;;
  verify_analyst) verify_analyst ;;
  scout)         run_scout ;;
  verify_scout)  verify_scout ;;
  scout_compat)  run_scout_compat ;;
  verify_scout_compat) verify_scout_compat ;;
  outbound)      run_outbound ;;
  verify_outbound) verify_outbound ;;
  all)
    echo "Run each test group in order:"
    echo "  1. bash scripts/run_phase5_tests_c.sh analyst"
    echo "     → Run the Claude command shown"
    echo "     → bash scripts/run_phase5_tests_c.sh verify_analyst"
    echo ""
    echo "  2. bash scripts/run_phase5_tests_c.sh scout"
    echo "     → Run the Claude command shown"
    echo "     → bash scripts/run_phase5_tests_c.sh verify_scout"
    echo ""
    echo "  3. bash scripts/run_phase5_tests_c.sh scout_compat"
    echo "     → Run the Claude command shown"
    echo "     → bash scripts/run_phase5_tests_c.sh verify_scout_compat"
    echo ""
    echo "  4. bash scripts/run_phase5_tests_c.sh outbound"
    echo "     → Run the Claude command shown"
    echo "     → bash scripts/run_phase5_tests_c.sh verify_outbound"
    ;;
  *)
    echo "Usage: bash scripts/run_phase5_tests_c.sh [analyst|verify_analyst|scout|verify_scout|scout_compat|verify_scout_compat|outbound|verify_outbound|all]"
    exit 1
    ;;
esac
