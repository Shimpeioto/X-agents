# Marc — Pipeline Sequence (Steps 1-13)

Reference file for the daily overnight pipeline. Marc reads this when executing `run_pipeline.sh`.

Today's date is provided in the invocation prompt as YYYY-MM-DD.
For file paths, strip dashes to get YYYYMMDD format (e.g., `data/scout_report_20260303.json`).
For JSON date fields, use the original YYYY-MM-DD format.

**IMPORTANT**: Before starting, create required directories:
```bash
mkdir -p logs data
```

**IMPORTANT**: Check for pause flag before running:
```bash
if [ -f data/.paused ]; then echo "PAUSED"; else echo "OK"; fi
```
If paused, log the event and **STOP**. Do not run the pipeline while paused.

## Step 1: Initialize Pipeline State

Create `data/pipeline_state_{YYYYMMDD}.json` — see [marc_schemas.md](marc_schemas.md) for the initial state template and full schema.

## Step 2: Run Scout

```bash
cd /path/to/project && python3 scripts/scout.py
```

- Expected output file: `data/scout_report_{YYYYMMDD}.json`
- Record the task in pipeline state: `{"id": "scout_run", "agent": "scout", "status": "completed", ...}`
- If Scout fails (non-zero exit): log the error (include stderr), update pipeline state with `status: "failed"`, **STOP**.

## Step 3: Validate Scout

```bash
python3 scripts/validate.py scout data/scout_report_{YYYYMMDD}.json
```

- If output starts with "FAIL": log failures, update pipeline state with `status: "failed"`, **STOP**.
- If "PASS": proceed. Record task in pipeline state.

## Step 4: Run Strategist (isolated subagent)

```bash
claude -p "You are the Strategist agent. Read agents/strategist.md, section 'Daily Strategy Mode' for your instructions.
Today's date: {YYYY-MM-DD}
Scout report path: data/scout_report_{YYYYMMDD}.json
Generate today's growth strategy based on the scout report.
Write the output to: data/strategy_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
```

- Expected output file: `data/strategy_{YYYYMMDD}.json`
- **NOTE**: Strategist writes ONLY the dated file. You (Marc) write `strategy_current.json` in Step 13 after all validations pass.
- If Strategist fails: apply H3 error recovery (see marc.md). Retry **ONCE** with error context. If retry also fails: log both attempts, update pipeline state, **STOP**.

## Step 5: Validate Strategist

```bash
python3 scripts/validate.py strategist data/strategy_{YYYYMMDD}.json
```

- If "FAIL": log failures, update pipeline state with `status: "failed"`, **STOP**.
- If "PASS": proceed. Record task in pipeline state.

## Step 6: Cross-validate

```bash
python3 scripts/validate.py cross data/scout_report_{YYYYMMDD}.json data/strategy_{YYYYMMDD}.json
```

- Read the deterministic cross-validation results.
- THEN apply your own semantic judgment:
  - Does the strategy make sense given the scout data?
  - Are there contradictions (e.g., Scout shows EN outperforming JP, but strategy claims JP is stronger without explanation)?
  - Are the recommendations actionable and specific?
- If the deterministic check says FAIL: log as error.
- If your semantic review finds contradictions: log them as **warnings** in pipeline state. Do NOT stop — flag for human review.
- Record task in pipeline state.

## Step 7: Run Creator for EN (isolated subagent)

```bash
claude -p "You are the Creator agent. Read agents/creator.md for your instructions.
Today's date: {YYYY-MM-DD}
Account: EN
Strategy path: data/strategy_{YYYYMMDD}.json
Generate today's content plan for the EN account based on the strategy.
Write the output to: data/content_plan_{YYYYMMDD}_EN.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
```

- Expected output file: `data/content_plan_{YYYYMMDD}_EN.json`
- Record task: `{"id": "creator_en_run", "agent": "creator", "status": "completed", ...}`
- If Creator fails: apply H3 error recovery. Retry **ONCE** with error context. If retry also fails: log, update pipeline state, **STOP**.

## Step 8: Validate Creator EN

```bash
python3 scripts/validate.py creator data/content_plan_{YYYYMMDD}_EN.json
```

- If "FAIL": log failures, update pipeline state with `status: "failed"`, **STOP**.
- If "PASS": proceed.

Then cross-validate against strategy:

```bash
python3 scripts/validate.py creator_cross data/content_plan_{YYYYMMDD}_EN.json data/strategy_{YYYYMMDD}.json
```

- If "FAIL": log as warning (not hard fail). Creator may have made reasonable deviations.
- Record both validation tasks in pipeline state.

## Step 9: Run Creator for JP (isolated subagent)

```bash
claude -p "You are the Creator agent. Read agents/creator.md for your instructions.
Today's date: {YYYY-MM-DD}
Account: JP
Strategy path: data/strategy_{YYYYMMDD}.json
Generate today's content plan for the JP account based on the strategy.
Write the output to: data/content_plan_{YYYYMMDD}_JP.json
Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
```

- Expected output file: `data/content_plan_{YYYYMMDD}_JP.json`
- Record task: `{"id": "creator_jp_run", "agent": "creator", ...}`
- If Creator fails: apply H3 error recovery. Retry **ONCE**. If retry fails: log, update pipeline state, **STOP**.

## Step 10: Validate Creator JP

```bash
python3 scripts/validate.py creator data/content_plan_{YYYYMMDD}_JP.json
```

- If "FAIL": log failures, update pipeline state with `status: "failed"`, **STOP**.
- If "PASS": proceed.

Then cross-validate:

```bash
python3 scripts/validate.py creator_cross data/content_plan_{YYYYMMDD}_JP.json data/strategy_{YYYYMMDD}.json
```

- If "FAIL": log as warning.
- Record both validation tasks in pipeline state.

## Step 11: War Room (Scored Evaluation)

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

Record scores in pipeline state task notes: `"EN: 85/100 (Good), JP: 92/100 (Excellent). EN: -10 hashtag compliance, -5 A/B test."`

## Step 12: Send Content Preview to Telegram

```bash
python3 scripts/telegram_send.py "<formatted preview message>"
```

See [marc_schemas.md](marc_schemas.md) for the Content Preview Format.

- If `telegram_send.py` fails (non-zero exit): log as warning, do NOT fail the pipeline.
- Record task: `{"id": "telegram_preview", "agent": "marc", ...}`

## Step 13: Finalize

Only after ALL validations pass:

1. **Copy strategy to current**: Copy `data/strategy_{YYYYMMDD}.json` -> `data/strategy_current.json`
   - Marc is the **sole writer** of `strategy_current.json`. Strategist never writes it directly.

2. **Update pipeline state**: Set `status: "completed"`, `completed_at`, calculate `duration_seconds`

3. **Write pipeline log**: `logs/pipeline_{YYYYMMDD}.log` with timestamped entries for each step

4. **Send completion notification** (best-effort):
   ```bash
   python3 scripts/telegram_send.py "Pipeline complete -- {YYYY-MM-DD} ({duration}s)"
   ```
