# Marc — War Room Playbook

Reference file for the PDCA war room sessions. Marc reads this for morning and evening briefings.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).
Yesterday's date: subtract 1 day for file lookups.

## Goal

Close the PDCA loop: Check yesterday's results (morning) and generate strategy feedback (evening) so that insights flow back into tomorrow's Strategist run.

## Prerequisites

Read `config/account_status.json`. Only report on and collect metrics for **active accounts**.

---

## Morning War Room (05:30 JST)

Review yesterday's results and send the operator a morning briefing before the pipeline runs.

### 1. Read Yesterday's Data

For each **active** account, read:
- `data/daily_report_{yesterday_YYYYMMDD}.json` — yesterday's daily report
- `data/content_plan_{yesterday_YYYYMMDD}_{account}.json` — what was posted
- `data/outbound_log_{yesterday_YYYYMMDD}.json` — outbound actions taken
- `data/strategy_{yesterday_YYYYMMDD}.json` — yesterday's strategy (for A/B test context)

If `daily_report` does not exist (e.g., first run, or metrics collection failed):
- Log a warning and compose a minimal briefing noting data unavailability
- Do NOT block the pipeline — proceed with whatever data is available

### 2. Compose Morning Briefing

Build a concise operator briefing covering:

- **Follower changes**: Current count and delta (e.g., "EN: 1,250 (+12)")
- **Engagement summary**: Total likes, retweets, replies across all posted content
- **Top post**: Best performing post by total engagement (post_id, category, likes)
- **A/B test status**: Which test is active, days remaining, early signal (if any)
- **Anomalies & alerts**: Any follower anomalies, failed outbound actions, or issues
- **Needs human decision**: Anything stuck waiting for operator input
- **Today's schedule**: Pipeline at 06:00, outbound at 14:00, evening review at 22:00

Keep the Telegram message scannable — bullet points, bold numbers, under 1000 characters.

### 3. Send Morning Briefing via Telegram

```bash
python3 scripts/telegram_send.py "<morning briefing text>"
```

Generate and send HTML for detailed review:
```bash
python3 scripts/generate_html_report.py generic data/morning_briefing_{YYYYMMDD}.json --title "Morning Briefing — {YYYY-MM-DD}"
python3 scripts/telegram_send.py --document data/morning_briefing_{YYYYMMDD}.html "Morning Briefing — {YYYY-MM-DD}"
```

### 4. Write Morning Briefing File

Write `data/morning_briefing_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "type": "morning_briefing",
  "daily_report_used": "data/daily_report_YYYYMMDD.json",
  "accounts": {
    "EN": {
      "followers": 1250,
      "followers_change": 12,
      "total_likes": 95,
      "total_retweets": 28,
      "total_replies": 7,
      "top_post": {
        "post_id": "EN_20260310_01",
        "category": "engagement_questions",
        "likes": 45
      },
      "ab_test_status": "caption style — day 3/7, variant A leading by 72%",
      "anomalies": [],
      "needs_attention": []
    }
  },
  "summary": "Concise text summary of the briefing",
  "telegram_message": "Pre-composed Telegram message text"
}
```

Validate:
```bash
python3 scripts/validate.py morning_briefing data/morning_briefing_{YYYYMMDD}.json
```

---

## Evening War Room (22:00 JST)

Collect today's metrics, generate the daily report, produce strategy feedback for tomorrow, and send the operator a daily summary.

### 1. Collect Metrics (Active Accounts Only)

For each **active** account:
```bash
python3 scripts/analyst.py collect --account {account}
```

If no posted tweets exist today: log and skip collection (not an error).

### 2. Generate Metric Summaries (Active Accounts Only)

For each **active** account:
```bash
python3 scripts/analyst.py summary --account {account}
```

Validate:
```bash
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_{account}.json
python3 scripts/validate.py analyst_metrics data/metrics_history.db
```

### 3. Daily Report (Analyst Intelligence Mode)

Spawn an Analyst teammate with **model: sonnet**:

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

### 4. Generate Strategy Feedback (THE PDCA BRIDGE)

This is the key new artifact. Read the daily report and today's strategy, then produce feedback for tomorrow's Strategist.

For EACH **active** account, analyze:

1. **Category Performance**: Group posts by category. Which categories had the highest engagement? Rank them. Calculate `vs_average` (percentage above/below account average).
   - Recommendation: `"increase"` if >50% above average, `"maintain_or_increase"` if >20% above, `"maintain"` if within 20%, `"decrease"` if >20% below, `"reduce"` if >50% below.

2. **A/B Test Evaluation**:
   - Read the strategy's `ab_test` definition (variable, variant_a, variant_b, duration_days, start_date)
   - Count days elapsed since `start_date`
   - Compare metrics between variant A and variant B posts
   - Confidence: `"low"` (<3 days or <2 data points per variant), `"medium"` (3-5 days, 2+ points per variant), `"high"` (5+ days, 3+ points per variant, >30% performance gap)
   - If confidence is `"high"` and duration is complete: set `status: "concluded"`, `winner: "variant_a|variant_b"`
   - Otherwise: set `status: "running"`, `winner: null`

3. **Posting Time Effectiveness**: Rank slots by average engagement. Note which time windows perform best.

4. **Outbound Effectiveness**: Check outbound log — did any target accounts reciprocally engage with us? Separate targets into `effective_targets` (reciprocal engagement observed) and `ineffective_targets` (no response after 3+ days of engagement).

5. **Recommended Adjustments**: Based on all the above, generate specific recommendations:
   - `type`: One of `"content_mix"`, `"ab_test"`, `"posting_time"`, `"outbound_target"`
   - `confidence`: `"low"`, `"medium"`, or `"high"`
   - `description`: Specific change (e.g., "Increase engagement_questions 40%→45%, decrease image_showcase 25%→20%")
   - `rationale`: Data-backed reason

Write `data/strategy_feedback_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "daily_report_used": "data/daily_report_YYYYMMDD.json",
  "strategy_used": "data/strategy_YYYYMMDD.json",
  "accounts": {
    "EN": {
      "category_performance": [
        {
          "category": "engagement_questions",
          "posts_count": 2,
          "total_likes": 89,
          "avg_engagement_per_post": 51,
          "rank": 1,
          "vs_average": "+45%",
          "recommendation": "maintain_or_increase"
        }
      ],
      "ab_test_evaluation": {
        "variable": "caption style",
        "status": "running",
        "days_elapsed": 3,
        "days_remaining": 4,
        "early_signal": "variant_a leading by 72%",
        "confidence": "low",
        "winner": null,
        "conclusion": null
      },
      "posting_time_effectiveness": [
        {"slot": 1, "time": "13:00 UTC", "avg_engagement": 55, "rank": 1}
      ],
      "outbound_effectiveness": {
        "total_likes_given": 12,
        "reciprocal_engagement": 0,
        "effective_targets": [],
        "ineffective_targets": ["@target1"]
      },
      "recommended_adjustments": [
        {
          "type": "content_mix",
          "confidence": "medium",
          "description": "Increase engagement_questions 40%→45%, decrease image_showcase 25%→20%",
          "rationale": "engagement_questions outperformed by 85% over 3 days"
        }
      ]
    }
  }
}
```

Validate:
```bash
python3 scripts/validate.py strategy_feedback data/strategy_feedback_{YYYYMMDD}.json
```

### 5. Send Daily Report + Alerts via Telegram

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

---

## Error Recovery

- Missing daily report: compose minimal briefing from raw metrics, note unavailability
- Analyst collection failure: log as warning, proceed with strategy feedback using available data
- Strategy feedback generation failure: log error, skip feedback (tomorrow's Strategist will run without it, same as before)
- Telegram send failure: log as warning, never fail the war room
- No posted content today: skip metrics collection, note in briefing
