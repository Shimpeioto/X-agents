# Marc — Schemas & Report Formats

Reference file for pipeline state schema and Telegram message formats.

## Pipeline State Schema

File: `data/pipeline/pipeline_state_{YYYYMMDD}.json`

```json
{
  "pipeline_date": "YYYY-MM-DD",
  "started_at": "ISO timestamp",
  "completed_at": "ISO timestamp or null",
  "status": "running|completed|failed",
  "duration_seconds": "number or null",
  "tasks": [
    {
      "id": "task_id",
      "agent": "scout|strategist|creator|publisher|marc",
      "status": "completed|failed|skipped",
      "started_at": "ISO timestamp",
      "completed_at": "ISO timestamp",
      "output": "file path or null",
      "dependencies": ["task_id"],
      "notes": "description"
    }
  ],
  "errors": ["error description"],
  "warnings": ["warning description"]
}
```

### Valid Task IDs

Pipeline: `scout_run`, `scout_validation`, `strategist_run`, `strategist_validation`, `cross_validation`, `creator_en_run`, `creator_en_validation`, `creator_en_cross_validation`, `creator_jp_run`, `creator_jp_validation`, `creator_jp_cross_validation`, `war_room`, `telegram_preview`

Publishing: `publisher_en_post`, `publisher_jp_post`, `publisher_en_validation`, `publisher_jp_validation`, `publisher_en_outbound`, `publisher_jp_outbound`, `publisher_rate_limits_validation`, `telegram_publish_report`

Metrics: `analyst_collect`, `analyst_en_summary`, `analyst_jp_summary`, `analyst_en_validation`, `analyst_jp_validation`, `analyst_metrics_validation`, `daily_report`

## Initial Pipeline State Template

```json
{
  "pipeline_date": "YYYY-MM-DD",
  "started_at": "<current JST ISO timestamp>",
  "completed_at": null,
  "status": "running",
  "duration_seconds": null,
  "tasks": [],
  "errors": [],
  "warnings": []
}
```

## Content Preview Format (Step 12)

```
Content Plan -- {YYYY-MM-DD}

EN Account ({N} posts):
  1. [HH:MM UTC] {category} -- {first 50 chars of text}...
  2. [HH:MM UTC] {category} -- {first 50 chars of text}...
  ...

JP Account ({N} posts):
  1. [HH:MM JST] {category} -- {first 50 chars of text}...
  ...

Strategy Highlights:
  - {key_insight_1}
  - {key_insight_2}

Status: Awaiting approval
Use /approve to approve, /details for full view
```

## Publish Report Format (Step P5)

```
Publish Report -- {YYYY-MM-DD}

EN Account:
  Posted: {N} tweets
  Failed: {N}
  Links:
    - {post_url_1}
    - {post_url_2}

JP Account:
  Posted: {N} tweets
  Failed: {N}
  Links:
    - {post_url_1}

Outbound:
  EN: {likes} likes, {replies} replies, {follows} follows
  JP: {likes} likes, {replies} replies, {follows} follows

Rate Limits:
  EN: posts {used}/{limit}, likes {used}/{limit}
  JP: posts {used}/{limit}, likes {used}/{limit}
```

## Follower Anomaly Alert Format (Step P8)

```
Follower Anomaly -- {account}
Change: {followers_change:+d} ({percentage:+.1f}%)
Previous: {yesterday} -> Current: {today}
Please investigate.
```

## Daily Report Format (Step P8)

```
Daily Report -- {YYYY-MM-DD}

Account Growth:
  EN: {followers} followers ({change:+d})
  JP: {followers} followers ({change:+d})

Post Performance ({hours}h after posting):
  EN:
    - {post_id}: {likes} likes {retweets} RTs {replies} replies
    ...
  JP:
    - {post_id}: {likes} likes {retweets} RTs {replies} replies
    ...

Outbound:
  EN: {likes} likes, {replies} replies, {follows} follows
  JP: {likes} likes, {replies} replies, {follows} follows

War Room Score:
  EN: {score}/100 -- {status}
  JP: {score}/100 -- {status}

{warnings_if_any}
```
