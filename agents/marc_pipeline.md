# Marc — Pipeline Playbook

Reference file for the daily content pipeline. Marc reads this when executing the pipeline.

Today's date is provided in the invocation prompt as YYYY-MM-DD.
For file paths, strip dashes to get YYYYMMDD format (e.g., `data/scout_report_20260303.json`).
For JSON date fields, use the original YYYY-MM-DD format.

## Goal

Produce today's content plans (EN + JP) ready for human approval.

## Prerequisites

Before starting:
```bash
mkdir -p logs data
```

Check for pause flag:
```bash
if [ -f data/.paused ]; then echo "PAUSED"; else echo "OK"; fi
```
If paused, log the event and **STOP**.

## Task Dependencies

```
scout_data → strategist → [creator_en, creator_jp] (parallel) → war_room → preview
```

Each step must validate before the next begins. Creator EN and JP can run in parallel.

## Execution

### 1. Initialize Pipeline State

Create `data/pipeline_state_{YYYYMMDD}.json` — see [marc_schemas.md](marc_schemas.md) for the initial state template.

### 2. Spawn Scout Teammate

Spawn a Scout teammate:
```
"You are Scout. Read agents/scout.md, section 'Daily Intelligence Mode' for your instructions.
Today's date: {YYYY-MM-DD}
Run data collection with compact output, then analyze the raw data and produce an enriched report.
Write output to: data/scout_report_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

Scout internally runs `python3 scripts/scout.py --raw --compact` for data collection, then enriches with analysis.

If Scout fails: message with error context, retry ONCE. If retry also fails, fall back to `python3 scripts/scout.py` (raw report without analysis).

### 3. Validate Scout

```bash
python3 scripts/validate.py scout data/scout_report_{YYYYMMDD}.json
```

If FAIL: log, update pipeline state, **STOP**.

### 4. Spawn Strategist Teammate

```
"You are Strategist. Read agents/strategist.md, section 'Daily Strategy Mode' for your instructions.
Today's date: {YYYY-MM-DD}
Scout report path: data/scout_report_{YYYYMMDD}.json
Generate today's growth strategy based on the scout report.
Write the output to: data/strategy_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

**NOTE**: Strategist writes ONLY the dated file. You (Marc) write `strategy_current.json` in the finalization step.

### 5. Validate Strategist + Cross-validate

```bash
python3 scripts/validate.py strategist data/strategy_{YYYYMMDD}.json
python3 scripts/validate.py cross data/scout_report_{YYYYMMDD}.json data/strategy_{YYYYMMDD}.json
```

If strategist validation FAILs: log, update pipeline state, **STOP**.
Cross-validation failures: log as warnings, flag for human review. Do NOT stop.

Apply your own semantic judgment:
- Does the strategy make sense given the scout data?
- Are there contradictions?
- Are the recommendations actionable and specific?

### 6. Spawn Creator EN + Creator JP Teammates IN PARALLEL

Spawn **both** at the same time:

**Creator EN:**
```
"You are Creator. Read agents/creator.md for your instructions.
Today's date: {YYYY-MM-DD}
Account: EN
Strategy path: data/strategy_{YYYYMMDD}.json
Generate today's content plan for the EN account.
Write the output to: data/content_plan_{YYYYMMDD}_EN.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

**Creator JP:**
```
"You are Creator. Read agents/creator.md for your instructions.
Today's date: {YYYY-MM-DD}
Account: JP
Strategy path: data/strategy_{YYYYMMDD}.json
Generate today's content plan for the JP account.
Write the output to: data/content_plan_{YYYYMMDD}_JP.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

### 7. Validate Both Content Plans

For each account (EN, JP):
```bash
python3 scripts/validate.py creator data/content_plan_{YYYYMMDD}_{account}.json
python3 scripts/validate.py creator_cross data/content_plan_{YYYYMMDD}_{account}.json data/strategy_{YYYYMMDD}.json
```

Creator validation FAIL: log, update pipeline state, **STOP**.
Cross-validation FAIL: log as warning (Creator may have made reasonable deviations).

### 8. War Room (Scored Evaluation)

Perform a **scored evaluation** (0-100 points) of each account's content plan against the strategy.

For EACH account (EN, JP), apply the 6-criterion rubric:

| # | Criterion | Max | Scoring Logic |
|---|---|---|---|
| 1 | Category match | 20 | Check each post's `category` against strategy `posting_schedule[slot].category` (case-insensitive). Deduct `20 / post_count` per mismatch. |
| 2 | Hashtag compliance | 20 | Check all `always_use` hashtags present in every post's `hashtags`. Deduct `20 / (post_count * always_use_count)` per missing tag. |
| 3 | Text quality | 20 | No post starts with `@` (deduct 5 per violation). All posts <= 280 chars unless text-only justified (deduct 3). Texts are distinct (deduct 5 if >50% seem repetitive). |
| 4 | Image prompt variety | 15 | Image prompts are diverse. Deduct 5 per pair of near-duplicate prompts (same subject + style). |
| 5 | Reply template quality | 15 | 5-10 templates (deduct 5 if out of range), no duplicates (deduct 3 per duplicate), varied tone (deduct 3 if all feel identical). |
| 6 | A/B test compliance | 10 | At least one post has `ab_test_variant` set matching the strategy's `ab_test.variable`. Full marks if yes, 0 if not. |

**Scoring thresholds**:

| Score | Status | Action |
|---|---|---|
| 90-100 | Excellent | Proceed with confidence |
| 70-89 | Good | Proceed, note improvement areas in warnings |
| 50-69 | Warning | Log warnings, flag for human review in Telegram preview |
| 0-49 | Poor | Log errors, send alert to Telegram, recommend re-running Creator |

Record scores in pipeline state task notes.

### 9. Send Content Preview to Telegram

```bash
python3 scripts/telegram_send.py "<formatted preview message>"
```

See [marc_schemas.md](marc_schemas.md) for the Content Preview Format.

If `telegram_send.py` fails: log as warning, do NOT fail the pipeline.

### 10. Finalize

Only after ALL validations pass:

1. **Copy strategy to current**: Copy `data/strategy_{YYYYMMDD}.json` → `data/strategy_current.json`
2. **Update pipeline state**: Set `status: "completed"`, `completed_at`, calculate `duration_seconds`
3. **Write pipeline log**: `logs/pipeline_{YYYYMMDD}.log` with timestamped entries for each step
4. **Send completion notification** (best-effort):
   ```bash
   python3 scripts/telegram_send.py "Pipeline complete -- {YYYY-MM-DD} ({duration}s)"
   ```

## Error Recovery

When a teammate produces invalid output:
1. Read the validation output
2. Reason about what went wrong
3. Message the teammate with the specific error and instructions to fix
4. Retry ONCE
5. If retry also fails: log both attempts, update pipeline state, **STOP**

**Scout fallback**: If Scout's enriched report fails, fall back to `python3 scripts/scout.py` (raw report without analysis). Strategist can still consume it.
