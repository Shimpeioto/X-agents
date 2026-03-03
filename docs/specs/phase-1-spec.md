# Phase 1 Technical Specification — Scout + Strategist + Marc Foundation

**Document version**: 1.0
**Date**: March 3, 2026
**Status**: Draft
**Phase**: 1 of 6 (Days 3-5)
**Parent documents**: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md), [PRD v1.1](./x-ai-beauty-prd-v1.md)

---

## 1. Scope & Timeline

**Phase 1 = Days 3-5** (3 calendar days, following Phase 0 completion).

### What Phase 1 Builds

| Agent | Scope |
|---|---|
| **Scout** | Full implementation — Python script + skill file. Daily competitor research via X API (read-only). |
| **Strategist** | Full implementation — Claude reasoning task via skill file. Daily growth strategy generation from Scout data. |
| **Marc (foundation)** | Pipeline orchestration only: Scout → validate → Strategist → validate → cross-check → log. No Telegram reporting, no War Room, no command processing. |

### What Phase 1 Does NOT Build

- Creator agent (Phase 2)
- Publisher agent (Phase 3)
- Analyst agent (Phase 4)
- Telegram Bot / command processing (Phase 2)
- War Room reviews (Phase 2+)
- Cron scheduling (Phase 5)
- Any write operations to X API (Phase 3)
- Automated test suite — all testing is manual via CLI

### Day-by-Day Plan

| Day | Focus | Key Deliverable |
|---|---|---|
| Day 3 | X API wrapper (`x_api.py`) + Scout script (`scout.py`) | Scout produces valid `scout_report_{date}.json` for all competitors in config |
| Day 4 | Strategist skill file (`agents/strategist.md`) + testing | Strategist produces valid `strategy_{date}.json` with EN + JP sections |
| Day 5 | Marc agent (`agents/marc.md`) + `validate.py` + end-to-end testing | Pipeline runs Scout → Strategist end-to-end with validation |

---

## 2. X API Budget for Phase 1

Phase 1 uses **bearer token only** (app-only auth, read-only). Only Scout makes API calls.

### 2.1 One-Time Costs (First Run)

| Operation | Endpoint | Calls | Notes |
|---|---|---|---|
| Resolve user_ids for all competitors | `GET /2/users/by/username/:username` | 41 | One-time; IDs saved to `competitors.json` |

### 2.2 Daily Costs (Per Scout Run)

| Operation | Endpoint | Calls/Run | Notes |
|---|---|---|---|
| Get user info (followers, etc.) | `GET /2/users?ids=` | 5 | Batch lookup, 100 users/request → ceil(41/100) = 1, but using conservative estimate with user.fields |
| Get user timelines | `GET /2/users/:id/tweets` | 41 | One per competitor, max_results=10 |
| Search recent tweets | `GET /2/tweets/search/recent` | 8 | One per tracked keyword |
| **Total per run** | | **~54** | |

### 2.3 Monthly Projection

| Metric | Value |
|---|---|
| Daily reads (Scout) | ~54 calls/day |
| First-run overhead | +41 calls (user_id resolution, one-time) |
| Monthly reads (30 days) | ~1,661 calls/month |
| Basic plan monthly limit | 15,000 reads/month |
| Phase 1 usage as % of limit | **~11%** |
| Headroom | **~89%** for Phase 2+ agents |

> **Note**: The full-spec estimate of ~10,700/month includes Analyst reads (~1,320/month) and higher Scout usage with 30 posts/competitor. Phase 1 Scout fetches 10 recent tweets per competitor to stay conservative. This can be increased in later phases.

### 2.4 Rate Limits Per Endpoint

| Endpoint | Rate Limit (Basic) | Phase 1 Usage | Status |
|---|---|---|---|
| `GET /2/users/by/username/:username` | 300/15 min | 41 (first run only) | Safe |
| `GET /2/users?ids=` | 300/15 min | 1/run | Safe |
| `GET /2/users/:id/tweets` | 1,500/15 min | 41/run | Safe |
| `GET /2/tweets/search/recent` | 450/15 min | 8/run | Safe |

---

## 3. Agent Definitions (Phase 1 Scope)

### 3.1 Scout Agent

| Item | Details |
|---|---|
| **Role** | Competitor analysis & trend research |
| **Implementation** | Python script (`scripts/scout.py`) using `scripts/x_api.py` wrapper |
| **Why Python** | Makes 50+ API calls per run — better as a deterministic script than Claude reasoning |
| **Input** | `config/competitors.json` |
| **Output** | `data/scout_report_{YYYYMMDD}.json` |
| **Auth** | Bearer token only (read-only, no user context needed) |

**Data collected per competitor**:

| Field | Source | Notes |
|---|---|---|
| `handle` | competitors.json | As-is from config |
| `user_id` | API lookup / cached | Resolved once, then cached |
| `display_name` | `GET /2/users` | From `user.name` field |
| `followers` | `user.public_metrics.followers_count` | Current snapshot |
| `following` | `user.public_metrics.following_count` | Current snapshot |
| `tweet_count` | `user.public_metrics.tweet_count` | Total post count |
| `description` | `user.description` | Bio text |
| `recent_posts` | `GET /2/users/:id/tweets` | Last 10 tweets with `public_metrics`, `created_at`, `entities` |
| `avg_engagement_rate` | Calculated | See formula below |
| `top_posts` | Sorted from recent_posts | Top 3 by engagement rate |
| `posting_frequency` | Calculated | Posts per day over the fetched window |
| `hashtags_used` | Extracted from entities | Frequency count of hashtags |
| `market` | competitors.json | EN, JP, or both |

**Engagement rate formula**:

```
engagement_rate = (like_count + retweet_count + reply_count + quote_count) / followers_count
```

- When `followers_count == 0`: set `engagement_rate` to `0.0` (avoid division by zero)
- This is a proxy metric (no impressions in Basic plan). It's consistent across competitors since all use the same formula.

**Hashtag analysis**:

Scout collects all hashtags from competitor posts and produces:
- `hashtag_frequency`: count of each unique hashtag across all competitors
- `hashtag_by_market`: breakdown of hashtag usage in EN vs JP markets

**Keyword search analysis**:

For each tracked keyword in `competitors.json.tracked_keywords`:
- Fetch up to 10 recent tweets via `GET /2/tweets/search/recent`
- Extract: tweet text, author handle, public_metrics, hashtags
- Identify any accounts not in our competitor list (→ `new_accounts_discovered`)

**Market comparison**:

Scout groups competitor data by market (EN / JP / both) and calculates per-market averages:
- Average followers
- Average engagement rate
- Average posting frequency
- Top-performing hashtags per market

**Error handling**:

| Error | Behavior |
|---|---|
| API rate limit (429) | Wait `reset_time` seconds, then retry. Max 3 retries. |
| User not found (404) | Log warning, skip competitor, mark `status: "not_found"` in output. |
| User suspended | Log warning, skip competitor, mark `status: "suspended"` in output. |
| Protected account (401) | Log warning, skip competitor, mark `status: "protected"` in output. |
| Network error | Retry after 5 seconds. Max 3 retries. If all fail, abort run. |
| Empty timeline | Record competitor with `recent_posts: []`. Not an error. |

### 3.2 Strategist Agent

| Item | Details |
|---|---|
| **Role** | Data-driven growth strategy formulation |
| **Implementation** | Claude reasoning task via skill file (`agents/strategist.md`). No Python script needed. |
| **Why Claude** | Pure analysis and judgment — exactly what LLMs excel at. No API calls. |
| **Input** | `data/scout_report_{YYYYMMDD}.json` (today's Scout output) |
| **Output** | `data/strategy_{YYYYMMDD}.json` (dated archive). Marc copies to `data/strategy_current.json` after validation passes. |
| **Invocation** | `claude -p "You are the Strategist agent. Read your skill file at agents/strategist.md for full instructions. Today's scout report: data/scout_report_{YYYYMMDD}.json. Write output to data/strategy_{YYYYMMDD}.json." --dangerously-skip-permissions` |

**Output structure** — per-account (EN and JP separately):

| Section | Contents |
|---|---|
| `posting_schedule` | 3-5 time slots per account with category and priority |
| `content_mix` | Percentage breakdown by content category (must sum to 100) |
| `hashtag_strategy` | `always_use`, `rotate`, `trending_today` arrays |
| `outbound_strategy` | Daily limits (likes/replies/follows), target accounts, reply style |
| `ab_test` | Current test variable, variants, duration |
| `key_insights` | 3-5 actionable observations from today's Scout data |
| `risks` | Any risks or concerns identified from the data |

**Quality checklist** (Marc validates these):

- [ ] Both EN and JP sections present
- [ ] `content_mix` percentages sum to 100 for each account
- [ ] `posting_schedule` has 3-5 slots per account
- [ ] `posting_schedule` times are appropriate (EN in UTC, JP in JST)
- [ ] No time slot conflicts within the same account
- [ ] `hashtag_strategy.always_use` contains at least 1 hashtag
- [ ] `outbound_strategy` daily limits are within global rules (max 30 likes, 10 replies, 5 follows)
- [ ] `key_insights` has at least 3 entries
- [ ] JSON is valid and parseable
- [ ] No markdown code fences wrapping the JSON output

### 3.3 Marc Agent (Foundation — Phase 1 Scope)

| Item | Details |
|---|---|
| **Role** | Pipeline orchestration + validation |
| **Implementation** | Claude agent (`agents/marc.md`) + validation script (`scripts/validate.py`) + shell wrapper (`scripts/run_pipeline.sh`) |
| **Phase 1 scope** | Sequencing (Scout → Strategist), output validation, cross-checking, logging |
| **NOT in Phase 1** | Telegram reporting, War Room, command processing, error escalation via Telegram |

**Phase 1 pipeline flow** (Marc executes these steps as a Claude agent via tool calls):

```
1. bash: Initialize pipeline state → data/pipeline_state_{date}.json
2. bash: python3 scripts/scout.py                                    (run Scout)
3. bash: python3 scripts/validate.py scout <report_path>             (deterministic pass/fail)
4. bash: claude -p "Read agents/strategist.md ..." --dangerously-skip-permissions  (spawn Strategist subagent)
5. bash: python3 scripts/validate.py strategist <strategy_path>      (deterministic pass/fail)
6. bash: python3 scripts/validate.py cross <report> <strategy>       (deterministic cross-checks)
   + Marc's own reasoning for semantic cross-validation              (judgment — Claude's strength)
7. file: Update pipeline state → status: completed
8. file: Copy strategy_{date}.json → strategy_current.json  (only after all validations pass)
9. file: Write pipeline log → logs/pipeline_{date}.log
```

**Validation rules — Scout output**:

| Rule | Check |
|---|---|
| File exists | `data/scout_report_{date}.json` must exist and be non-empty |
| Valid JSON | Must parse without errors |
| Required fields present | `date`, `competitors`, `trending_topics`, `trending_posts`, `new_accounts_discovered` |
| Competitor count | `len(competitors)` should match `config/competitors.json` count (allowing for skipped accounts) |
| No null user_ids | Every successfully-fetched competitor must have a non-empty `user_id` |
| Engagement rates valid | All `engagement_rate` values ≥ 0 and ≤ 1.0 |
| Date matches | `report.date` matches today's date (JST) |

**Validation rules — Strategist output**:

| Rule | Check |
|---|---|
| File exists | `data/strategy_{date}.json` must exist and be non-empty |
| Valid JSON | Must parse without errors |
| Both accounts present | Top-level keys include both `EN` and `JP` sections |
| Content mix sums to 100 | Each account's `content_mix` values sum to 100 |
| Schedule slot count | Each account has 3-5 `posting_schedule` entries |
| Limits within bounds | `outbound_strategy` limits ≤ global rules maximums |
| Insights present | `key_insights` has ≥ 3 entries |

**Cross-validation rules** (Scout ↔ Strategist):

| Rule | Check |
|---|---|
| Market coverage | If Scout reports both EN and JP competitors, Strategist must have both EN and JP sections |
| Hashtag consistency | Strategist's `always_use` hashtags should appear in Scout's `hashtag_frequency` (top hashtags) |
| No contradictions | If Scout shows EN outperforming JP, Strategist's insights shouldn't claim the opposite without explanation |

**Pipeline logging format**:

```
[2026-03-03 01:00:00] [MARC] [INFO] Pipeline start — Phase 1 (Scout + Strategist)
[2026-03-03 01:00:01] [MARC] [INFO] Running Scout...
[2026-03-03 01:05:23] [SCOUT] [INFO] Completed — 41 competitors fetched, 2 skipped (protected)
[2026-03-03 01:05:24] [MARC] [INFO] Scout validation — PASS (39/41 competitors, all fields present)
[2026-03-03 01:05:25] [MARC] [INFO] Running Strategist...
[2026-03-03 01:08:45] [STRATEGIST] [INFO] Completed — EN + JP strategies generated
[2026-03-03 01:08:46] [MARC] [INFO] Strategist validation — PASS (all checks passed)
[2026-03-03 01:08:47] [MARC] [INFO] Cross-validation — PASS
[2026-03-03 01:08:47] [MARC] [INFO] Pipeline complete — duration: 8m47s
```

---

## 4. Implementation Architecture

### 4.1 Why This Split

| Agent | Implementation | Rationale |
|---|---|---|
| Scout | Python script (`scripts/scout.py`) | Makes 50+ API calls per run. Python handles HTTP, pagination, error recovery, and JSON assembly deterministically. Claude would waste context tokens on repetitive API calls. |
| Strategist | Claude reasoning (`agents/strategist.md`) | Pure analysis — read data, reason about patterns, produce recommendations. No API calls. This is exactly what Claude excels at. |
| Marc | Claude agent (`agents/marc.md`) calling Python validation scripts | Orchestration involves judgment (cross-validation, error recovery) — Claude's strength. Python validation scripts (`scripts/validate.py`) provide deterministic feedback loops. Parent spec defines Marc as Claude in all cron jobs; using Claude from day 1 avoids a Phase 2 rewrite. |

### 4.2 Execution Model

```
# Day-to-day operation (Phase 1 — manual CLI):
$ cd /path/to/x-ai-beauty
$ bash scripts/run_pipeline.sh
# — or directly —
$ claude -p "You are Marc, the COO agent. Read agents/marc.md for your full instructions. Run today's pipeline for $(TZ=Asia/Tokyo date +%Y-%m-%d)." --dangerously-skip-permissions

# What Marc (Claude) does internally via tool calls:
# 1. bash: python3 scripts/scout.py                          (runs Scout)
# 2. bash: python3 scripts/validate.py scout <report_path>   (deterministic pass/fail)
# 3. bash: claude -p "Read agents/strategist.md ..."          (spawns Strategist as isolated subagent)
# 4. bash: python3 scripts/validate.py strategist <strat_path> (deterministic pass/fail)
# 5. reasoning: cross-validate Scout ↔ Strategist             (semantic judgment — Claude's strength)
# 6. file: write pipeline_state_{date}.json
# 7. file: copy strategy_{date}.json → strategy_current.json  (only after all validations pass)
# 8. file: write pipeline log
```

### 4.3 Dependency Chain

```
config/competitors.json ──▶ scout.py ──▶ data/scout_report_{date}.json
                                                    │
                                                    ▼
                                         agents/strategist.md (Claude)
                                                    │
                                                    ▼
                                         data/strategy_{date}.json
                                                    │
                                                    ▼ (Marc copies after validation)
                                         data/strategy_current.json
                                                    │
                                                    ▼
                                         data/pipeline_state_{date}.json
```

### 4.4 Harness Design Principles

Three principles derived from harness engineering research ("Agent Harness is the Real Product", "Seeing like an Agent", "Coding Agent Harness"). Marc (`agents/marc.md`) IS the harness — a Claude agent that orchestrates scripts and subagents while using `scripts/validate.py` as its deterministic feedback loop.

| # | Principle | Phase 1 Implication |
|---|---|---|
| **H1** | **The harness is the product** — Marc + `validate.py` are the quality gates, not the prompts. "Skills are programmable, context-aware, composable units of agent behavior" — Marc's skill file defines the harness. | Invest time in validation rules (`validate.py`) and Marc's orchestration logic (`agents/marc.md`). A missed validation check is a product defect — it lets bad data flow downstream. |
| **H2** | **Plan for simplification** — Validation rules that never fire after 10+ runs are removal candidates. | Track which rules actually catch issues. If pipeline complexity grows while model capabilities improve, something is wrong. Review at each phase boundary. |
| **H3** | **Errors are context** — Marc preserves error details (stderr, validation failures) and reasons about them for recovery. | When Strategist fails, Marc reads the stderr and validation output, reasons about what went wrong, and crafts a targeted retry prompt. This is semantic error recovery — a key advantage of Marc-as-Claude over a Python script that retries blindly. |

---

## 5. File Specifications

### 5.1 `scripts/x_api.py` — X API Wrapper

**Purpose**: Thin wrapper around tweepy for X API v2 calls. Used by Scout (and later by Publisher/Analyst).

**Class design**:

```python
class XApiClient:
    """X API v2 wrapper using tweepy."""

    def __init__(self, bearer_token: str):
        """Initialize with bearer token for read-only access."""
        self.client = tweepy.Client(bearer_token=bearer_token)

    def resolve_user_id(self, handle: str) -> dict:
        """Resolve a handle to user_id + public_metrics.
        Args:
            handle: X handle without @ prefix
        Returns:
            {"user_id": str, "username": str, "name": str,
             "description": str, "public_metrics": dict} or None if not found
        """

    def get_user_info_batch(self, user_ids: list[str]) -> list[dict]:
        """Batch lookup of user info by user_ids (up to 100 per request).
        Returns list of user data dicts with public_metrics.
        """

    def get_user_timeline(self, user_id: str, max_results: int = 10) -> list[dict]:
        """Fetch recent tweets for a user.
        Args:
            user_id: The user's numeric ID
            max_results: Number of tweets to fetch (5-100)
        Returns:
            List of tweet dicts with text, public_metrics, created_at, entities
        """

    def search_recent(self, query: str, max_results: int = 10) -> list[dict]:
        """Search recent tweets by keyword.
        Args:
            query: Search query string
            max_results: Number of results (10-100)
        Returns:
            List of tweet dicts with author info
        """
```

**Auth pattern** (from existing `test_x_api.py`):

```python
import tweepy, json, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(PROJECT, "config/accounts.json")) as f:
    config = json.load(f)

xapi = config["x_api"]
client = tweepy.Client(bearer_token=xapi["bearer_token"])
```

**Tweepy Response normalization**:

Tweepy returns `tweepy.Response` objects, not plain dicts. The wrapper must normalize:

```python
def _normalize_user(self, user) -> dict:
    """Convert tweepy User object to plain dict."""
    if user is None:
        return None
    return {
        "user_id": str(user.id),
        "username": user.username,
        "name": user.name,
        "description": user.description or "",
        "public_metrics": dict(user.public_metrics) if user.public_metrics else {}
    }

def _normalize_tweet(self, tweet) -> dict:
    """Convert tweepy Tweet object to plain dict."""
    if tweet is None:
        return None
    return {
        "tweet_id": str(tweet.id),
        "text": tweet.text,
        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
        "public_metrics": dict(tweet.public_metrics) if tweet.public_metrics else {},
        "entities": tweet.entities if hasattr(tweet, 'entities') and tweet.entities else {}
    }
```

**Error handling**:

```python
import tweepy
import time
import logging

MAX_RETRIES = 3
RETRY_WAIT = 5  # seconds

def _api_call_with_retry(self, func, *args, **kwargs):
    """Execute an API call with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except tweepy.TooManyRequests as e:
            reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
            wait = max(reset_time - int(time.time()), RETRY_WAIT)
            logging.warning(f"Rate limited. Waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
            time.sleep(wait)
        except tweepy.NotFound:
            logging.warning(f"User not found")
            return None
        except tweepy.Forbidden:
            logging.warning(f"User suspended or protected")
            return None
        except Exception as e:
            logging.error(f"API error: {e} (attempt {attempt+1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAIT)
    logging.error(f"All {MAX_RETRIES} retries exhausted")
    return None
```

### 5.2 `scripts/scout.py` — Scout Agent Script

**Purpose**: Fetch competitor data from X API, analyze, and produce the scout report JSON.

**Class design**:

```python
class Scout:
    """Competitor research agent."""

    def __init__(self, config_path: str, dry_run: bool = False):
        """Load competitors.json and initialize X API client."""

    def resolve_user_ids(self) -> int:
        """Resolve empty user_ids in competitors.json.
        Returns number of newly resolved IDs.
        Writes updated IDs back to competitors.json.
        """

    def fetch_all_competitors(self, max_competitors: int = None) -> list[dict]:
        """Fetch data for all (or max_competitors) competitors.
        Returns list of competitor data dicts.
        """

    def fetch_competitor(self, competitor: dict) -> dict:
        """Fetch data for a single competitor.
        Returns enriched competitor dict with recent_posts, metrics, etc.
        """

    def search_keywords(self) -> dict:
        """Search tracked keywords for trending content.
        Returns {trending_topics, trending_posts, new_accounts_discovered}.
        """

    def analyze(self, competitors: list[dict], keyword_data: dict) -> dict:
        """Combine all data into the final scout report.
        Calculates engagement rates, market comparisons, hashtag analysis.
        """

    def run(self, max_competitors: int = None) -> str:
        """Full scout run. Returns path to output file."""

    def save_report(self, report: dict) -> str:
        """Save report to data/scout_report_{date}.json. Returns file path."""
```

**Output path convention**: Scout always saves to `data/scout_report_{YYYYMMDD}.json` where `YYYYMMDD` is today's date in JST. The `__main__` block prints the output path to stdout as its last line (e.g., `Saved: data/scout_report_20260303.json`). Marc constructs the expected path deterministically from today's date and verifies the file exists before proceeding.

**CLI interface**:

```bash
# Full run (all competitors in config/competitors.json)
python3 scripts/scout.py

# Limited run (for testing)
python3 scripts/scout.py --max-competitors 1
python3 scripts/scout.py --max-competitors 5

# Dry run (no API calls, generates mock data for pipeline testing)
# Produces a valid scout_report with synthetic competitor data (5 EN, 3 JP)
# Useful for testing validate.py and Strategist without consuming API quota
python3 scripts/scout.py --dry-run

# Force re-resolve user_ids (even if already cached)
python3 scripts/scout.py --force-resolve
```

**First-run user_id resolution**:

On the first run, all `user_id` fields in `competitors.json` are empty strings. Scout must:

1. Detect empty `user_id` fields
2. Call `GET /2/users/by/username/:username` for each (41 calls)
3. Write resolved IDs back to `competitors.json` (updating in-place)
4. On subsequent runs, skip resolution for competitors with existing `user_id`

**Edge cases**:

| Case | Behavior |
|---|---|
| Handle with `@` prefix | Strip `@` before API call (`.lstrip("@")`) |
| Handle without `@` prefix | Use as-is |
| Suspended account | Set `status: "suspended"`, skip data fetch, continue |
| Protected account | Set `status: "protected"`, skip data fetch, continue |
| Account not found | Set `status: "not_found"`, skip data fetch, continue |
| Empty timeline (0 tweets) | Set `recent_posts: []`, `engagement_rate: 0`, continue |
| followers == 0 | Set `engagement_rate: 0.0` (avoid division by zero) |
| API rate limit hit mid-run | Wait for reset, then continue from where we left off |

### 5.3 `scripts/validate.py` — Unified Validation Script

**Purpose**: Deterministic pass/fail validation for Scout reports, Strategist strategies, and cross-validation between them. Called by Marc (Claude agent) via bash tool — provides the structured feedback loop (Harness Principle H1).

**CLI interface**:

```bash
# Validate a Scout report
python3 scripts/validate.py scout data/scout_report_20260303.json

# Validate a Strategist strategy
python3 scripts/validate.py strategist data/strategy_20260303.json

# Cross-validate Scout report against Strategist strategy
python3 scripts/validate.py cross data/scout_report_20260303.json data/strategy_20260303.json
```

**Output format** (stdout — structured for Marc to parse):

```
# On success:
PASS: All 7 checks passed.

# On failure:
FAIL: 2 of 7 checks failed.
  - content_mix_sum: EN content_mix sums to 95, expected 100
  - posting_schedule_slots: JP has 2 slots, expected 3-5
```

**Exit codes**: `0` = all checks passed, `1` = one or more checks failed, `2` = invalid usage or file not found.

**Validation modes**:

| Mode | Input | Checks |
|---|---|---|
| `scout` | `scout_report_{date}.json` | Valid JSON; has `competitors` array; `competitors_fetched` ≥ 1; each competitor has required fields (`handle`, `user_id`, `status`, `market`); `market_comparison` section present; `hashtag_frequency` present; engagement_rate ≥ 0 |
| `strategist` | `strategy_{date}.json` | Valid JSON; has both `EN` and `JP` top-level keys; each account has `posting_schedule` with 3-5 slots; `content_mix` values sum to 100; `hashtag_strategy` present with `always_use` array; `outbound_strategy` within global rules limits (≤30 likes, ≤10 replies, ≤5 follows); `ab_test` section present |
| `cross` | scout report + strategy | Markets referenced in strategy exist in scout data; Strategist's hashtag recommendations appear in Scout's `hashtag_frequency`; outbound target accounts exist in competitor list; posting schedule times are reasonable (not all identical) |

**Function design**:

```python
import json, sys

def validate_scout(report_path: str) -> tuple[bool, list[str]]:
    """Validate Scout output. Returns (passed, list_of_issues)."""

def validate_strategist(strategy_path: str) -> tuple[bool, list[str]]:
    """Validate Strategist output. Returns (passed, list_of_issues)."""

def cross_validate(scout_path: str, strategy_path: str) -> tuple[bool, list[str]]:
    """Cross-validate Scout and Strategist outputs. Returns (passed, list_of_issues)."""

if __name__ == "__main__":
    mode = sys.argv[1]  # "scout", "strategist", or "cross"
    # Parse args, run appropriate validation, print PASS/FAIL, exit with code
```

### 5.3.1 `scripts/run_pipeline.sh` — Thin Shell Wrapper

**Purpose**: Convenience entry point that invokes Marc (Claude agent) with today's date. This is the only "pipeline script" — all orchestration logic lives in `agents/marc.md`.

```bash
#!/bin/bash
# scripts/run_pipeline.sh — Invoke Marc to run today's pipeline
set -euo pipefail
DATE=$(TZ=Asia/Tokyo date +%Y-%m-%d)
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

# Prevent concurrent pipeline runs
LOCK_FILE="$PROJECT_DIR/.pipeline.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Pipeline already running (lock file exists: $LOCK_FILE). Exiting."
    exit 1
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

claude -p "You are Marc, the COO agent. Read agents/marc.md for your full instructions.
Run today's pipeline for ${DATE}." --dangerously-skip-permissions
```

**Usage**:

```bash
# Full pipeline
bash scripts/run_pipeline.sh

# Scout only (pass instruction to Marc)
claude -p "You are Marc. Read agents/marc.md. Run Scout only for $(TZ=Asia/Tokyo date +%Y-%m-%d). Skip Strategist." --dangerously-skip-permissions

# Skip Scout (use existing report)
claude -p "You are Marc. Read agents/marc.md. Run Strategist only for $(TZ=Asia/Tokyo date +%Y-%m-%d). Use the existing scout report." --dangerously-skip-permissions
```

> **Why a shell wrapper, not a Python script?** Marc IS the orchestrator. The shell script just passes today's date and invokes Claude. All sequencing, validation calls, error handling, and logging are Marc's responsibility via his skill file. This matches the parent spec (v2.4), which defines `orchestrator.sh` as the entry point for Marc.

### 5.4 Skill File Content Outlines

#### `agents/scout.md`

```
# Scout Agent — Competitor Research & Trend Analysis
## Role
## Data collection scope (what to fetch per competitor)
## Engagement rate formula
## Market comparison instructions
## Hashtag analysis instructions
## Output JSON schema reference
## Error handling instructions
## Edge cases (protected accounts, empty timelines, etc.)
```

> Note: In Phase 1, Scout is primarily a Python script. The skill file serves as documentation and is used if Marc invokes Scout via Claude for any reason.

#### `agents/strategist.md`

Structured as progressive disclosure steps — the model reads only what it needs, when it needs it, keeping context usage minimal (see Harness Principle H1).

```
# Strategist Agent — Growth Strategy Engine

## Role
You are the Strategist agent. You analyze competitor data and produce daily growth strategies.

## Step 1: Read today's inputs (always)
- Read the scout report at the path provided in the prompt
- Read config/global_rules.md for engagement limits and posting constraints

## Step 2: Read context if available (conditional)
- IF data/strategy_current.json exists → read it for continuity with yesterday's strategy
- IF it does not exist (first run) → skip this step, produce strategy from scratch

## Step 3: Analysis
- Identify top-performing content categories from competitor data
- Calculate optimal posting times from competitor posting patterns
- Compare EN vs JP market performance
- Design hashtag strategy based on Scout's hashtag_frequency data
- Set outbound engagement policy within global rules limits
- Design one A/B test per account

## Output
- Write valid JSON matching the schema in Section 6.2 of the Phase 1 spec
- Both EN and JP sections required
- content_mix must sum to 100 per account
- posting_schedule must have 3-5 slots per account
- outbound limits must respect global rules (max 30 likes, 10 replies, 5 follows)

## Format
- Output ONLY valid JSON — no markdown code fences, no commentary
```

#### `agents/marc.md`

Marc is a **Claude agent** that orchestrates the pipeline using bash tool calls (to run scripts and spawn subagents) and file tool calls (to write state and logs). This skill file is Marc's full instruction set.

```
# Marc Agent — COO / Orchestrator (Phase 1 Foundation)

## Role
You are Marc, the COO agent. You orchestrate the daily intelligence pipeline.
You use bash tool calls to run Python scripts and spawn subagents, and file tool calls to write state and logs.

## Pipeline Sequence (Phase 1)

Today's date is provided in the invocation prompt as YYYY-MM-DD (e.g., 2026-03-03).
For file paths, strip dashes to get YYYYMMDD format (e.g., data/scout_report_20260303.json).
For JSON date fields, use the original YYYY-MM-DD format.

### Step 1: Run Scout
- bash: python3 scripts/scout.py
- Expected output: data/scout_report_{YYYYMMDD}.json
- If Scout fails (non-zero exit): log the error (include stderr), write pipeline state with status "failed", STOP.

### Step 2: Validate Scout
- bash: python3 scripts/validate.py scout data/scout_report_{YYYYMMDD}.json
- Read stdout. If output starts with "FAIL": log the specific failures, write pipeline state, STOP.
- If "PASS": proceed.

### Step 3: Run Strategist (isolated subagent)
- bash: claude -p "You are the Strategist agent. Read your skill file at agents/strategist.md for full instructions.
  Today's date: {YYYY-MM-DD}
  Scout report path: data/scout_report_{YYYYMMDD}.json
  Generate today's growth strategy based on the scout report.
  Write the output to: data/strategy_{YYYYMMDD}.json
  Output ONLY valid JSON — no markdown code fences, no commentary." --dangerously-skip-permissions
- Expected output: data/strategy_{YYYYMMDD}.json
- NOTE: Strategist writes ONLY the dated file. Marc writes strategy_current.json in Step 6 after validation passes.
- If Strategist fails: read the error, reason about what went wrong, craft a BETTER retry prompt
  with the error context included (H3). Retry ONCE. If retry also fails: log both attempts, STOP.

### Step 4: Validate Strategist
- bash: python3 scripts/validate.py strategist data/strategy_{YYYYMMDD}.json
- Read stdout. If "FAIL": log failures, write pipeline state, STOP.
- If "PASS": proceed.

### Step 5: Cross-validate (your own reasoning)
- bash: python3 scripts/validate.py cross data/scout_report_{YYYYMMDD}.json data/strategy_{YYYYMMDD}.json
- Read the deterministic cross-validation results.
- THEN apply your own semantic judgment:
  - Does the strategy make sense given the scout data?
  - Are there contradictions (e.g., Scout shows EN outperforming JP, but strategy claims JP is stronger)?
  - Are the recommendations actionable and specific?
- If contradictions found: log them as warnings in pipeline state. Do NOT stop — flag for human review.

### Step 6: Write pipeline state + log
- Write data/pipeline_state_{YYYYMMDD}.json (schema in Section 6.3)
- Write logs/pipeline_{YYYYMMDD}.log with timestamped entries for each step
- Copy data/strategy_{YYYYMMDD}.json → data/strategy_current.json (Marc writes this ONLY after all validations pass — Strategist never writes strategy_current.json directly)

## Logging Conventions
- Format: [YYYY-MM-DD HH:MM:SS] [AGENT] [LEVEL] message
- Agents: MARC, SCOUT, STRATEGIST
- Levels: INFO, WARN, ERROR
- All times in JST (Asia/Tokyo)

## Harness Evolution Notes
- Track which validation rules actually fire (catch real issues)
- After 10+ successful runs, review rules that never fired — candidates for removal (H2)
- Pipeline should get simpler over time as model outputs stabilize
- Review at each phase boundary (Phase 1→2, 2→3, etc.)

## NOT in Scope for Phase 1
- Telegram reporting
- War Room reviews
- Command processing
- Creator/Publisher/Analyst invocation
```

---

## 6. Output Schemas

### 6.1 `data/scout_report_{YYYYMMDD}.json`

```json
{
  "date": "2026-03-03",
  "generated_at": "2026-03-03T01:05:23+09:00",
  "competitors_total": 41,
  "competitors_fetched": 39,
  "competitors_skipped": 2,
  "competitors": [
    {
      "handle": "example_account",
      "user_id": "123456789",
      "display_name": "Example",
      "status": "ok",
      "market": "EN",
      "category": "ai_beauty",
      "followers": 45200,
      "following": 1234,
      "tweet_count": 5678,
      "description": "AI art creator...",
      "recent_posts": [
        {
          "tweet_id": "1234567890123456789",
          "text": "Post text here...",
          "created_at": "2026-03-02T14:30:00Z",
          "public_metrics": {
            "like_count": 2400,
            "retweet_count": 180,
            "reply_count": 95,
            "quote_count": 12,
            "bookmark_count": 45
          },
          "hashtags": ["#AIart", "#AIbeauty"],
          "engagement_rate": 0.059
        }
      ],
      "avg_engagement_rate": 0.042,
      "posting_frequency": 3.5,
      "top_posts": [
        {
          "tweet_id": "...",
          "engagement_rate": 0.089,
          "like_count": 4200
        }
      ],
      "hashtags_used": {
        "#AIart": 8,
        "#AIbeauty": 6,
        "#midjourney": 3
      }
    }
  ],
  "skipped_competitors": [
    {
      "handle": "suspended_account",
      "status": "suspended",
      "reason": "Account suspended"
    }
  ],
  "hashtag_frequency": {
    "#AIart": 120,
    "#AIbeauty": 95,
    "#AIgirl": 45
  },
  "hashtag_by_market": {
    "EN": {"#AIart": 80, "#AIbeauty": 60},
    "JP": {"#aiイラスト": 40, "#AI美女": 35}
  },
  "market_comparison": {
    "EN": {
      "competitor_count": 24,
      "avg_followers": 25000,
      "avg_engagement_rate": 0.038,
      "avg_posting_frequency": 3.2,
      "top_hashtags": ["#AIart", "#AIbeauty", "#AIgirl"]
    },
    "JP": {
      "competitor_count": 15,
      "avg_followers": 18000,
      "avg_engagement_rate": 0.045,
      "avg_posting_frequency": 2.8,
      "top_hashtags": ["#aiイラスト", "#AI美女", "#AIart"]
    }
  },
  "trending_topics": [
    {
      "keyword": "#AIbeauty",
      "sample_tweets": [
        {
          "tweet_id": "...",
          "text": "...",
          "author": "someone",
          "like_count": 500
        }
      ]
    }
  ],
  "trending_posts": [
    {
      "tweet_id": "...",
      "text": "...",
      "author": "viral_account",
      "like_count": 10000,
      "engagement_rate": 0.12
    }
  ],
  "new_accounts_discovered": [
    {
      "handle": "new_ai_creator",
      "followers": 8500,
      "source": "keyword_search:#AIbeauty"
    }
  ]
}
```

### 6.2 `data/strategy_{YYYYMMDD}.json`

```json
{
  "date": "2026-03-03",
  "generated_at": "2026-03-03T01:08:45+09:00",
  "scout_report_used": "data/scout_report_20260303.json",
  "EN": {
    "posting_schedule": [
      {"slot": 1, "time": "09:00 UTC", "category": "portrait", "priority": "high"},
      {"slot": 2, "time": "13:00 UTC", "category": "fashion", "priority": "medium"},
      {"slot": 3, "time": "17:00 UTC", "category": "artistic", "priority": "high"},
      {"slot": 4, "time": "21:00 UTC", "category": "portrait", "priority": "medium"}
    ],
    "content_mix": {
      "portrait": 50,
      "fashion": 25,
      "artistic": 20,
      "trend_reactive": 5
    },
    "hashtag_strategy": {
      "always_use": ["#AIart", "#AIbeauty"],
      "rotate": ["#midjourney", "#stablediffusion", "#aimodel"],
      "trending_today": ["#AIgirl"],
      "max_per_post": 3
    },
    "outbound_strategy": {
      "daily_likes": 30,
      "daily_replies": 10,
      "daily_follows": 5,
      "target_accounts": ["@large_account_1", "@large_account_2"],
      "reply_style": "complimentary, add value, never spammy"
    },
    "ab_test": {
      "variable": "hashtag_count",
      "variant_a": "2 hashtags",
      "variant_b": "5 hashtags",
      "duration_days": 3,
      "start_date": "2026-03-03"
    },
    "key_insights": [
      "Portrait posts with soft lighting outperform by 2.3x",
      "Posts at 17:00 UTC get 40% more engagement than 09:00 UTC",
      "Top competitors average 3.5 posts/day"
    ],
    "risks": [
      "EN market more saturated — 24 competitors vs JP's 15"
    ]
  },
  "JP": {
    "posting_schedule": [
      {"slot": 1, "time": "09:00 JST", "category": "portrait", "priority": "high"},
      {"slot": 2, "time": "12:00 JST", "category": "artistic", "priority": "medium"},
      {"slot": 3, "time": "18:00 JST", "category": "portrait", "priority": "high"},
      {"slot": 4, "time": "21:00 JST", "category": "fashion", "priority": "medium"}
    ],
    "content_mix": {
      "portrait": 55,
      "fashion": 20,
      "artistic": 20,
      "trend_reactive": 5
    },
    "hashtag_strategy": {
      "always_use": ["#AIart", "#aiイラスト"],
      "rotate": ["#AI美女", "#AIgirl", "#AImodel"],
      "trending_today": [],
      "max_per_post": 3
    },
    "outbound_strategy": {
      "daily_likes": 30,
      "daily_replies": 10,
      "daily_follows": 5,
      "target_accounts": ["@jp_large_account_1"],
      "reply_style": "polite Japanese, add value, never spammy"
    },
    "ab_test": {
      "variable": "posting_time",
      "variant_a": "morning_heavy (09:00, 10:00, 12:00, 18:00)",
      "variant_b": "evening_heavy (12:00, 18:00, 20:00, 22:00)",
      "duration_days": 3,
      "start_date": "2026-03-03"
    },
    "key_insights": [
      "JP market has higher avg engagement rate (4.5% vs EN's 3.8%)",
      "Japanese AI beauty content trends toward anime-influenced style",
      "Evening posts (18:00-21:00 JST) perform best in JP"
    ],
    "risks": [
      "Fewer JP competitors to learn from — smaller dataset"
    ]
  }
}
```

### 6.3 `data/pipeline_state_{YYYYMMDD}.json`

```json
{
  "pipeline_date": "2026-03-03",
  "started_at": "2026-03-03T01:00:00+09:00",
  "completed_at": "2026-03-03T01:08:47+09:00",
  "status": "completed",
  "duration_seconds": 527,
  "tasks": [
    {
      "id": "scout_run",
      "agent": "scout",
      "status": "completed",
      "started_at": "2026-03-03T01:00:01+09:00",
      "completed_at": "2026-03-03T01:05:23+09:00",
      "output": "data/scout_report_20260303.json",
      "dependencies": [],
      "notes": "39/41 competitors fetched, 2 skipped (1 protected, 1 suspended)"
    },
    {
      "id": "scout_validation",
      "agent": "marc",
      "status": "completed",
      "started_at": "2026-03-03T01:05:24+09:00",
      "completed_at": "2026-03-03T01:05:24+09:00",
      "output": null,
      "dependencies": ["scout_run"],
      "notes": "All validation checks passed"
    },
    {
      "id": "strategist_run",
      "agent": "strategist",
      "status": "completed",
      "started_at": "2026-03-03T01:05:25+09:00",
      "completed_at": "2026-03-03T01:08:45+09:00",
      "output": "data/strategy_20260303.json",
      "dependencies": ["scout_validation"],
      "notes": "EN + JP strategies generated"
    },
    {
      "id": "strategist_validation",
      "agent": "marc",
      "status": "completed",
      "started_at": "2026-03-03T01:08:46+09:00",
      "completed_at": "2026-03-03T01:08:46+09:00",
      "output": null,
      "dependencies": ["strategist_run"],
      "notes": "All validation checks passed, content_mix sums verified"
    },
    {
      "id": "cross_validation",
      "agent": "marc",
      "status": "completed",
      "started_at": "2026-03-03T01:08:47+09:00",
      "completed_at": "2026-03-03T01:08:47+09:00",
      "output": null,
      "dependencies": ["scout_validation", "strategist_validation"],
      "notes": "No contradictions found"
    }
  ],
  "errors": [],
  "warnings": [
    "2 competitors skipped (protected/suspended)"
  ]
}
```

---

## 7. Authentication

### 7.1 Phase 1 Auth Method

Phase 1 uses **bearer token only** (OAuth 2.0 App-Only / Bearer Token):

| Token | Used By | Purpose |
|---|---|---|
| Bearer Token | Scout (via `x_api.py`) | All read operations (user lookup, timeline fetch, search) |

OAuth 1.0a (Access Token + Access Token Secret) is **NOT used in Phase 1**. It is tested in Phase 0 (`test_x_api.py`) but only needed for write operations starting in Phase 3 (Publisher).

### 7.2 Credential Loading Pattern

```python
import json, os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_credentials() -> dict:
    """Load X API credentials from config/accounts.json."""
    config_path = os.path.join(PROJECT, "config/accounts.json")
    with open(config_path) as f:
        return json.load(f)

def get_bearer_token() -> str:
    """Get bearer token for read-only API access."""
    config = load_credentials()
    return config["x_api"]["bearer_token"]
```

### 7.3 `config/accounts.json` Structure (Phase 1 Relevant Fields)

```json
{
  "x_api": {
    "consumer_key": "...",
    "consumer_secret": "...",
    "bearer_token": "...",
    "accounts": {
      "EN": {
        "handle": "@ai_beauty_en",
        "user_id": "123456789",
        "access_token": "...",
        "access_token_secret": "..."
      },
      "JP": {
        "handle": "@ai_beauty_jp",
        "user_id": "987654321",
        "access_token": "...",
        "access_token_secret": "..."
      }
    }
  }
}
```

Only `bearer_token` is used in Phase 1. The `accounts` section exists for Phase 3+.

### 7.4 `config/competitors.json` Structure

Schema defined in parent spec [Section 10.2](./x-ai-beauty-spec-v2.3.md#102-configcompetitorsjson). Key fields used in Phase 1:

| Field | Type | Used By | Notes |
|---|---|---|---|
| `competitors[].handle` | string | Scout | X handle (with or without `@` — Scout strips `@`) |
| `competitors[].user_id` | string | Scout | Empty on first run; Scout resolves and writes back |
| `competitors[].category` | string | Scout | Content category for grouping |
| `competitors[].market` | string | Scout | `"EN"`, `"JP"`, or `"both"` |
| `tracked_keywords` | string[] | Scout | Keywords for `GET /2/tweets/search/recent` |

---

## 8. Testing Strategy

All Phase 1 tests are **manual via CLI**. No automated test suite, no cron, no CI/CD.

### 8.1 Test Progression

| Step | Command | Pass Criteria |
|---|---|---|
| 1. X API wrapper — resolve 1 handle | `python3 -c "from scripts.x_api import XApiClient; c = XApiClient('...'); print(c.resolve_user_id('JosephinaM3131'))"` | Returns user_id + public_metrics dict |
| 2. X API wrapper — fetch 1 timeline | `python3 -c "from scripts.x_api import XApiClient; c = XApiClient('...'); print(c.get_user_timeline('USER_ID', max_results=5))"` | Returns list of 5 tweet dicts |
| 3. Scout — 1 competitor | `python3 scripts/scout.py --max-competitors 1` | Creates `data/scout_report_{date}.json` with 1 competitor |
| 4. Scout — 5 competitors | `python3 scripts/scout.py --max-competitors 5` | Report contains 5 competitors with valid data |
| 5. Scout — full run | `python3 scripts/scout.py` | Report contains all competitors from config (minus any skipped) |
| 6. Scout — user_id resolution | Check `config/competitors.json` after first run | All accessible accounts have non-empty `user_id` |
| 7. Strategist — standalone | `claude -p "You are the Strategist agent. Read agents/strategist.md for full instructions. Scout report: data/scout_report_{date}.json. Write output to data/strategy_{date}.json." --dangerously-skip-permissions` | Creates valid `strategy_{date}.json` with EN + JP sections |
| 8. Strategist — JSON validation | `python3 -m json.tool data/strategy_{date}.json` | Parses without errors |
| 9. Validate.py — scout mode | `python3 scripts/validate.py scout data/scout_report_{date}.json` | Prints `PASS: All N checks passed.`, exit code 0 |
| 10. Validate.py — strategist mode | `python3 scripts/validate.py strategist data/strategy_{date}.json` | Prints `PASS: All N checks passed.`, exit code 0 |
| 11. Validate.py — cross mode | `python3 scripts/validate.py cross data/scout_report_{date}.json data/strategy_{date}.json` | Prints `PASS`, exit code 0 |
| 12. Pipeline — full run (Marc) | `bash scripts/run_pipeline.sh` | Marc runs Scout → validate → Strategist → validate → cross-check → writes state + log |
| 13. Pipeline — scout-only | `claude -p "You are Marc. Read agents/marc.md. Run Scout only for {date}. Skip Strategist." --dangerously-skip-permissions` | Scout runs + validates, Marc writes pipeline state |
| 14. Pipeline — strategist-only | `claude -p "You are Marc. Read agents/marc.md. Run Strategist only for {date}. Use existing scout report." --dangerously-skip-permissions` | Strategist runs using existing Scout report |
| 15. Pipeline — state check | Inspect `data/pipeline_state_{date}.json` | All tasks show `status: "completed"`, no errors |

### 8.2 Manual Inspection Checklist

After a full pipeline run, manually verify:

- [ ] `data/scout_report_{date}.json` — valid JSON, competitors array populated, market_comparison present
- [ ] `data/strategy_{date}.json` — valid JSON, both EN and JP sections present
- [ ] `data/strategy_current.json` — exists and matches the dated file
- [ ] `data/pipeline_state_{date}.json` — all tasks completed, no errors
- [ ] `logs/pipeline_{date}.log` — timestamps present, no ERROR entries
- [ ] `config/competitors.json` — user_ids populated (after first run)

---

## 9. Exit Criteria

**All of the following must be true before moving to Phase 2**:

| # | Criterion | Verification Method |
|---|---|---|
| 1 | Scout produces valid JSON for all competitors in config | `python3 -m json.tool data/scout_report_{date}.json` + check `competitors_fetched` count |
| 2 | All accessible competitors have resolved `user_id` | Check `config/competitors.json` — no empty `user_id` for accessible accounts |
| 3 | Strategist produces valid strategy JSON | `python3 -m json.tool data/strategy_{date}.json` + check for EN + JP sections |
| 4 | Strategy `content_mix` sums to 100 for each account | Manual check or validation script |
| 5 | Strategy `posting_schedule` has 3-5 slots per account | Manual check |
| 6 | Marc's pipeline runs Scout → Strategist end-to-end | `bash scripts/run_pipeline.sh` completes without errors |
| 7 | Pipeline validation passes for both outputs | `pipeline_state_{date}.json` shows all validations passed |
| 8 | Cross-validation passes | No contradictions logged in pipeline state |
| 9 | Pipeline log shows complete execution | `logs/pipeline_{date}.log` has start + complete entries |
| 10 | user_ids saved to `competitors.json` | Persistent after first run — no re-resolution needed |

---

## 10. Edge Cases & Gotchas

### 10.1 Data Edge Cases

| Issue | Description | Mitigation |
|---|---|---|
| Empty `user_id` on first run | `competitors.json` ships with all `user_id` fields empty | Scout detects empty IDs and runs resolution before data fetch |
| Handle with/without `@` | Config may have `@handle` or `handle` | Always strip `@` before API calls: `handle.lstrip("@")` |
| `followers == 0` | New or empty accounts | Set `engagement_rate = 0.0` to avoid ZeroDivisionError |
| Protected accounts | API returns 401 for protected users | Mark `status: "protected"`, skip, continue with remaining competitors |
| Suspended accounts | API returns user not found / suspended | Mark `status: "suspended"`, skip, continue |
| Empty timeline | Account exists but has 0 tweets | Set `recent_posts: []`, all metrics to 0, continue |

### 10.2 API Edge Cases

| Issue | Description | Mitigation |
|---|---|---|
| Tweepy Response objects | Tweepy returns `Response` objects, not plain dicts | Always normalize via `_normalize_user()` / `_normalize_tweet()` |
| `public_metrics` is None | Some tweet fields may be None | Default to empty dict: `tweet.public_metrics or {}` |
| Rate limit during run | 429 response mid-way through | Wait for `x-rate-limit-reset`, then resume (not restart) |
| Bearer token invalid | Token expired or malformed | Fail fast with clear error message pointing to `config/accounts.json` |

### 10.3 Strategist Edge Cases

| Issue | Description | Mitigation |
|---|---|---|
| Claude wraps JSON in code fences | Output starts with ` ```json ` | Strip markdown code fences before parsing: regex remove ` ```json\n ` and ` ``` ` |
| Claude adds commentary | Text before/after JSON | Extract JSON using brace matching: find first `{`, find matching last `}` |
| Inconsistent schema | Claude changes field names across runs | Skill file includes exact schema with field names |
| Claude refuses or gives disclaimer | Safety-related refusal | Skill file explicitly states this is legitimate competitor analysis |
| Context budget exceeded | Scout report grows beyond ~50 competitors, pushing prompt past 40% of input capacity | Keep prompt minimal (file paths, not contents). If scout report grows large, consider summarizing before passing to Strategist. |

> **Note on context budget**: Harness research identifies 40% of input token capacity as a practical threshold — beyond this, model output quality degrades. Phase 1 mitigates this by using progressive disclosure (Strategist reads files via tool, not via prompt injection) and keeping the scout report at ~41 competitors with 10 posts each. If competitor count grows in later phases, add a summarization step in the pipeline before Strategist invocation.

### 10.4 System Edge Cases

| Issue | Description | Mitigation |
|---|---|---|
| JST vs UTC date mismatch | Running at 00:30 JST = previous day in UTC | Always use JST for date strings in filenames: `datetime.now(ZoneInfo("Asia/Tokyo"))` |
| Concurrent pipeline runs | Two runs started simultaneously | `run_pipeline.sh` checks for existing `.pipeline.lock` file before invoking Marc |
| Disk full | Large reports over time | Not a Phase 1 concern (daily reports are ~50KB each) |
| `claude` CLI not found | Claude Code not in PATH | Pipeline checks `which claude` at startup |

### 10.5 Security Note: `--dangerously-skip-permissions`

Phase 1 uses `--dangerously-skip-permissions` on all `claude -p` invocations (Marc, Strategist subagent). This grants full tool access (bash, file read/write) to each Claude session, meaning:

- Marc can execute arbitrary bash commands and write to any file
- Strategist subagent (spawned by Marc) has the same full access

**Why this is acceptable in Phase 1**: All execution is local, manually triggered by the operator, and the operator monitors output. No cron, no VPS, no unattended execution.

**Phase 5 mitigation**: When deploying to VPS with cron, scope permissions per agent. Consider using Claude Code's permission system to restrict Strategist to file writes only (no bash), and Marc to specific directories and scripts. Track this as a Phase 5 deployment checklist item.

---

*Phase 1 Technical Specification v1.0*
*Date: March 3, 2026*
*Parent: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md)*
