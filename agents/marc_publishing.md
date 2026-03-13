# Marc — Publishing Playbook

Reference file for the publishing workflow. Marc reads this after human approval of content plans.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).

## Goal

Publish approved content to X and run outbound engagement. Metrics collection and daily reporting are handled by the evening war room (see [marc_warroom.md](marc_warroom.md)).

## Prerequisites

Read `config/account_status.json`. Only publish and run outbound for **active accounts**.
Skip suspended accounts with a log message.

Content plans must have approved posts (`status == "approved"`). Check active accounts:
- For each active account: `data/content/content_plan_{YYYYMMDD}_{account}.json`

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
python3 scripts/validate.py publisher data/content/content_plan_{YYYYMMDD}_{account}.json
python3 scripts/validate.py publisher_rate_limits data/pipeline/rate_limits_{YYYYMMDD}.json
```

Log failures as warnings. Posts may have partially succeeded.

### 3. Outbound Engagement (Active Accounts Only)

Spawn the Outbound agent for each **active** account only, with **model: sonnet**:

```
"You are Outbound. Read agents/outbound.md for your full instructions.
Today's date: {YYYY-MM-DD}
Account: {EN|JP}
Strategy path: data/strategy/strategy_{YYYYMMDD}.json
Content plan path: data/content/content_plan_{YYYYMMDD}_{account}.json
Safety rules: config/outbound_rules.json

Execute your full workflow:
1. Check outbound history
2. Safety reasoning
3. Fetch target data
4. Plan engagement
5. Write plan to data/outbound/outbound_plan_{YYYYMMDD}_{account}.json
6. Execute via publisher.py smart-outbound"
```

Validate after completion:
```bash
python3 scripts/validate.py outbound_plan data/outbound/outbound_plan_{YYYYMMDD}_{account}.json
```

If Outbound agent fails: log error, skip outbound for this account.
Do NOT fall back to legacy `publisher.py outbound` without safety reasoning.

After outbound completes, read `data/outbound/outbound_log_{YYYYMMDD}.json`. If it contains a `failed_replies` array, escalate to the operator via Telegram with exact instructions for manual replies:

```bash
python3 scripts/telegram_send.py "Replies that need manual posting from @{handle}:

1. Reply to @{target}: \"{reply_text}\"
   → {tweet_url}
..."
```

Don't just report failures — provide the alternative path for the human to complete the goal.

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
  data/content/content_plan_{YYYYMMDD}_EN.json \
  --outbound-log data/outbound/outbound_log_{YYYYMMDD}.json --rate-limits data/pipeline/rate_limits_{YYYYMMDD}.json
python3 scripts/telegram_send.py --document data/reports/publish_report_{YYYYMMDD}.html "Publish Report — {YYYY-MM-DD}"
```

**Note**: Steps 5-8 (metrics collection, summaries, daily report, alerts) have moved to the evening war room.
See [marc_warroom.md](marc_warroom.md) for the full metrics and reporting workflow.

## Error Recovery

- Publisher post failure: log, continue to next account
- Outbound agent failure: log error, skip outbound (do NOT fall back without safety reasoning)
- Telegram send failure: log as warning, never fail the workflow
