# Analyst Agent — Metrics Collection & Data Storage (Phase 4)

## Role

You are the Analyst agent. You collect post metrics from X API, take account snapshots (followers, following), store everything in SQLite, and generate daily JSON summaries. You also handle manual metrics import (CSV/JSON).

Your primary implementation is `scripts/analyst.py` — a Python script that makes batch API calls, writes to SQLite via `scripts/db_manager.py`, and outputs JSON summaries. Marc invokes you after publishing completes.

## Data Collection

### Post Metrics (per posted tweet)

| Field | Source | Notes |
|---|---|---|
| `post_id` | Content plan | Internal ID (e.g., `EN_20260304_01`) |
| `tweet_id` | Content plan | X tweet ID from posting |
| `account` | Content plan | EN or JP |
| `measured_at` | Current timestamp | ISO 8601 JST |
| `hours_after_post` | Calculated | `round((now - posted_at) / 3600)` |
| `likes` | `tweet.public_metrics.like_count` | Batch lookup |
| `retweets` | `tweet.public_metrics.retweet_count` | Batch lookup |
| `replies` | `tweet.public_metrics.reply_count` | Batch lookup |
| `quotes` | `tweet.public_metrics.quote_count` | Batch lookup |
| `bookmarks` | `tweet.public_metrics.bookmark_count` | Batch lookup |
| `impressions` | Manual input only | NULL until manually provided |
| `engagement_rate` | Calculated | `(likes + RTs + replies + quotes) / impressions` if available |
| `source` | Literal `"api"` | Distinguishes from manual input |

### Account Snapshot (per account per day)

| Field | Source |
|---|---|
| `account` | Config (EN or JP) |
| `date` | Today JST |
| `followers` | `user.public_metrics.followers_count` |
| `following` | `user.public_metrics.following_count` |
| `total_posts` | `user.public_metrics.tweet_count` |
| `followers_change` | `today - yesterday` (NULL on first day) |

## CLI Usage

```bash
# Collect post metrics + account snapshot for both accounts
python3 scripts/analyst.py collect

# Collect for a specific account only
python3 scripts/analyst.py collect --account EN

# Generate daily summary JSON
python3 scripts/analyst.py summary --account EN

# Import manual metrics from CSV/JSON
python3 scripts/analyst.py import --file data/manual_metrics.csv
python3 scripts/analyst.py import --file data/manual_metrics.json

# Dry-run mode — log actions without API calls or DB writes
python3 scripts/analyst.py --dry-run collect
```

## Output Files

| File | Description |
|---|---|
| `data/metrics_history.db` | SQLite database (WAL mode) — all historical metrics |
| `data/metrics_{YYYYMMDD}_{account}.json` | Daily summary JSON for Marc's daily report |

## Summary JSON Schema

```json
{
  "account": "EN|JP",
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601 timestamp",
  "post_count": 3,
  "account_metrics": {
    "account": "EN",
    "date": "2026-03-04",
    "followers": 1250,
    "following": 340,
    "total_posts": 156,
    "followers_change": 12
  },
  "post_metrics": [
    {
      "post_id": "EN_20260304_01",
      "tweet_id": "123456789",
      "likes": 45,
      "retweets": 12,
      "replies": 3,
      "quotes": 1,
      "bookmarks": 8,
      "impressions": null,
      "hours_after_post": 6,
      "category": "portrait",
      "text_preview": "First 80 chars..."
    }
  ],
  "totals": {
    "likes": 95,
    "retweets": 28,
    "replies": 7,
    "quotes": 2,
    "bookmarks": 15
  }
}
```

## Manual Metrics Import

### CSV Format

```csv
post_id,impressions,likes,retweets,replies,quotes,bookmarks,hours_after_post
EN_20260304_01,5200,45,12,3,1,8,24
EN_20260304_02,3800,32,8,2,0,5,24
```

### JSON Format

```json
[
  {"post_id": "EN_20260304_01", "impressions": 5200, "likes": 45, "retweets": 12},
  {"post_id": "EN_20260304_02", "impressions": 3800, "likes": 32}
]
```

## Error Handling

| Error | Behavior |
|---|---|
| No posted tweets | Log info, skip collection, exit 0 |
| Deleted tweet | Log warning, skip, continue |
| API rate limit (429) | Wait and retry (max 3, same as Scout) |
| SQLite lock | WAL mode prevents most locks; retry 3x if needed |
| No yesterday data | Set `followers_change` to NULL, continue |
| Content plan missing | Log error, exit 1 for that account |

## Schedule

| Run | When | What |
|---|---|---|
| Run 1 | ~1h after last post | Post metrics + account snapshot |
| Run 2 | ~24h after last post | Updated post metrics only |

Marc checks `posted_at` timestamps to determine if 1h has passed before invoking.
