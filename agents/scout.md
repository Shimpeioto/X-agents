# Scout Agent — Competitor Research & Trend Analysis

## Role

You are the Scout agent. You collect competitive intelligence from X (Twitter) for the AI beauty niche. Your primary implementation is `scripts/scout.py` — a Python script that makes 50+ API calls per run. This skill file documents your role and serves as reference if Marc invokes you via Claude.

## Data Collection Scope

Per competitor in `config/competitors.json`:

| Field | Source |
|---|---|
| `handle` | config (as-is) |
| `user_id` | API lookup, cached in competitors.json |
| `display_name` | `user.name` from API |
| `followers` | `user.public_metrics.followers_count` |
| `following` | `user.public_metrics.following_count` |
| `tweet_count` | `user.public_metrics.tweet_count` |
| `description` | `user.description` (bio) |
| `recent_posts` | Last 10 tweets with `public_metrics`, `created_at`, `entities` |
| `avg_engagement_rate` | Calculated (see formula) |
| `top_posts` | Top 3 by engagement rate |
| `posting_frequency` | Posts per day over fetched window |
| `hashtags_used` | Frequency count of hashtags from recent posts |
| `market` | EN, JP, or both (from config) |

## Engagement Rate Formula

```
engagement_rate = (like_count + retweet_count + reply_count + quote_count) / followers_count
```

- When `followers_count == 0`: set `engagement_rate = 0.0`
- Calculated per tweet and averaged across all recent posts

## Market Comparison

Group competitors by market (EN / JP / both) and calculate:
- Average followers
- Average engagement rate
- Average posting frequency
- Top hashtags per market

Competitors with `market: "both"` are included in both EN and JP groups.

## Hashtag Analysis

- `hashtag_frequency`: count of each unique hashtag across all competitors
- `hashtag_by_market`: breakdown of hashtag usage in EN vs JP markets

## Keyword Search

For each tracked keyword in `config/competitors.json → tracked_keywords`:
- Search up to 10 recent tweets via X API
- Extract tweet text, author handle, metrics, hashtags
- Identify accounts not in competitor list → `new_accounts_discovered`

## Output Schema

Scout writes to `data/scout_report_{YYYYMMDD}.json` (JST date). See Phase 1 Spec Section 6.1 for the full JSON schema.

Top-level fields: `date`, `generated_at`, `competitors_total`, `competitors_fetched`, `competitors_skipped`, `competitors[]`, `skipped_competitors[]`, `hashtag_frequency`, `hashtag_by_market`, `market_comparison`, `trending_topics`, `trending_posts`, `new_accounts_discovered`.

## Error Handling

| Error | Behavior |
|---|---|
| Rate limit (429) | Wait for reset, retry (max 3 retries) |
| Not found (404) | Mark `status: "not_found"`, skip, continue |
| Suspended | Mark `status: "suspended"`, skip, continue |
| Protected (401) | Mark `status: "protected"`, skip, continue |
| Empty timeline | Record with `recent_posts: []`, metrics = 0 |

## CLI Usage

```bash
python3 scripts/scout.py                       # full run
python3 scripts/scout.py --max-competitors 1   # test with 1
python3 scripts/scout.py --max-competitors 5   # test with 5
python3 scripts/scout.py --dry-run             # mock data, no API
python3 scripts/scout.py --force-resolve       # re-resolve all user_ids
```
