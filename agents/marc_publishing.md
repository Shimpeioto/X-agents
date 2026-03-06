# Marc — Publishing Playbook

Reference file for the publishing workflow. Marc reads this after human approval of content plans.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).

## Goal

Publish approved content to X, run outbound engagement, collect metrics, and deliver a daily performance report.

## Prerequisites

Content plans must have approved posts (`status == "approved"`). Check both:
- `data/content_plan_{YYYYMMDD}_EN.json`
- `data/content_plan_{YYYYMMDD}_JP.json`

If no approved posts exist for either account: log and **STOP**.

## Execution

### 1. Publish Approved Posts

For each account with approved posts, run directly:

```bash
python3 scripts/publisher.py post --account EN
python3 scripts/publisher.py post --account JP
```

Expected: Content plan updated with `status: "posted"`, `tweet_id`, `post_url`, `posted_at`.
If Publisher exits non-zero: log error, continue to next account (do NOT stop).

### 2. Validate Publisher Output

```bash
python3 scripts/validate.py publisher data/content_plan_{YYYYMMDD}_EN.json
python3 scripts/validate.py publisher data/content_plan_{YYYYMMDD}_JP.json
python3 scripts/validate.py publisher_rate_limits data/rate_limits_{YYYYMMDD}.json
```

Log failures as warnings. Posts may have partially succeeded.

### 3. Smart Outbound Engagement

For each account, spawn a Publisher teammate for outbound planning:

**3a. Generate Outbound Plan:**

```
"You are Publisher. Read agents/publisher.md, section 'Smart Outbound Mode' for your instructions.
Today's date: {YYYY-MM-DD}
Account: {EN|JP}
Strategy path: data/strategy_{YYYYMMDD}.json
Content plan path: data/content_plan_{YYYYMMDD}_{account}.json
Generate a smart outbound engagement plan.
Write plan to: data/outbound_plan_{YYYYMMDD}_{account}.json
Output ONLY valid JSON — no markdown code fences, no commentary."
```

**3b. Validate Outbound Plan:**

```bash
python3 scripts/validate.py outbound_plan data/outbound_plan_{YYYYMMDD}_{account}.json
```

If validation fails: fall back to legacy outbound (`python3 scripts/publisher.py outbound --account {account}`)

**3c. Execute Outbound Plan:**

```bash
python3 scripts/publisher.py smart-outbound --account {account} --plan data/outbound_plan_{YYYYMMDD}_{account}.json
```

### 4. Send Publish Report to Telegram

```bash
python3 scripts/telegram_send.py "<formatted publish report>"
```

See [marc_schemas.md](marc_schemas.md) for the Publish Report Format.

Then generate and send the HTML version for mobile-friendly review:

```bash
python3 scripts/generate_html_report.py publish_report \
  data/content_plan_{YYYYMMDD}_EN.json data/content_plan_{YYYYMMDD}_JP.json \
  --outbound-log data/outbound_log_{YYYYMMDD}.json --rate-limits data/rate_limits_{YYYYMMDD}.json
python3 scripts/telegram_send.py --document data/publish_report_{YYYYMMDD}.html "Publish Report — {YYYY-MM-DD}"
```

### 5. Collect Metrics

Check if at least 1 hour has passed since the latest `posted_at` timestamp. If not, log a warning and skip.

```bash
python3 scripts/analyst.py collect
```

### 6. Generate Metric Summaries

```bash
python3 scripts/analyst.py summary --account EN
python3 scripts/analyst.py summary --account JP
```

Validate:
```bash
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_EN.json
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_JP.json
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
- Outbound plan failure: fall back to legacy `publisher.py outbound`
- Analyst failure: log as warning, skip metrics (can re-run later)
- Daily report failure: compose basic report from raw metrics
- Telegram send failure: log as warning, never fail the workflow
