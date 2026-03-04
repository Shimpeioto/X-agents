# Marc — Publishing Sequence (Steps P1-P8)

Reference file for the publishing workflow. Marc reads this after human approval of content plans.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).

## Step P1: Check Approval Status

Read content plans for both accounts:
- `data/content_plan_{YYYYMMDD}_EN.json`
- `data/content_plan_{YYYYMMDD}_JP.json`

Count posts with `status == "approved"` for each account. If no approved posts exist for either account, log and **STOP** — nothing to publish.

## Step P2: Run Publisher Post

For each account with approved posts:

```bash
cd /path/to/project && python3 scripts/publisher.py post --account EN
```

```bash
cd /path/to/project && python3 scripts/publisher.py post --account JP
```

- Expected: Content plan updated with `status: "posted"`, `tweet_id`, `post_url`, `posted_at` for each published post
- If Publisher exits non-zero: log the error, record task as failed, continue to next account (do NOT stop)
- Record tasks: `{"id": "publisher_en_post", "agent": "publisher", ...}`, `{"id": "publisher_jp_post", ...}`

## Step P3: Validate Publisher Output

For each account that was published:

```bash
python3 scripts/validate.py publisher data/content_plan_{YYYYMMDD}_EN.json
python3 scripts/validate.py publisher data/content_plan_{YYYYMMDD}_JP.json
```

- If "FAIL": log as warning. Posts may have partially succeeded.
- Record tasks: `{"id": "publisher_en_validation", ...}`, `{"id": "publisher_jp_validation", ...}`

Validate rate limits:

```bash
python3 scripts/validate.py publisher_rate_limits data/rate_limits_{YYYYMMDD}.json
```

- If "FAIL": log as warning.
- Record task: `{"id": "publisher_rate_limits_validation", ...}`

## Step P4: Run Publisher Outbound

For each account:

```bash
python3 scripts/publisher.py outbound --account EN
python3 scripts/publisher.py outbound --account JP
```

- Outbound engagement runs with random 30-120s delays between operations
- If Publisher exits non-zero: log the error, continue (outbound failure is not critical)
- Record tasks: `{"id": "publisher_en_outbound", ...}`, `{"id": "publisher_jp_outbound", ...}`

## Step P5: Send Publish Report to Telegram

```bash
python3 scripts/telegram_send.py "<formatted publish report>"
```

See [marc_schemas.md](marc_schemas.md) for the Publish Report Format.

- If `telegram_send.py` fails: log as warning, do NOT fail.
- Record task: `{"id": "telegram_publish_report", "agent": "marc", ...}`

## Step P6: Run Analyst Collect

Check if at least 1 hour has passed since the latest `posted_at` timestamp across both accounts. If not, log a warning and skip (can be re-run manually).

```bash
python3 scripts/analyst.py collect
```

- Expected: Metrics written to SQLite, no JSON output for collect
- If Analyst exits non-zero: log as warning, continue (metrics collection failure is not critical)
- Record task: `{"id": "analyst_collect", "agent": "analyst", ...}`

## Step P7: Generate Summaries + Validate

```bash
python3 scripts/analyst.py summary --account EN
python3 scripts/analyst.py summary --account JP
```

- Expected output files: `data/metrics_{YYYYMMDD}_EN.json`, `data/metrics_{YYYYMMDD}_JP.json`
- Record tasks: `{"id": "analyst_en_summary", ...}`, `{"id": "analyst_jp_summary", ...}`

Then validate:

```bash
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_EN.json
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_JP.json
```

- If "FAIL": log as warning
- Record tasks: `{"id": "analyst_en_validation", ...}`, `{"id": "analyst_jp_validation", ...}`

```bash
python3 scripts/validate.py analyst_metrics data/metrics_history.db
```

- If "FAIL": log as warning
- Record task: `{"id": "analyst_metrics_validation", ...}`

## Step P8: Follower Anomaly Check + Daily Report

### Follower Anomaly Detection

Read today's metrics summaries for both accounts:

1. Read `followers` and `followers_change` from `data/metrics_{YYYYMMDD}_{account}.json`
2. If `abs(followers_change) > followers * 0.10` (>10% change): send alert to Telegram
3. If first day (no yesterday data): skip anomaly check

Alert format — see [marc_schemas.md](marc_schemas.md).

### Daily Report

Read both summaries and the War Room scores (from Step 11's `war_room` task `notes` field in pipeline state) to compose the daily report.

```bash
python3 scripts/telegram_send.py "<formatted daily report>"
```

See [marc_schemas.md](marc_schemas.md) for the Daily Report Format.

- If `telegram_send.py` fails: log as warning, do NOT fail.
- Record task: `{"id": "daily_report", "agent": "marc", ...}`
