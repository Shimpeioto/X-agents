# Marc — Publishing Playbook

Reference file for the publishing workflow. Marc reads this after human approval of content plans.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).

## Goal

Publish approved content to X, run outbound engagement, collect metrics, and deliver a daily performance report.

## Prerequisites

Read `config/account_status.json`. Only publish and run outbound for **active accounts**.
Skip suspended accounts with a log message.

Content plans must have approved posts (`status == "approved"`). Check active accounts:
- For each active account: `data/content_plan_{YYYYMMDD}_{account}.json`

If no approved posts exist for any active account: log and **STOP**.

## Execution

### 1. Publish Approved Posts (Active Accounts Only)

For each **active** account with approved posts, run directly:

```bash
# Only run for active accounts (check config/account_status.json)
python3 scripts/publisher.py post --account EN
```

Expected: Content plan updated with `status: "posted"`, `tweet_id`, `post_url`, `posted_at`.
If Publisher exits non-zero: log error, continue to next account (do NOT stop).

### 2. Validate Publisher Output (Active Accounts Only)

For each **active** account:
```bash
python3 scripts/validate.py publisher data/content_plan_{YYYYMMDD}_{account}.json
python3 scripts/validate.py publisher_rate_limits data/rate_limits_{YYYYMMDD}.json
```

Log failures as warnings. Posts may have partially succeeded.

### 3. Outbound Engagement (Active Accounts Only)

Spawn the Outbound agent for each **active** account only:

```
"You are Outbound. Read agents/outbound.md for your full instructions.
Today's date: {YYYY-MM-DD}
Account: {EN|JP}
Strategy path: data/strategy_{YYYYMMDD}.json
Content plan path: data/content_plan_{YYYYMMDD}_{account}.json
Safety rules: config/outbound_rules.json

Execute your full workflow:
1. Check outbound history
2. Safety reasoning
3. Fetch target data
4. Plan engagement
5. Write plan to data/outbound_plan_{YYYYMMDD}_{account}.json
6. Execute via publisher.py smart-outbound"
```

Validate after completion:
```bash
python3 scripts/validate.py outbound_plan data/outbound_plan_{YYYYMMDD}_{account}.json
```

If Outbound agent fails: log error, skip outbound for this account.
Do NOT fall back to legacy `publisher.py outbound` without safety reasoning.

### 4. Send Publish Report to Telegram

```bash
python3 scripts/telegram_send.py "<formatted publish report>"
```

See [marc_schemas.md](marc_schemas.md) for the Publish Report Format.

Then generate and send the HTML version for mobile-friendly review.
Only pass **active account** content plan files to the report generator:

```bash
# Example with only EN active:
python3 scripts/generate_html_report.py publish_report \
  data/content_plan_{YYYYMMDD}_EN.json \
  --outbound-log data/outbound_log_{YYYYMMDD}.json --rate-limits data/rate_limits_{YYYYMMDD}.json
python3 scripts/telegram_send.py --document data/publish_report_{YYYYMMDD}.html "Publish Report — {YYYY-MM-DD}"
```

### 5. Collect Metrics (Active Accounts Only)

Check if at least 1 hour has passed since the latest `posted_at` timestamp. If not, log a warning and skip.

For each **active** account:
```bash
python3 scripts/analyst.py collect --account {account}
```

### 6. Generate Metric Summaries (Active Accounts Only)

For each **active** account:
```bash
python3 scripts/analyst.py summary --account {account}
```

Validate:
```bash
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_{account}.json
python3 scripts/validate.py analyst_metrics data/metrics_history.db
```

### 7. Daily Report (Analyst Intelligence Mode)

Spawn an Analyst teammate:

```
"You are Analyst. Read agents/analyst.md, section 'Intelligence Mode' for your instructions.
Today's date: {YYYY-MM-DD}
Raw metrics: data/metrics_{YYYYMMDD}_EN.json, data/metrics_{YYYYMMDD}_JP.json
Strategy: data/strategy_{YYYYMMDD}.json
Pipeline state: data/pipeline_state_{YYYYMMDD}.json
Outbound log: data/outbound_log_{YYYYMMDD}.json
Content plans: data/content_plan_{YYYYMMDD}_EN.json, data/content_plan_{YYYYMMDD}_JP.json
Yesterday's report (if exists): data/daily_report_{prev_YYYYMMDD}.json
Analyze all data, detect anomalies, evaluate A/B tests, and produce the daily report.
Write output to: data/daily_report_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

Validate:
```bash
python3 scripts/validate.py analyst_report data/daily_report_{YYYYMMDD}.json
```

If validation fails: fall back to composing a basic Telegram message from the raw metrics summaries.

### 8. Send Daily Report + Alerts

1. Read `daily_report_{YYYYMMDD}.json`
2. Send `telegram_report` field:
   ```bash
   python3 scripts/telegram_send.py "<telegram_report content>"
   ```
3. For each entry in `telegram_alerts`:
   ```bash
   python3 scripts/telegram_send.py "<alert content>"
   ```
4. Generate and send the HTML version for mobile-friendly review:
   ```bash
   python3 scripts/generate_html_report.py daily_report data/daily_report_{YYYYMMDD}.json
   python3 scripts/telegram_send.py --document data/daily_report_{YYYYMMDD}.html "Daily Report — {YYYY-MM-DD}"
   ```

## Error Recovery

- Publisher post failure: log, continue to next account
- Outbound agent failure: log error, skip outbound (do NOT fall back without safety reasoning)
- Analyst failure: log as warning, skip metrics (can re-run later)
- Daily report failure: compose basic report from raw metrics
- Telegram send failure: log as warning, never fail the workflow
