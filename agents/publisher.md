# Publisher Agent — X API Posting & Outbound Engagement

## Role

You are the Publisher agent. You post approved content to X (Twitter) and execute outbound engagement (likes, replies, follows). You are implemented as a Python script (`scripts/publisher.py`) — deterministic execution with precise API control.

Publishing runs **separately from the main pipeline**. The pipeline runs overnight (Scout → Strategist → Creator). After human approval via Telegram, Marc invokes Publisher to post and engage.

## CLI Usage

```bash
# Post all approved content for an account
python3 scripts/publisher.py post --account EN
python3 scripts/publisher.py post --account JP

# Post a specific slot only
python3 scripts/publisher.py post --account EN --slot 1

# Run outbound engagement (likes, replies, follows)
python3 scripts/publisher.py outbound --account EN

# Dry-run mode — log actions without making API calls
python3 scripts/publisher.py --dry-run post --account EN
python3 scripts/publisher.py --dry-run outbound --account EN
```

## Post Execution Flow

1. Load content plan (`data/content_plan_{YYYYMMDD}_{account}.json`)
2. Filter posts with `status == "approved"`
3. For each approved post:
   a. Check rate limits (max 5 posts/account/day)
   b. Look for image in `media/pending/{post_id}.{png,jpg,jpeg,webp}`
   c. If image found: upload via v1.1 media endpoint (must be <2MB)
   d. Create tweet via v2 API (text-only if no image)
   e. Update post status to `"posted"` with `tweet_id`, `post_url`, `posted_at`
   f. On failure: set status to `"failed"` with `error`, `failed_at`
   g. Move uploaded image from `media/pending/` to `media/posted/`
4. Save updated content plan and rate limits

## Outbound Engagement Flow

1. Load strategy's `outbound_strategy` for the account
2. Load reply templates from content plan
3. For each `target_account`:
   a. Resolve user ID via read-only API
   b. Fetch 5 recent tweets
   c. Like tweets (within rate limits, 30-120s random delay between ops)
   d. Reply to one tweet using a random reply template
   e. Follow the target account
4. Save rate limits and outbound log

## Rate Limits (per account per day)

| Action | Limit | Source |
|---|---|---|
| Posts | 5 | Publisher internal |
| Likes | 30 | `config/global_rules.md` |
| Replies | 10 | `config/global_rules.md` |
| Follows | 5 | `config/global_rules.md` |

Tracked in `data/rate_limits_{YYYYMMDD}.json`. Publisher checks before each action and stops when limits are reached.

## Output Files

| File | Description |
|---|---|
| `data/content_plan_{YYYYMMDD}_{account}.json` | Updated with posted/failed status |
| `data/rate_limits_{YYYYMMDD}.json` | Rate limit counters for the day |
| `data/outbound_log_{YYYYMMDD}.json` | Log of all outbound actions (likes, replies, follows) |

## Compliance Notes

- Human approval required before any post goes live (enforced by status flow: draft → approved → posted)
- Never starts post text with `@` (X hides it from feeds)
- Images compressed to <2MB before upload
- Random 30-120s delays between outbound operations to avoid patterns
- All actions logged with timestamps for audit
