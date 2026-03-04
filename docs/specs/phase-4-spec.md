# Phase 4 Technical Specification — Analyst + Manual Metrics + War Room Upgrade

**Document version**: 1.0
**Date**: March 4, 2026
**Status**: Draft
**Phase**: 4 of 6 (Days 13-16)
**Parent documents**: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md), [PRD v1.1](./x-ai-beauty-prd-v1.md)

---

## 1. Scope & Timeline

**Phase 4 = Days 13-16** (4 calendar days, following Phase 3 completion).

Phase 4 builds the **measurement layer** — the feedback loop that transforms the pipeline from "post and hope" to "post, measure, and adapt." It adds the Analyst agent (automated metrics collection), manual impression input (3 methods), War Room upgrade (quality scoring), and full 6-agent validation.

### What Phase 4 Builds

| Component | Scope |
|---|---|
| **Analyst** | Python script (`scripts/analyst.py`) — batch tweet metrics collection via X API, account snapshots, SQLite storage + JSON summaries. |
| **Manual Metrics Input** | Three methods: Telegram `/metrics` command, screenshot parsing via Claude Vision API, CSV/JSON file import. |
| **Marc War Room Upgrade** | War Room Lite → Full War Room with quality scoring (0-100), rubric-based evaluation, follower anomaly detection. |
| **Daily Report** | Marc sends a daily Telegram report with real engagement data instead of placeholder text. |
| **Outbound Log Migration** | Publisher dual-writes outbound actions to JSON + SQLite for historical analysis. |
| **Validation Extensions** | New `analyst` and `analyst_metrics` modes in `validate.py`. |

### What Phase 4 Does NOT Build

- Cron scheduling (Phase 5)
- VPS deployment (Phase 5)
- `/edit`, `/strategy`, `/competitors` full Telegram command implementations (Phase 4+)
- Playwright-based impression scraping (removed from spec — compliance risk)
- Automated impression collection of any kind (impressions are manual-only)
- Posting time optimization based on own metrics (Phase 5+)
- Strategy auto-adaptation from own engagement data (Phase 5+)

### Day-by-Day Plan

| Day | Focus | Key Deliverable |
|---|---|---|
| Day 13 | `analyst.py` (collect + summary) + `db_manager.py` upgrades + `x_api.py` batch method + validation | Analyst collects post metrics for both accounts, writes to SQLite + JSON |
| Day 14 | Manual metrics (Telegram `/metrics`, screenshot handler via Claude Vision, CSV/JSON import) | All 3 impression input methods working |
| Day 15 | Marc War Room full scoring, daily report with real data, follower anomaly detection, outbound SQLite migration | War Room scores content plans, daily report includes real engagement numbers |
| Day 16+ | End-to-end testing (2-3 consecutive real pipeline days with all 6 agents) | Full pipeline proven reliable over multiple days |

---

## 2. X API Budget

### 2.1 Analyst API Costs

Analyst uses **batch tweet lookup** (`GET /2/tweets?ids=`) — up to 100 tweet IDs per request.

| Operation | Endpoint | Calls/Run | Notes |
|---|---|---|---|
| Batch tweet metrics | `GET /2/tweets?ids=` | ~2 | Up to 10 tweets per account × 2 accounts = ~20 IDs → 1 request. Conservative: 2 requests (1 per account). |
| Account snapshot | `GET /2/users?ids=` | 1 | Both accounts in one batch request |
| **Total per Analyst run** | | **~3** | |

### 2.2 Analyst Collection Schedule

| Metric | Value |
|---|---|
| Runs per day | 2 (1h and 24h after last post) |
| Daily Analyst reads | ~5 calls/day (2 batch tweet lookups × 2 runs + 1 account snapshot × 1 run) |
| Monthly Analyst reads (30 days) | ~150 calls/month |

**Note**: Account snapshots only need to run once per day (follower counts don't change significantly intraday). The second Analyst run (24h) fetches updated tweet metrics only.

### 2.3 Combined Monthly Projection

| Agent | Monthly Calls | Notes |
|---|---|---|
| Scout | ~1,620 | Phase 1 baseline |
| Publisher | ~600 | Phase 3 (outbound reads for user resolution + timelines) |
| Analyst | ~150 | ~5 calls/day × 30 days (see Section 2.2) |
| **Total** | **~2,370** | **16% of 15,000 Basic plan limit** |

### 2.4 Rate Limits Per Endpoint

| Endpoint | Rate Limit (Basic) | Phase 4 Usage | Status |
|---|---|---|---|
| `GET /2/tweets?ids=` | 300/15 min | ~2/run | Safe |
| `GET /2/users?ids=` | 300/15 min | 1/run | Safe |
| `GET /2/users/by/username/:username` | 300/15 min | unchanged from Phase 3 | Safe |
| `GET /2/users/:id/tweets` | 1,500/15 min | unchanged from Phase 3 | Safe |
| `POST /2/tweets` | 100/15 min (per-user) | unchanged from Phase 3 | Safe |

---

## 3. Agent Definitions (Phase 4 Scope)

### 3.1 Analyst Agent

| Item | Details |
|---|---|
| **Role** | Post metrics collection, account snapshots, historical data storage |
| **Implementation** | Python script (`scripts/analyst.py`) using `scripts/x_api.py` wrapper + `scripts/db_manager.py` |
| **Why Python** | Makes batch API calls, writes to SQLite, calculates deltas — deterministic operations better as a script than Claude reasoning |
| **Input** | Content plans (`data/content_plan_{YYYYMMDD}_{account}.json`) for tweet_ids, `config/accounts.json` for account user_ids |
| **Output** | SQLite rows in `data/metrics_history.db` + JSON summary `data/metrics_{YYYYMMDD}_{account}.json` |
| **Auth** | Bearer token only (read-only, same as Scout) |

**Data collected per posted tweet**:

| Field | Source | Notes |
|---|---|---|
| `post_id` | Content plan | Internal post ID (e.g., `EN_20260304_01`) |
| `tweet_id` | Content plan | X tweet ID from posting |
| `account` | Content plan | EN or JP |
| `measured_at` | Current timestamp | ISO 8601 JST |
| `hours_after_post` | Calculated | `(measured_at - posted_at)` in hours, rounded |
| `likes` | `tweet.public_metrics.like_count` | From batch lookup |
| `retweets` | `tweet.public_metrics.retweet_count` | From batch lookup |
| `replies` | `tweet.public_metrics.reply_count` | From batch lookup |
| `quotes` | `tweet.public_metrics.quote_count` | From batch lookup |
| `bookmarks` | `tweet.public_metrics.bookmark_count` | From batch lookup |
| `impressions` | Manual input only | NULL until manually provided |
| `engagement_rate` | Calculated | `(likes + retweets + replies + quotes) / impressions` if impressions available, else NULL |
| `source` | Literal `"api"` | Distinguishes API data from manual input |

**Data collected per account snapshot**:

| Field | Source | Notes |
|---|---|---|
| `account` | Config | EN or JP |
| `date` | Today JST | Date of snapshot |
| `followers` | `user.public_metrics.followers_count` | Current count |
| `following` | `user.public_metrics.following_count` | Current count |
| `total_posts` | `user.public_metrics.tweet_count` | Lifetime total |
| `followers_change` | Calculated | `today_followers - yesterday_followers` (NULL on first day) |

**CLI interface**:

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

**How `hours_after_post` is calculated**:

1. Read each post's `posted_at` timestamp from the content plan
2. Calculate: `hours = round((now_jst - posted_at_jst).total_seconds() / 3600)`
3. This allows tracking engagement growth over time (1h, 24h, 48h snapshots)

**Batch tweet lookup**:

- Collect all `tweet_id` values from both accounts' content plans
- Call `GET /2/tweets?ids={comma_separated_ids}` with up to 100 IDs per request
- Parse `public_metrics` from each tweet in the response
- Handle deleted tweets (404 in response → mark as `deleted` in DB, skip)

**Error handling**:

| Error | Behavior |
|---|---|
| No posted tweets found | Log info, skip collection, exit 0 (not an error) |
| Deleted tweet (not in batch response) | Log warning, skip that tweet, continue |
| API rate limit (429) | Wait for reset, retry (max 3 retries — same as Scout) |
| SQLite lock | Retry after 1s, max 3 retries. WAL mode prevents most locks. |
| No yesterday data (first day) | Set `followers_change` to NULL, log info, continue |
| Content plan missing | Log error, exit 1 for that account |

### 3.2 Marc Upgrades

#### War Room Lite → Full War Room

Phase 3's War Room Lite performed semantic consistency checks. Phase 4 upgrades to a **scored evaluation** (0-100 points) with a detailed rubric:

| Criterion | Max Points | Scoring Logic |
|---|---|---|
| Category match | 20 | Each post's category matches its strategy slot. Deduct `20 / post_count` per mismatch. |
| Hashtag compliance | 20 | All `always_use` hashtags present in every post. Deduct `20 / (post_count × always_use_count)` per missing tag. |
| Text quality | 20 | No post starts with `@`, all posts under 280 chars (or appropriate for text-only), text feels distinct (not copy-pasted). Deduct 5 per violation. |
| Image prompt variety | 15 | Image prompts are diverse (different subjects, not repetitive). Deduct 5 per pair of near-duplicate prompts. |
| Reply template quality | 15 | 5-10 templates, no duplicates, varied tone. Deduct 3 per issue (duplicate, missing variety, count out of range). |
| A/B test compliance | 10 | At least one post references the active A/B test variant. 0 if no post mentions it. |

**Scoring thresholds**:

| Score | Status | Action |
|---|---|---|
| 90-100 | Excellent | Proceed with confidence |
| 70-89 | Good | Proceed, note areas for improvement in daily report |
| 50-69 | Warning | Log warnings, flag for human review in Telegram |
| 0-49 | Poor | Log errors, send alert to Telegram, recommend re-running Creator |

#### Analyst Invocation Steps

Marc adds the following steps **after publishing** (Steps P6-P8, extending the Phase 3 publishing sequence):

**Step P6: Run Analyst Collect**

```bash
python3 scripts/analyst.py collect
```

- Expected: Metrics written to SQLite, no JSON output for collect
- If Analyst exits non-zero: log as warning, continue (metrics collection failure is not critical)
- Record task: `{"id": "analyst_collect", "agent": "analyst", ...}`

**Step P7: Generate Summaries + Validate**

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

**Step P8: Follower Anomaly Check + Daily Report**

Marc reads both summaries and the War Room scores (from Step 11's `war_room` task in pipeline state `notes` field) to compose the daily report.

#### Daily Report Format

```
📊 Daily Report — {YYYY-MM-DD}

📈 Account Growth:
  🇺🇸 EN: {followers} followers ({change:+d})
  🇯🇵 JP: {followers} followers ({change:+d})

🐦 Post Performance ({hours}h after posting):
  🇺🇸 EN:
    • {post_id}: {likes}❤️ {retweets}🔁 {replies}💬 {quotes}🔄
    ...
  🇯🇵 JP:
    • {post_id}: {likes}❤️ {retweets}🔁 {replies}💬 {quotes}🔄
    ...

📊 Aggregates:
  EN: avg {avg_engagement}% engagement, total {total_likes} likes
  JP: avg {avg_engagement}% engagement, total {total_likes} likes

📤 Outbound:
  EN: {likes} likes, {replies} replies, {follows} follows
  JP: {likes} likes, {replies} replies, {follows} follows

🏆 War Room Score:
  EN: {score}/100 — {status}
  JP: {score}/100 — {status}

{warnings_if_any}
```

#### Follower Anomaly Detection

Marc checks for abnormal follower changes after the Analyst collects account metrics:

1. Read today's `followers` and `followers_change` from `data/metrics_{YYYYMMDD}_{account}.json`
2. If `abs(followers_change) > followers * 0.10` (>10% change): send alert to Telegram
3. If this is the first day (no yesterday data): skip anomaly check

**Alert format**:

```
⚠️ Follower Anomaly — {account}
Change: {followers_change:+d} ({percentage:+.1f}%)
Previous: {yesterday_followers} → Current: {today_followers}
Please investigate.
```

### 3.3 Publisher Modification — Outbound Log SQLite Migration

Publisher currently writes outbound actions to `data/outbound_log_{YYYYMMDD}.json` only. Phase 4 adds **dual-write** — the same actions are written to both JSON (for human readability / backward compat) and SQLite (for historical queries).

**Changes to `scripts/publisher.py`**:

1. After each outbound action (like, reply, follow), call `db_manager.insert_outbound_log()`
2. Continue writing to JSON as before (no change to JSON format)
3. If SQLite write fails: log warning, continue (JSON is the primary log)

**SQLite schema addition** — add `timestamp` column to `outbound_log` table:

```sql
ALTER TABLE outbound_log ADD COLUMN timestamp DATETIME;
```

This is handled by `db_manager.py` migration logic (see Section 5.2).

---

## 4. Implementation Architecture

### 4.1 Why Python Script for Analyst

| Consideration | Decision |
|---|---|
| **API calls** | Batch tweet lookup — deterministic HTTP call, not reasoning |
| **SQLite writes** | Structured inserts — Python excels at this |
| **Calculations** | Engagement rate, follower delta — arithmetic, not judgment |
| **Consistency** | Same pattern as Scout and Publisher — all API-calling agents are Python scripts |

### 4.2 Execution Model — Post-Publish Flow

```
Publishing Sequence (Phase 3):
  P1: Check approval → P2: Post → P3: Validate → P4: Outbound → P5: Telegram report

New Phase 4 steps (after P5):
  P6: Analyst collect → P7: Generate summaries + Validate → P8: Anomaly check + Daily report
```

**Note**: Analyst `collect` should run at least 1 hour after the last post to capture initial engagement. Marc checks this by comparing `now` to the latest `posted_at` timestamp across **both** accounts. If < 1 hour has passed since the latest post on either account, Marc logs a warning and skips the Analyst step (it can be re-run manually or in the next cycle). This means if EN posted at 09:00 and JP posted at 18:00, running collect at 10:00 would skip (JP is too recent). To handle this, Marc can alternatively run `collect --account EN` for the account that's ready and defer JP to a later manual run. The default behavior (collect without `--account`) collects both at once for simplicity.

### 4.3 Dependency Chain

```
content_plan_{date}_{account}.json (posted tweets with tweet_ids)
        │
        ▼
  analyst.py collect ──▶ data/metrics_history.db (SQLite)
        │
        ▼
  analyst.py summary ──▶ data/metrics_{date}_{account}.json
        │
        ▼
  Marc daily report (reads summaries + War Room scores)
        │
        ▼
  Telegram daily report message
```

### 4.4 Manual Metrics Flow (3 Methods)

```
Method 1: Telegram /metrics command
  User sends: /metrics EN_20260304_01 impressions=5000
  Bot: Parses → writes to SQLite via db_manager → confirms

Method 2: Screenshot via Telegram
  User sends: photo of X Analytics screenshot
  Bot: Downloads image → sends to Claude Vision API → extracts metrics
     → shows parsed data → user confirms with /confirm
     → writes to SQLite via db_manager

Method 3: CSV/JSON file import
  User runs: python3 scripts/analyst.py import --file data/manual_metrics.csv
  Script: Parses file → validates → writes to SQLite via db_manager → reports results
```

### 4.5 War Room Scoring Rubric

Marc performs the scoring in Step 11 (War Room) after reading both content plans and the strategy.

**Scoring is per account** — EN and JP each get their own score.

| # | Criterion | Max | How Marc Scores It |
|---|---|---|---|
| 1 | Category match | 20 | For each post, check `post.category` against `strategy.posting_schedule[slot].category` (case-insensitive). Full marks if all match. Deduct proportionally per mismatch. |
| 2 | Hashtag compliance | 20 | For each post, check that all `always_use` hashtags from strategy are in `post.hashtags` (case-insensitive). Deduct proportionally per missing tag per post. |
| 3 | Text quality | 20 | Check: no post text starts with `@` (deduct 5), all posts ≤ 280 chars or text-only justified (deduct 3), texts are distinct/not repetitive (deduct 5 if >50% similarity). |
| 4 | Image prompt variety | 15 | Read all image prompts. If any two prompts describe essentially the same image (same subject + same style), deduct 5 per duplicate pair. Marc uses judgment. |
| 5 | Reply template quality | 15 | Check: 5-10 templates (deduct 5 if out of range), no exact duplicates (deduct 3), varied tone (deduct 3 if all templates feel identical). |
| 6 | A/B test compliance | 10 | Check if at least one post has `ab_test_variant` set and it matches the strategy's `ab_test.variable`. Full marks if yes, 0 if not. |

---

## 5. File Specifications

### 5.1 `scripts/analyst.py` — Analyst Agent Script

**Purpose**: Collect engagement metrics for posted tweets, account snapshots, and generate daily summaries. All data stored in SQLite with JSON summaries for human consumption.

**Class design**:

```python
class Analyst:
    """Metrics collection agent."""

    def __init__(self, dry_run: bool = False):
        """Initialize X API client + DB connection."""
        self.dry_run = dry_run
        self.api = XApiClient(load_bearer_token())
        self.db_path = DB_PATH

    def collect_post_metrics(self, account: str) -> list[dict]:
        """Collect metrics for all posted tweets of an account.

        1. Load content_plan_{date}_{account}.json
        2. Filter posts with status == "posted" and tweet_id present
        3. Batch-fetch tweet metrics via get_tweets_batch()
        4. Calculate hours_after_post from posted_at
        5. Write each row to SQLite via db_manager.insert_post_metrics()
        6. Return list of collected metrics dicts

        Returns:
            List of {"post_id", "tweet_id", "likes", "retweets",
                     "replies", "quotes", "bookmarks", "hours_after_post"}
        """

    def collect_account_metrics(self, account: str) -> dict:
        """Collect account snapshot (followers, following, total_posts).

        1. Load account user_id from config/accounts.json
        2. Fetch user info via get_user_info_batch([user_id])
        3. Query yesterday's followers from SQLite
        4. Calculate followers_change
        5. Write to SQLite via db_manager.insert_account_metrics()
        6. Return snapshot dict

        Returns:
            {"account", "date", "followers", "following",
             "total_posts", "followers_change"}
        """

    def generate_summary(self, account: str) -> dict:
        """Generate daily summary JSON from SQLite data.

        1. Query today's post metrics from SQLite
        2. Query today's account snapshot
        3. Query today's outbound log
        4. Calculate aggregates (avg engagement, totals)
        5. Write to data/metrics_{date}_{account}.json
        6. Return summary dict

        Returns:
            Full summary dict matching schema in Section 6.1
        """

    def import_manual_metrics(self, file_path: str) -> int:
        """Import manual metrics from CSV or JSON file.

        1. Detect format from file extension (.csv or .json)
        2. Parse and validate each row
        3. Write to SQLite with source="manual"
        4. Return count of imported rows

        Returns:
            Number of rows successfully imported
        """

    def run_collect(self, account: str | None = None) -> int:
        """Full collection run. Returns exit code (0=success, 1=error)."""

    def run_summary(self, account: str) -> int:
        """Generate summary for an account. Returns exit code."""

    def run_import(self, file_path: str) -> int:
        """Import manual metrics. Returns exit code."""
```

**CLI interface**:

```python
def main():
    parser = argparse.ArgumentParser(description="Analyst agent — metrics collection")
    parser.add_argument("--dry-run", action="store_true")

    subparsers = parser.add_subparsers(dest="command")

    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--account", choices=["EN", "JP"], default=None)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--account", required=True, choices=["EN", "JP"])

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--file", required=True)

    args = parser.parse_args()
    # ... dispatch to Analyst methods
```

### 5.2 `scripts/db_manager.py` — Upgrades

**Current state**: `db_manager.py` has `init()` that creates 4 tables: `post_metrics`, `account_metrics`, `outbound_log`, `error_log`. No insert/query functions exist — just the schema.

**Phase 4 additions**:

```python
# --- Enable WAL mode for concurrent reads ---

def init():
    """Initialize database with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    # ... existing CREATE TABLE statements ...

    # Migration: add timestamp column to outbound_log if missing
    c.execute("PRAGMA table_info(outbound_log)")
    columns = [col[1] for col in c.fetchall()]
    if "timestamp" not in columns:
        c.execute("ALTER TABLE outbound_log ADD COLUMN timestamp DATETIME")

    conn.commit()
    conn.close()


# --- Insert functions ---

def insert_post_metrics(post_id: str, tweet_id: str, account: str,
                        measured_at: str, hours_after_post: int,
                        likes: int, retweets: int, replies: int,
                        quotes: int, bookmarks: int,
                        impressions: int | None, engagement_rate: float | None,
                        source: str) -> None:
    """Insert a post metrics row. Uses INSERT OR REPLACE for idempotency."""

def insert_account_metrics(account: str, date: str,
                           followers: int, following: int,
                           total_posts: int,
                           followers_change: int | None) -> None:
    """Insert an account metrics snapshot. Uses INSERT OR REPLACE for idempotency."""

def insert_outbound_log(date: str, account: str, action_type: str,
                        target_handle: str | None, target_tweet_id: str | None,
                        success: bool, api_response_code: int | None,
                        timestamp: str | None = None) -> None:
    """Insert an outbound action log entry."""

def insert_error_log(timestamp: str, agent: str, error_type: str,
                     error_message: str | None, resolution: str | None,
                     resolved: bool = False) -> None:
    """Insert an error log entry."""


# --- Query functions ---

def get_yesterday_followers(account: str) -> int | None:
    """Get yesterday's follower count for an account.

    Returns:
        Follower count or None if no data exists.
    """

def get_post_metrics(post_id: str, measured_at: str | None = None) -> list[dict]:
    """Get all metrics snapshots for a post_id.

    Args:
        post_id: Internal post ID (e.g., "EN_20260304_01")
        measured_at: Optional — filter to a specific measurement time

    Returns:
        List of metric dicts ordered by measured_at.
    """

def get_account_metrics_range(account: str, start_date: str,
                              end_date: str) -> list[dict]:
    """Get account metrics for a date range.

    Returns:
        List of {"account", "date", "followers", "following",
                 "total_posts", "followers_change"} dicts.
    """

def get_daily_summary(account: str, date: str) -> dict:
    """Get aggregated metrics for a single day.

    Returns:
        {"posts_measured": int, "total_likes": int, "total_retweets": int,
         "total_replies": int, "avg_engagement_rate": float | None,
         "followers": int, "followers_change": int | None}
    """

def get_outbound_log(account: str, date: str) -> list[dict]:
    """Get outbound actions for an account on a given date.

    Returns:
        List of {"action_type", "target_handle", "target_tweet_id",
                 "success", "timestamp"} dicts.
    """
```

**Migration handling**: The `init()` function is idempotent — safe to call on every startup. It uses `CREATE TABLE IF NOT EXISTS` (already present) and adds the new `timestamp` column to `outbound_log` only if missing (via `PRAGMA table_info` check). WAL mode is enabled once and persists.

### 5.3 `scripts/x_api.py` — New Batch Method

**Addition to `XApiClient`**:

```python
def get_tweets_batch(self, tweet_ids: list[str]) -> list[dict]:
    """Batch lookup of tweets by ID (up to 100 per request).

    Uses GET /2/tweets?ids= endpoint.

    Args:
        tweet_ids: List of tweet ID strings (max 100)

    Returns:
        List of tweet dicts with text, public_metrics, created_at.
        Deleted/not-found tweets are omitted from the result.
    """
    results = []
    for i in range(0, len(tweet_ids), 100):
        batch = tweet_ids[i : i + 100]
        response = self._api_call_with_retry(
            self.client.get_tweets,
            ids=batch,
            tweet_fields=TWEET_FIELDS,
        )
        if response and response.data:
            for tweet in response.data:
                normalized = self._normalize_tweet(tweet)
                if normalized:
                    results.append(normalized)
    return results
```

**Notes**:
- Uses existing `_api_call_with_retry` for error handling
- Uses existing `_normalize_tweet` for response normalization
- `tweepy.Client.get_tweets()` maps to `GET /2/tweets`
- Deleted tweets appear as `None` in `response.data` — the `if normalized` check handles this

### 5.4 `scripts/telegram_bot.py` — Extensions

**New commands and handlers**:

#### `_show_metrics_summary` Helper

```python
async def _show_metrics_summary(update: Update, account: str | None = None) -> None:
    """Display today's metrics summary from SQLite.

    Args:
        update: Telegram update to reply to
        account: Optional — "EN" or "JP". If None, show both accounts.

    Reads from db_manager:
    1. get_daily_summary(account, today) for post counts, total likes, etc.
    2. get_account_metrics_range(account, today, today) for follower snapshot

    Reply format:
        📊 Metrics — 2026-03-04
        🇺🇸 EN: 3 posts measured
          Total: 77❤️ 13🔁 5💬
          Followers: 1250 (+12)
        🇯🇵 JP: 2 posts measured
          Total: 55❤️ 8🔁 3💬
          Followers: 890 (+5)

    If no data exists for today, reply: "No metrics collected yet for {date}."
    """
    from db_manager import get_daily_summary, get_account_metrics_range
    date = today_str()
    accounts = [account] if account else ["EN", "JP"]
    lines = [f"📊 Metrics — {today_iso()}\n"]
    has_data = False

    for acct in accounts:
        summary = get_daily_summary(acct, f"{date[:4]}-{date[4:6]}-{date[6:8]}")
        if not summary or summary.get("posts_measured", 0) == 0:
            lines.append(f"  {acct}: No data yet")
            continue
        has_data = True
        lines.append(
            f"  {acct}: {summary['posts_measured']} posts measured\n"
            f"    Total: {summary['total_likes']}❤️ "
            f"{summary['total_retweets']}🔁 {summary['total_replies']}💬\n"
            f"    Followers: {summary.get('followers', '?')} "
            f"({summary.get('followers_change', '?'):+d})"
        )

    if not has_data:
        await update.message.reply_text(f"No metrics collected yet for {today_iso()}.")
    else:
        await update.message.reply_text("\n".join(lines))
```

#### `/metrics` Command (View + Input Modes)

```python
async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /metrics command.

    Usage:
        /metrics              — View today's metrics summary
        /metrics EN           — View EN account metrics
        /metrics EN_20260304_01 impressions=5000  — Input manual metrics
        /metrics EN_20260304_01 impressions=5000 likes=120  — Input multiple
    """
    if not is_authorized(update):
        return

    args = context.args or []

    if len(args) == 0:
        # View mode: show today's summary for both accounts
        await _show_metrics_summary(update)
        return

    if len(args) == 1 and args[0].upper() in ("EN", "JP"):
        # View mode: show specific account
        await _show_metrics_summary(update, account=args[0].upper())
        return

    # Input mode: parse post_id and key=value pairs
    post_id = args[0]
    metrics = {}
    for arg in args[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            try:
                metrics[key] = int(value)
            except ValueError:
                await update.message.reply_text(f"Invalid value for {key}: {value}")
                return

    if not metrics:
        await update.message.reply_text(
            "Usage: /metrics POST_ID key=value [key=value ...]\n"
            "Example: /metrics EN_20260304_01 impressions=5000"
        )
        return

    # Resolve tweet_id and existing metrics from content plan
    import re
    id_match = re.match(r"^(EN|JP)_(\d{8})_\d{2}$", post_id)
    if not id_match:
        await update.message.reply_text(
            f"Invalid post_id format: {post_id}\n"
            "Expected: EN_YYYYMMDD_SS or JP_YYYYMMDD_SS"
        )
        return

    acct, date_str = id_match.group(1), id_match.group(2)
    plan_path = os.path.join(DATA_DIR, f"content_plan_{date_str}_{acct}.json")
    plan = load_json(plan_path)
    if not plan:
        await update.message.reply_text(f"Content plan not found: {plan_path}")
        return

    # Find the post to get tweet_id and posted_at
    post = next((p for p in plan.get("posts", []) if p.get("id") == post_id), None)
    if not post or not post.get("tweet_id"):
        await update.message.reply_text(f"Post {post_id} not found or not yet posted.")
        return

    tweet_id = post["tweet_id"]
    posted_at = post.get("posted_at")

    # Calculate hours_after_post (0 if posted_at unavailable)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    hours = 0
    if posted_at:
        try:
            post_time = datetime.fromisoformat(posted_at)
            now = datetime.now(ZoneInfo("Asia/Tokyo"))
            hours = round((now - post_time).total_seconds() / 3600)
        except (ValueError, TypeError):
            pass

    # For fields not provided by the user, query existing row or default to 0
    from db_manager import get_post_metrics, insert_post_metrics
    existing = get_post_metrics(post_id)
    latest = existing[-1] if existing else {}

    insert_post_metrics(
        post_id=post_id, tweet_id=tweet_id, account=acct,
        measured_at=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        hours_after_post=hours,
        likes=metrics.get("likes", latest.get("likes", 0)),
        retweets=metrics.get("retweets", latest.get("retweets", 0)),
        replies=metrics.get("replies", latest.get("replies", 0)),
        quotes=metrics.get("quotes", latest.get("quotes", 0)),
        bookmarks=metrics.get("bookmarks", latest.get("bookmarks", 0)),
        impressions=metrics.get("impressions", latest.get("impressions")),
        engagement_rate=None,  # recalculated by Analyst summary
        source="manual_telegram",
    )

    await update.message.reply_text(f"Saved metrics for {post_id}: {metrics}")
```

#### Photo Handler for Screenshot Parsing

```python
from telegram.ext import MessageHandler, filters

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle screenshot photos sent to the bot.

    1. Download the highest-resolution photo
    2. Send to Anthropic Claude Vision API for metric extraction
    3. Display parsed metrics and ask for confirmation
    4. Store pending confirmation in context.user_data
    """
    if not is_authorized(update):
        return

    photo = update.message.photo[-1]  # highest resolution
    file = await context.bot.get_file(photo.file_id)
    # Download to temp file
    file_path = f"/tmp/screenshot_{photo.file_id}.jpg"
    await file.download_to_drive(file_path)

    # Send to Claude Vision API
    import anthropic
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

    import base64
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                    "media_type": "image/jpeg", "data": image_data}},
                {"type": "text", "text": (
                    "Extract tweet metrics from this X Analytics screenshot. "
                    "Return JSON with fields: post_id (if visible), impressions, "
                    "likes, retweets, replies, quotes, bookmarks. "
                    "If a field is not visible, omit it. "
                    "Return ONLY valid JSON, no commentary."
                )}
            ]
        }]
    )

    # Parse Vision response
    try:
        metrics = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        await update.message.reply_text(
            "Could not parse screenshot. Please try a clearer image or use /metrics command."
        )
        return

    # Store in pending confirmation
    context.user_data["pending_screenshot_metrics"] = metrics

    # Show parsed data
    lines = ["📸 Parsed from screenshot:"]
    for key, val in metrics.items():
        lines.append(f"  {key}: {val}")
    lines.append("\nUse /confirm to save, or /cancel to discard.")

    await update.message.reply_text("\n".join(lines))


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm and save screenshot-parsed metrics."""
    if not is_authorized(update):
        return

    pending = context.user_data.get("pending_screenshot_metrics")
    if not pending:
        await update.message.reply_text("Nothing to confirm.")
        return

    # Write to SQLite with source="manual_screenshot"
    from db_manager import insert_post_metrics
    # ... write metrics
    del context.user_data["pending_screenshot_metrics"]
    await update.message.reply_text("Metrics saved from screenshot.")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel pending screenshot metrics."""
    if not is_authorized(update):
        return

    if "pending_screenshot_metrics" in context.user_data:
        del context.user_data["pending_screenshot_metrics"]
        await update.message.reply_text("Screenshot metrics discarded.")
    else:
        await update.message.reply_text("Nothing to cancel.")
```

**Registration in `main()`**:

```python
app.add_handler(CommandHandler("metrics", cmd_metrics))
app.add_handler(CommandHandler("confirm", cmd_confirm))
app.add_handler(CommandHandler("cancel", cmd_cancel))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# Remove /metrics from stub handlers list
for cmd in ["edit", "strategy", "competitors"]:  # removed "metrics"
    app.add_handler(CommandHandler(cmd, cmd_stub))
```

### 5.5 `scripts/validate.py` — New Validation Modes

**New mode: `analyst`** — Validates Analyst summary JSON output.

```python
def validate_analyst(summary_path: str) -> tuple[bool, list[str]]:
    """Validate Analyst summary JSON. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is valid JSON
    # Check 2: Required top-level fields: date, account, generated_at,
    #           posts_measured, account_snapshot, daily_aggregate
    # Check 3: account is EN or JP
    # Check 4: posts_measured is a list
    # Check 5: Each post in posts_measured has: post_id, tweet_id, likes,
    #           retweets, replies, quotes, hours_after_post
    # Check 6: account_snapshot has: followers, following, total_posts
    # Check 7: daily_aggregate has: total_likes, total_retweets,
    #           total_replies, avg_engagement_rate (can be null)
    # Check 8: All numeric values are non-negative

    passed = len(issues) == 0
    return passed, issues
```

**New mode: `analyst_metrics`** — Validates SQLite integrity.

```python
def validate_analyst_metrics(db_path: str) -> tuple[bool, list[str]]:
    """Validate Analyst SQLite data integrity. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: Database file exists and is valid SQLite
    # Check 2: Required tables exist: post_metrics, account_metrics,
    #           outbound_log, error_log
    # Check 3: post_metrics has at least 1 row for today
    # Check 4: account_metrics has entries for both EN and JP for today
    # Check 5: No negative values in numeric columns
    # Check 6: No orphan post_ids (post_id in metrics but not in
    #           any content plan — warning only)

    passed = len(issues) == 0
    return passed, issues
```

**CLI addition to `main()`**:

```python
elif mode == "analyst":
    passed, issues = validate_analyst(sys.argv[2])

elif mode == "analyst_metrics":
    passed, issues = validate_analyst_metrics(sys.argv[2])
```

**Updated usage line**:

```
Usage: python3 scripts/validate.py {scout|strategist|cross|creator|creator_cross|publisher|publisher_rate_limits|analyst|analyst_metrics} <file1> [<file2>]
```

### 5.6 `agents/marc.md` — Updates

The following sections are **added or modified** in Marc's skill file:

#### Step 11 Replacement: War Room Lite → Full War Room

Replace the existing Step 11 content with:

```markdown
### Step 11: War Room (Full Scoring)

Apply scored evaluation to both content plans (EN and JP separately):

1. Read the strategy and both content plans
2. For EACH account, score against the rubric (see Scoring Rubric):

   | Criterion | Max | Check |
   |---|---|---|
   | Category match | 20 | post.category vs strategy.posting_schedule[slot].category |
   | Hashtag compliance | 20 | all always_use tags in every post.hashtags |
   | Text quality | 20 | no @-prefix, length appropriate, texts distinct |
   | Image prompt variety | 15 | prompts describe different subjects/styles |
   | Reply template quality | 15 | 5-10 templates, no dupes, varied tone |
   | A/B test compliance | 10 | at least 1 post references ab_test variant |

3. Calculate total score per account (0-100)
4. Apply thresholds:
   - ≥ 70: proceed normally, log score
   - 50-69: log warnings, flag for human review
   - < 50: log error, send Telegram alert, recommend re-running Creator
5. Record task: {"id": "war_room", "agent": "marc", "notes": "EN: {score}/100 ({status}), JP: {score}/100 ({status})", ...}
   The notes field persists scores so Step P8 (daily report) can read them later.
6. Add any threshold violations to pipeline state warnings/errors
```

#### New Steps P6-P8: Analyst Invocation

Add after Step P5 (Telegram publish report):

```markdown
### Step P6: Run Analyst Collect (1h+ after posting)

Check that at least 1 hour has passed since the latest posted_at timestamp.
If not, log: "Analyst skipped — posts are < 1h old" and skip to P8.

python3 scripts/analyst.py collect

- If Analyst exits non-zero: log as warning, continue
- Record task: {"id": "analyst_collect", "agent": "analyst", ...}

### Step P7: Generate Summaries + Validate

python3 scripts/analyst.py summary --account EN
python3 scripts/analyst.py summary --account JP

python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_EN.json
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_JP.json
python3 scripts/validate.py analyst_metrics data/metrics_history.db

- If any validation fails: log as warning
- Record tasks: analyst_en_summary, analyst_jp_summary,
  analyst_en_validation, analyst_jp_validation, analyst_metrics_validation

### Step P8: Follower Anomaly Check + Daily Report

1. Read metrics summaries for both accounts
2. Read War Room scores from Step 11's war_room task notes in pipeline state
3. Check follower anomaly: if abs(followers_change) > followers × 0.10
   → send Telegram alert (see alert format in Section 3.2)
4. Send daily report to Telegram (see format in Section 3.2)
   Include War Room scores from pipeline state.
5. Record task: {"id": "daily_report", "agent": "marc", ...}
```

#### Pipeline State Additions

New task IDs for Phase 4:

```
analyst_collect, analyst_en_summary, analyst_jp_summary,
analyst_en_validation, analyst_jp_validation, analyst_metrics_validation,
war_room (replaces war_room_lite), daily_report
```

### 5.7 `agents/analyst.md` — Full Skill File

Replace the placeholder content with:

```markdown
# Analyst Agent — Metrics Collection & Summary

## Role

You are the Analyst agent. You collect engagement metrics for posted tweets,
take account snapshots, and generate daily summary reports. Your primary
implementation is `scripts/analyst.py` — a Python script that makes batch
API calls and writes to SQLite.

## Data Collection

### Post Metrics
- Source: X API v2 batch tweet lookup (GET /2/tweets?ids=)
- Collected fields: likes, retweets, replies, quotes, bookmarks
- Impressions: manual input only (API does not provide for Basic plan)
- Stored in: SQLite post_metrics table + JSON summary

### Account Snapshots
- Source: X API v2 user lookup (GET /2/users?ids=)
- Collected fields: followers, following, total_posts, followers_change
- Stored in: SQLite account_metrics table + JSON summary

## Collection Schedule
- Run after publishing (1h+ after last post for initial engagement)
- Run again at 24h for mature metrics
- Manual trigger: python3 scripts/analyst.py collect

## Manual Metrics Input
Three methods for adding impressions and corrections:
1. Telegram /metrics command: /metrics POST_ID impressions=5000
2. Screenshot: send analytics screenshot to Telegram bot
3. File import: python3 scripts/analyst.py import --file data/manual.csv

## CLI Usage
python3 scripts/analyst.py collect                    # Collect all
python3 scripts/analyst.py collect --account EN       # Collect EN only
python3 scripts/analyst.py summary --account EN       # Generate summary
python3 scripts/analyst.py import --file data/m.csv   # Import manual
python3 scripts/analyst.py --dry-run collect           # No API/DB writes

## Output Files
- data/metrics_{YYYYMMDD}_{account}.json — Daily summary
- data/metrics_history.db — SQLite historical database

## Error Handling
| Error | Behavior |
|---|---|
| No posted tweets | Skip collection, exit 0 |
| Deleted tweet | Log warning, skip, continue |
| Rate limit (429) | Wait + retry (max 3) |
| SQLite lock | Retry after 1s (max 3) |
| No yesterday data | followers_change = NULL |
```

---

## 6. Output Schemas

### 6.1 `data/metrics_{YYYYMMDD}_{account}.json` — Daily Summary

```json
{
  "date": "2026-03-04",
  "account": "EN",
  "generated_at": "2026-03-04T23:00:00+09:00",
  "posts_measured": [
    {
      "post_id": "EN_20260304_01",
      "tweet_id": "1897234567890123456",
      "category": "portrait",
      "posted_at": "2026-03-04T09:00:00+09:00",
      "hours_after_post": 14,
      "likes": 45,
      "retweets": 8,
      "replies": 3,
      "quotes": 1,
      "bookmarks": 12,
      "impressions": null,
      "engagement_rate": null,
      "source": "api"
    },
    {
      "post_id": "EN_20260304_02",
      "tweet_id": "1897234567890123789",
      "category": "fashion",
      "posted_at": "2026-03-04T14:00:00+09:00",
      "hours_after_post": 9,
      "likes": 32,
      "retweets": 5,
      "replies": 2,
      "quotes": 0,
      "bookmarks": 7,
      "impressions": 5000,
      "engagement_rate": 0.0078,
      "source": "manual_telegram"
    }
  ],
  "account_snapshot": {
    "followers": 1250,
    "following": 340,
    "total_posts": 156,
    "followers_change": 12
  },
  "daily_aggregate": {
    "total_likes": 77,
    "total_retweets": 13,
    "total_replies": 5,
    "total_quotes": 1,
    "total_bookmarks": 19,
    "avg_engagement_rate": null,
    "posts_with_impressions": 1,
    "posts_without_impressions": 1
  },
  "outbound_summary": {
    "likes": 15,
    "replies": 3,
    "follows": 2,
    "total_actions": 20
  }
}
```

### 6.2 Manual Metrics — CSV Format

```csv
post_id,impressions,likes,retweets,replies,quotes,bookmarks
EN_20260304_01,5200,45,8,3,1,12
EN_20260304_02,3800,32,5,2,0,7
JP_20260304_01,4100,38,6,4,2,9
```

**Rules**:
- Header row required
- `post_id` is required; all other columns are optional
- Empty values are treated as "no update" (existing value preserved)
- Duplicate `post_id` rows: last value wins
- Imported with `source: "manual_csv"`

### 6.3 Manual Metrics — JSON Format

```json
[
  {
    "post_id": "EN_20260304_01",
    "impressions": 5200,
    "likes": 45,
    "retweets": 8,
    "replies": 3,
    "quotes": 1,
    "bookmarks": 12
  },
  {
    "post_id": "JP_20260304_01",
    "impressions": 4100
  }
]
```

**Rules**:
- Array of objects
- `post_id` is required per object; all other fields optional
- Imported with `source: "manual_json"`

### 6.4 Pipeline State Additions

New task IDs added to the `tasks` array in `data/pipeline_state_{YYYYMMDD}.json`:

| Task ID | Agent | Dependencies | Notes |
|---|---|---|---|
| `analyst_collect` | analyst | publisher_en_post, publisher_jp_post | Runs after posting |
| `analyst_en_summary` | analyst | analyst_collect | Summary generation |
| `analyst_jp_summary` | analyst | analyst_collect | Summary generation |
| `analyst_en_validation` | marc | analyst_en_summary | Validates EN summary JSON |
| `analyst_jp_validation` | marc | analyst_jp_summary | Validates JP summary JSON |
| `analyst_metrics_validation` | marc | analyst_collect | Validates SQLite integrity |
| `war_room` | marc | creator_en_validation, creator_jp_validation | Replaces war_room_lite |
| `daily_report` | marc | analyst_en_validation, analyst_jp_validation | Telegram daily report |

---

## 7. Authentication

### 7.1 Analyst — Bearer Token

Analyst uses the same bearer token as Scout. No additional API credentials required.

```python
from x_api import load_bearer_token
bearer = load_bearer_token()  # reads from config/accounts.json
api = XApiClient(bearer)
```

### 7.2 Telegram Screenshot Handler — Anthropic API Key

The screenshot handler requires an Anthropic API key for Claude Vision.

**Resolution order**:
1. `ANTHROPIC_API_KEY` environment variable (preferred — same as Claude Code uses)
2. `config/accounts.json` → `anthropic.api_key` field (fallback)

```python
import os
import anthropic

# Method 1: env var (anthropic SDK reads this automatically)
# Just construct: client = anthropic.Anthropic()

# Method 2: explicit from config (fallback)
def get_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    config_path = os.path.join(PROJECT, "config/accounts.json")
    with open(config_path) as f:
        config = json.load(f)
    return config.get("anthropic", {}).get("api_key", "")
```

**Model choice**: Use `claude-haiku-4-5-20251001` for screenshot parsing — fast, cheap, good enough for structured data extraction from images.

### 7.3 Account User IDs for Snapshot

Analyst needs the X user IDs for our own accounts (not competitors). These are stored in `config/accounts.json`:

```json
{
  "x_api": {
    "accounts": {
      "EN": { "user_id": "...", "handle": "..." },
      "JP": { "user_id": "...", "handle": "..." }
    }
  }
}
```

If `user_id` is not present, Analyst resolves it via `XApiClient.resolve_user_id(handle)` and logs a warning suggesting the operator add it to config.

---

## 8. Testing Strategy

21 tests in progression — each builds on the previous:

### Day 13: Analyst Core (Tests 1-8)

| # | Test | Command | Pass Criteria |
|---|---|---|---|
| 1 | X API batch tweet lookup | `python3 -c "from scripts.x_api import XApiClient, load_bearer_token; c = XApiClient(load_bearer_token()); print(c.get_tweets_batch(['TWEET_ID']))"` | Returns list with tweet data including public_metrics |
| 2 | db_manager insert/query functions | `python3 -c "from scripts.db_manager import *; init(); insert_post_metrics('test_01', '123', 'EN', '2026-03-04T10:00:00+09:00', 1, 10, 2, 1, 0, 3, None, None, 'test'); print(get_post_metrics('test_01'))"` | Row inserted and queried successfully |
| 3 | Analyst collect (single account) | `python3 scripts/analyst.py collect --account EN` | Exit 0, rows in SQLite for today's posted tweets |
| 4 | Analyst collect (dry-run) | `python3 scripts/analyst.py --dry-run collect` | Exit 0, no API calls, no DB writes, log messages shown |
| 5 | Analyst collect (24h window) | Run collect again 24h after first collection | New rows with higher `hours_after_post`, existing rows preserved |
| 6 | Analyst summary generation | `python3 scripts/analyst.py summary --account EN` | Valid JSON written to `data/metrics_{date}_EN.json` |
| 7 | Validate analyst JSON output | `python3 scripts/validate.py analyst data/metrics_{date}_EN.json` | `PASS: All 8 checks passed.` |
| 8 | Validate analyst SQLite integrity | `python3 scripts/validate.py analyst_metrics data/metrics_history.db` | `PASS: All 6 checks passed.` |

### Day 14: Manual Metrics (Tests 9-14)

| # | Test | Command | Pass Criteria |
|---|---|---|---|
| 9 | Telegram /metrics view | Send `/metrics` to bot | Bot replies with today's metrics summary |
| 10 | Telegram /metrics input | Send `/metrics EN_20260304_01 impressions=5000` | Bot confirms, value in SQLite with source="manual_telegram" |
| 11 | Telegram screenshot send | Send X Analytics screenshot photo to bot | Bot replies with parsed metrics + confirm prompt |
| 12 | Telegram screenshot confirm | Send `/confirm` after screenshot parsing | Metrics saved to SQLite with source="manual_screenshot" |
| 13 | CSV import | `python3 scripts/analyst.py import --file data/test_manual.csv` | Rows imported, count reported |
| 14 | JSON import | `python3 scripts/analyst.py import --file data/test_manual.json` | Rows imported, count reported |

### Day 15: War Room + Migration + Anomaly (Tests 15-18)

| # | Test | Command | Pass Criteria |
|---|---|---|---|
| 15 | Follower anomaly detection (simulated) | Manually insert yesterday's followers = 1000, today's = 850 into SQLite. Run Marc's anomaly check. | Telegram alert sent with correct percentage |
| 16 | Outbound log SQLite migration | Run publisher outbound, then check both JSON and SQLite | Actions present in both `outbound_log_{date}.json` and SQLite `outbound_log` table with timestamps |
| 17 | War Room full scoring | Run Marc pipeline with existing content plans | War Room scores printed for both EN and JP (0-100), logged in pipeline state |
| 18 | Daily report with real metrics | Run Marc's P6-P8 steps after posting | Telegram receives daily report with real engagement numbers |

### Day 16+: End-to-End (Tests 19-21)

| # | Test | Command | Pass Criteria |
|---|---|---|---|
| 19 | E2E Day 1 | Run full pipeline: Scout → Strategist → Creator → approve → Publisher → Analyst → Daily Report | All 6 agents complete. Metrics collected. Daily report sent. |
| 20 | E2E Day 2 | Run full pipeline again the next day | Pipeline handles existing data. `followers_change` calculated correctly. Anomaly detection runs. |
| 21 | E2E Day 3 | Run full pipeline a third day | 3 consecutive days of data in SQLite. Historical queries return correct ranges. System stable. |

---

## 9. Exit Criteria

**Go/no-go checklist for Phase 5 (VPS deployment)**:

| # | Criterion | How to Verify |
|---|---|---|
| 1 | Analyst collects post metrics for both accounts | Check `post_metrics` table in SQLite after a real run |
| 2 | Analyst collects account snapshots with follower change | Check `account_metrics` table — `followers_change` is non-NULL on Day 2+ |
| 3 | Analyst summary JSON passes validation | `python3 scripts/validate.py analyst data/metrics_{date}_{account}.json` → PASS |
| 4 | SQLite integrity validation passes | `python3 scripts/validate.py analyst_metrics data/metrics_history.db` → PASS |
| 5 | Manual metrics input works via at least 1 method | Input impressions via `/metrics` command and verify in SQLite |
| 6 | War Room produces scores (0-100) for both accounts | Check pipeline state for `war_room` task with score in notes |
| 7 | Follower anomaly detection triggers on simulated data | Simulate >10% drop, verify Telegram alert sent |
| 8 | Daily report includes real engagement data | Verify Telegram daily report has actual numbers (not placeholders) |
| 9 | Outbound actions dual-written to JSON + SQLite | Verify same actions in both `outbound_log_{date}.json` and SQLite `outbound_log` |
| 10 | All 6 agents run in sequence without errors | Full pipeline: Scout → Strategist → Creator → Publisher → Analyst → Marc report |
| 11 | At least 2 consecutive E2E days completed | Dated files in `data/` for 2+ consecutive days |
| 12 | All validation modes pass | All `validate.py` modes (scout, strategist, cross, creator, creator_cross, publisher, publisher_rate_limits, analyst, analyst_metrics) return PASS |

---

## 10. Edge Cases & Gotchas

### 10.1 Analyst Edge Cases

| Case | Expected Behavior |
|---|---|
| No posted tweets for today | `collect` exits 0, logs "No posted tweets found", no metrics rows created |
| Deleted tweet (tweet_id no longer exists) | Batch lookup omits it. Log warning: "Tweet {tweet_id} not found (deleted?)". Skip that tweet. |
| Partial batch response (some tweets returned, some not) | Process returned tweets normally. Log warnings for missing ones. |
| Duplicate collection (collect run twice) | `INSERT OR REPLACE` in SQLite — second run overwrites with newer metrics. Not an error. |
| First day — no yesterday data for follower change | Set `followers_change` to `null`. Log info: "First day — no baseline for follower change." |
| Content plan has no `posted_at` field (pre-Phase 3 data) | Skip `hours_after_post` calculation. Use 0 as fallback. Log warning. |
| `tweet_id` is a dry-run ID (starts with "dry_run_") | Skip API lookup for dry-run IDs. Log info. |

### 10.2 Manual Metrics Edge Cases

| Case | Expected Behavior |
|---|---|
| Invalid post_id format | Reject with error message: "Invalid post_id format. Expected: {account}_{YYYYMMDD}_{slot}" |
| Post_id doesn't exist in any content plan | Accept but log warning: "post_id not found in today's content plans" (may be a past date) |
| Non-X screenshot (random photo) | Vision API returns unparseable result. Bot replies: "Could not parse screenshot." |
| Japanese X Analytics screenshot | Vision API should handle Japanese UI. Prompt includes "Extract tweet metrics" without language assumption. |
| Duplicate manual entries | Later entry overwrites earlier one (same `INSERT OR REPLACE` behavior) |
| Wrong CSV format (missing header) | Reject with error: "CSV must have header row with at least 'post_id' column" |
| CSV with extra columns | Ignore unknown columns, process known ones |
| Negative metric values | Reject: "Metric values must be non-negative" |

### 10.3 War Room Edge Cases

| Case | Expected Behavior |
|---|---|
| Unexpected content plan structure (missing fields) | Score 0 for that criterion, log warning. Don't crash — degrade gracefully. |
| Boundary scores (exactly 70, exactly 50) | 70 = "Good" threshold (proceed), 50 = "Warning" threshold (flag) |
| Case-insensitive category matching | `"Portrait"` matches `"portrait"`. All comparisons lowercased. |
| Content plan has 0 posts | Score 0 total. Log error: "Content plan has no posts." |
| Strategy missing for an account | Skip scoring for that account. Log error. |
| All image prompts identical | Deduct 5 per duplicate pair. If 4 posts with same prompt = 3 pairs = 15 deducted (cap at max). |

### 10.4 Follower Anomaly Edge Cases

| Case | Expected Behavior |
|---|---|
| First day (no yesterday data) | Skip anomaly check entirely. Log info: "Skipping anomaly check — no baseline." |
| Zero followers | Skip anomaly check (division by zero in percentage). Log warning. |
| Stale API data (followers same as yesterday) | `followers_change = 0`, no anomaly. Normal. |
| Large positive growth (>10% increase) | Also triggers anomaly alert (could be viral or bot activity). Alert shows positive change. |
| Follower count dips then recovers (API eventual consistency) | Anomaly alert on the dip. Next day shows recovery. Operator decides if action needed. |

### 10.5 Outbound Migration Edge Cases

| Case | Expected Behavior |
|---|---|
| SQLite concurrency (bot and publisher writing simultaneously) | WAL mode handles this. Both can write without locking issues. |
| JSON and SQLite drift (one write succeeds, other fails) | JSON is primary. If SQLite fails, log warning and continue. |
| Migration on existing DB (timestamp column already exists) | `PRAGMA table_info` check prevents duplicate `ALTER TABLE`. Idempotent. |
| Old outbound_log rows (no timestamp) | Existing rows have `timestamp = NULL`. New rows have timestamps. Acceptable. |

---

*Phase 4 Technical Specification v1.0*
*Date: March 4, 2026*
*Parent: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md)*
