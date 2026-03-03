# X (Twitter) AI Beauty Growth Agent System — Technical Specification v2.4

**Document version**: 2.4
**Date**: March 2, 2026
**Status**: Draft
**Related documents**: [Product Requirements Document v1.1](./x-ai-beauty-prd-v1.md), [Compliance Review](./x-developer-terms-compliance-review.md)

> **Project**: AI Beauty account — reach 10,000 followers as fast as possible
> **Accounts**: EN (global market) + JP (日本市場) — A/B test to determine which language fits the AI strategy
> **Post frequency**: 3-5 posts/day per account
> **Media**: AI-generated still images only (prepared by human)
> **Automation method**: X API v2 (Basic $200/month) + Playwright (impression scraping only)
> **Interface**: Telegram Bot
>
> **Changes from v2.3**:
> - ✅ Removed duplicate Section 17 (Risk Management) — identical to Section 8
> - ✅ Added inline compliance warnings (⚠️) for likes, follows, replies, and Playwright per compliance review
> - ✅ Added Marc to Section 1 textual agent list
> - ✅ Migrated `global_rules.json` → `global_rules.md` (Markdown format for CLAUDE.md native loading)
> - ✅ Fixed Section 16.1 title: "Phase 0" → "Phase 5" (VPS deployment is Phase 5)
> - ✅ Added `aiosqlite` to deployment dependencies
> - ✅ Added OAuth 1.0a vs 2.0 clarification in Section 9.1
> - ✅ Fixed Analyst API usage calculation in Section 2.2 (1,200 → 1,320)
> - ✅ Added SQLite schema constraints (PRIMARY KEY, NOT NULL, defaults)
> - ✅ Added impressions NULL handling comment and API-only proxy formula
> - ✅ Added `flock`-based locking recommendation for Phase 5 cron deployment
> - ✅ Added CLAUDE_MODEL per-agent override comment in Section 12
> - ✅ Added cross-reference to compliance review document
> - ✅ Fixed Playwright risk language from "low-risk" to explicit risk acknowledgment

---

## 1. System Overview

### Agent Hierarchy

```
Human (Shimpei)
└── Telegram (all communication unified through Marc)
    └── 🎖️ Marc (COO / Orchestrator / Reporter)
        │
        ├── 🔍 Scout ──────── Competitor research & trend analysis
        ├── 📊 Strategist ─── Data analysis & growth strategy
        ├── ✍️ Creator ─────── Content planning & image prompts
        ├── 📢 Publisher ──── X API posting & outbound engagement
        └── 📈 Analyst ────── Metrics collection & data storage
```

The system consists of 6 agents: **Marc** (COO/Orchestrator), **Scout** (research), **Strategist** (strategy), **Creator** (content), **Publisher** (posting & outbound), and **Analyst** (metrics). Marc coordinates all other agents and is the sole communication channel with the human.

### Daily Operation Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Scout   │───▶│Strategist│───▶│ Creator  │
│ research │    │ strategy │    │ content  │
└──────────┘    └──────────┘    └──────────┘
                                      │
      ┌──── 🎖️ Marc monitors, coordinates, & reports ────┐
      │                                                    │
      │                                              [Telegram]
      │                                              Morning brief
      │                                              Alerts & reports
      │                                              Command processing
      │                                                    │
      │                                               [HUMAN]
      │                                           Media prep & approval
      │                                                    │
┌──────────┐    ┌──────────┐    ┌──────────┐              │
│ Analyst  │◀───│Publisher │◀───│  Marc    │◀─────────────┘
│ metrics  │    │post &    │    │receives  │
└────┬─────┘    │outbound  │    │approval, │
     │          └──────────┘    │instructs │
     │                          │downstream│
     └──▶ [Shared State DB] ──▶ └──────────┘ ──▶ Next day's Strategist
```

---

## 2. X API Strategy

### 2.1 Plan Selection: Basic ($200/month)

| Item | Basic Plan Spec | Projected Usage | Headroom |
|---|---|---|---|
| Read (tweets consumed) | 15,000/month | ~10,700/month | ✅ ~30% buffer |
| Write (posts/actions) | 50,000/month | ~3,000/month | ✅ Large buffer |
| Monthly cost | $200 ($175 with annual) | — | — |

### 2.2 Monthly Usage Breakdown

**Write operations (~3,000/month)**:

| Operation | Calculation | Monthly volume |
|---|---|---|
| Posts | 3-5 posts × 2 accounts × 30 days | 180-300 |
| Likes | 30 × 2 accounts × 30 days | 1,800 |
| Replies | 10 × 2 accounts × 30 days | 600 |
| Follows | 5 × 2 accounts × 30 days | 300 |
| **Total** | | **~2,460-3,000** |

> **Note**: Budget calculated at max (5 posts/day). Actual usage will be 3-5 posts/day per account.

**Read operations (~10,700/month)**:

| Operation | Calculation | Monthly volume |
|---|---|---|
| Competitor timeline fetching (Scout) | 10 accounts × 30 posts × 30 days | 9,000 |
| Own post metrics (Analyst) | ~22 requests/run × 2 runs/day × 30 days | 1,320 |
| User info lookups | Various | ~500 |
| **Total** | | **~10,820** |

> **Buffer**: ~28% headroom against 15,000/month read limit.

### 2.3 Hybrid Strategy: API vs Playwright

| Operation | Method | Reason |
|---|---|---|
| Post (text + image) | ✅ **X API** | Official, stable, zero BAN risk |
| Like | ✅ **X API** | Official, rate limit: 1,000/24h. ⚠️ X Terms risk — see compliance review |
| Reply | ✅ **X API** | Official. ⚠️ X Terms risk — see compliance review |
| Follow | ✅ **X API** | Official. ⚠️ X Terms risk — see compliance review |
| Own account public_metrics | ✅ **X API** | likes/RT/replies/quotes/bookmarks |
| Competitor timeline fetching | ✅ **X API** | User timeline endpoint |
| Impression count | ⚠️ **Playwright** | Basic plan cannot access `non_public_metrics`. Scrape own post detail pages only. ⚠️ Carries X Terms risk (see compliance review). Risk accepted for impression data value. |

> For full X Developer Terms compliance analysis, see [`x-developer-terms-compliance-review.md`](./x-developer-terms-compliance-review.md).

### 2.4 API Rate Limits

| Endpoint | Rate Limit (Basic) | Our Usage | Status |
|---|---|---|---|
| POST /2/tweets (post) | 300/3 hours (app-wide) | ~5/day per account | ✅ Plenty of room |
| POST /2/users/:id/likes (like) | 1,000/24 hours (app-wide) | ~60/day total | ✅ Plenty of room |
| GET /2/users/:id/tweets (timeline) | 1,500/15 min | ~30/day | ✅ Plenty of room |
| GET /2/tweets/search/recent (search) | 450/15 min | ~5/day | ✅ Plenty of room |

### 2.5 Metrics Limitation & Workaround

**Available with Basic (`public_metrics`)**:
```json
{
  "like_count": 245,
  "retweet_count": 18,
  "reply_count": 12,
  "quote_count": 3,
  "bookmark_count": 8
}
```

**NOT available with Basic (`non_public_metrics` — requires Pro at $5,000/month)**:
```json
{
  "impression_count": 12500,
  "url_link_clicks": 340,
  "user_profile_clicks": 89
}
```

**Workaround**: Impression counts are scraped via Playwright from our own account's post detail pages only. This carries X Terms risk as non-API automation is prohibited (see compliance review, Issue 4). Risk accepted for the value of impression data. If we upgrade to Pro later, this can be fully replaced with API calls.

---

## 3. Agent Roster (6 Agents)

### Agent 0: 🎖️ Marc (COO / Orchestrator / Reporter)

| Item | Details |
|---|---|
| **Role** | Overall orchestration, decision-making, inter-agent coordination, escalation, **all human communication** |
| **Trigger** | Pipeline start (daily 0:30 AM) + scheduled reports (7:00 AM, 23:30) + real-time Telegram command processing |
| **Input** | All agent outputs, human Telegram messages, metrics DB |
| **Output** | Instructions to each agent, Telegram reports/briefs/alerts, escalation notifications |

**Why Marc owns reporting**: Marc holds full orchestration context from War Room reviews — what succeeded, what failed, what stalled, what needs human decision. A separate Reporter would need the same context re-loaded, producing a worse report with less judgment at additional API cost. Reporting to the human is the communication layer of orchestration, not a separate domain.

**Specific tasks**:

1. **Pipeline execution control**
   - Invoke each agent in sequence
   - Evaluate success/failure of each step → proceed / abort / retry
   - Manage dependencies (Scout → Strategist → Creator order guarantee)
   - Log execution to `logs/pipeline_{date}.log`

2. **War Room (full review)** — daily at 6:00 AM
   - Cross-review all agent outputs
   - Detect inconsistencies (e.g., Strategist says "4 posts/day" but Creator only produced 3)
   - Quality check (Creator's post text aligns with strategy)
   - If issues found → send back to the relevant agent or escalate to human

3. **Telegram reporting** (formerly Reporter agent)
   - **Morning brief (7:00 AM JST)**: Yesterday's results, today's plan, action items, strategy highlights
   - **Daily report (23:30 JST)**: Full performance details, outbound results, EN vs JP comparison, error summary, tomorrow's preview
   - **Instant alerts**: Error notifications, follower anomalies, pipeline halts
   - **Content preview (3:00 AM JST)**: Early notification of drafted content for optional pre-review
   - All reports include Marc's judgment: what to highlight, what to deprioritize, what decisions need human input

   **Morning brief format**:
   ```
   📊 AI Beauty Daily Brief — Mar 1, 2026

   ━━━ YESTERDAY'S RESULTS ━━━
   🇺🇸 EN: +47 followers (total: 1,234)
      Best post: 2.4K likes, 5.2% ER
      Outbound: 30 likes, 10 replies, 5 follows
   🇯🇵 JP: +62 followers (total: 987)
      Best post: 1.8K likes, 6.1% ER
      Outbound: 30 likes, 10 replies, 5 follows

   ━━━ TODAY'S PLAN ━━━
   EN: 4 posts (09:00/13:00/17:00/21:00 UTC)
   JP: 4 posts (09:00/12:00/18:00/21:00 JST)

   ⚡ ACTION REQUIRED:
   • 8 posts need approval
   • 8 image prompts ready

   ━━━ STRATEGY UPDATE ━━━
   • JP outperforming EN by 32% in ER
   • Soft-lighting portraits → 2.3x avg engagement
   • A/B test result: 2 hashtags > 5 hashtags

   📎 Commands:
   /approve — approve all posts
   /approve 1,3,5 — approve specific posts
   /details — full content plan
   /status — pipeline status
   ```

4. **Telegram command interpretation & routing**
   - Parse human commands and route to appropriate agents:
     - `/approve` → Update all posts to `approved` status
     - `/approve 1,3,5` → Approve specific posts only
     - `/edit 3 "change the caption to..."` → Instruct Creator to revise
     - `/pause` → Halt Publisher's automated posting
     - `/strategy "increase portrait ratio"` → Relay directive to Strategist
     - `/status` → Report current pipeline state
   - Handle ambiguous instructions using context (e.g., "the third one looks off" → identify post #3 and route to Creator)

5. **Error handling & escalation**
   - **Auto-resolve**: Timeout → retry (max 3 attempts)
   - **Auto-resolve + notify**: API rate limit → wait and re-execute, notify human
   - **Immediate halt + escalate**: Playwright selector error → possible UI change, halt all automated posting, notify human immediately
   - **Immediate escalate**: Auth error → possible token expiry, notify human immediately

6. **Daily retrospective & rule updates**
   - Classify errors that occurred today
   - Add recurring patterns to `config/global_rules.md` as new rules
   - Propose improvements to agent skill files

**Marc's decision logic examples**:
```
IF Scout fails to fetch competitor data:
  → API error? → Retry after 5 minutes
  → Account went private? → Propose removal from competitor list, ask human

IF Creator output is inconsistent with strategy:
  → Post category ratio deviates ±15% from strategy → Instruct Creator to regenerate
  → Hashtags differ from strategy → Auto-correct and pass through

IF Publisher posting fails:
  → Image upload error → Validate image file → Retry or notify human
  → Duplicate tweet error → Skip and log
  → Auth error → Halt all posting, escalate to human

IF Analyst detects anomalous metrics:
  → Follower drop >10% → Urgent notification to human
  → Engagement rate <50% of previous week → Instruct Strategist to run emergency review
```

---

### Agent 1: 🔍 Scout (Research Agent)

| Item | Details |
|---|---|
| **Role** | Competitor analysis & trend research |
| **Trigger** | Daily 1:00 AM (invoked by Marc) |
| **Input** | `config/competitors.json`, previous analysis data |
| **Output** | `data/scout_report_{date}.json` |
| **X API endpoints** | `GET /2/users/by/username/:username`, `GET /2/users/:id/tweets`, `GET /2/tweets/search/recent` |

**Specific tasks**:

1. **Competitor data collection** (X API v2)
   - `GET /2/users/by/username/:username` → User info (follower count etc.)
   - `GET /2/users/:id/tweets` → Recent posts (tweet.fields=public_metrics,created_at)
   - Collect public_metrics for each post (likes, RT, replies, quotes, bookmarks)
   - Daily follower count snapshots

2. **Viral post analysis**
   - Sort by engagement rate, identify top 20 posts
   - Extract common patterns:
     - Post text structure (character count, hashtags, CTA presence)
     - Image style (composition, color tone, subject characteristics from image URLs)
     - Posting time distribution
     - Comment sentiment trends

3. **Trend research** (X API v2)
   - `GET /2/tweets/search/recent` with AI Beauty related keywords
   - Discover new competitor / noteworthy accounts

**Output format**:
```json
{
  "date": "2026-03-01",
  "competitors": [
    {
      "handle": "@example_account",
      "user_id": "123456789",
      "followers": 45200,
      "followers_change_7d": 1200,
      "avg_posts_per_day": 4.2,
      "top_posts": [
        {
          "tweet_id": "1234567890",
          "url": "https://x.com/example_account/status/1234567890",
          "text": "...",
          "public_metrics": {
            "like_count": 2400,
            "retweet_count": 180,
            "reply_count": 95,
            "quote_count": 12,
            "bookmark_count": 45
          },
          "posted_at": "2026-02-28T14:30:00Z",
          "image_urls": ["https://pbs.twimg.com/..."],
          "image_description": "close-up portrait, soft lighting, pastel background...",
          "hashtags": ["#AIart", "#AIbeauty"],
          "engagement_rate": 0.059
        }
      ],
      "posting_time_distribution": {"9-12": 15, "12-15": 25, "15-18": 30, "18-21": 20, "21-24": 10},
      "content_categories": {"portrait": 60, "fashion": 20, "artistic": 15, "meme": 5}
    }
  ],
  "trending_topics": ["..."],
  "trending_posts": ["..."],
  "new_accounts_discovered": ["@new_competitor"]
}
```

**API usage per Scout run**: ~45 Read requests/day → ~1,350/month

---

### Agent 2: 📊 Strategist (Strategy Agent)

| Item | Details |
|---|---|
| **Role** | Data-driven growth strategy formulation & daily updates |
| **Trigger** | Daily 1:30 AM (invoked by Marc after Scout completes) |
| **Input** | Scout report, Analyst metrics data, current strategy |
| **Output** | `data/strategy_current.json` (latest), `data/strategy_{date}.json` (archive) |

**Specific tasks**:

1. **Performance analysis**
   - Evaluate yesterday's post performance for own accounts
   - Comparative analysis vs competitors (engagement rate, follower growth rate)
   - EN vs JP account performance comparison

2. **Strategy document update**
   - Optimal posting times (derived from own + competitor data)
   - Content mix ratio adjustment (portrait / fashion / artistic etc.)
   - Hashtag strategy update (identify high-performing tags)
   - Outbound engagement policy update (target accounts, reply style)

3. **A/B test design**
   - Design tests with different approaches for EN vs JP
   - Evaluate previous test results, propose next test

**Output format**:
```json
{
  "date": "2026-03-01",
  "account": "EN",
  "posting_schedule": [
    {"slot": 1, "time": "09:00 UTC", "category": "portrait", "priority": "high"},
    {"slot": 2, "time": "13:00 UTC", "category": "fashion", "priority": "medium"},
    {"slot": 3, "time": "17:00 UTC", "category": "artistic", "priority": "high"},
    {"slot": 4, "time": "21:00 UTC", "category": "portrait", "priority": "medium"}
  ],
  "content_mix": {"portrait": 50, "fashion": 25, "artistic": 20, "trend_reactive": 5},
  "hashtag_strategy": {
    "always_use": ["#AIart", "#AIbeauty"],
    "rotate": ["#midjourney", "#stablediffusion", "#aimodel"],
    "trending_today": ["#AIgirl"]
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
    "duration_days": 3
  },
  "key_insights": [
    "Portrait posts with soft lighting outperform by 2.3x",
    "Posts at 17:00 UTC get 40% more impressions than 09:00 UTC",
    "JP account growing 15% faster than EN this week"
  ]
}
```

---

### Agent 3: ✍️ Creator (Content Planning Agent)

| Item | Details |
|---|---|
| **Role** | Daily post content drafting & image prompt creation |
| **Trigger** | Daily 2:00 AM (invoked by Marc after Strategist completes) |
| **Input** | Today's strategy, competitor analysis, past high-performing posts |
| **Output** | `data/content_plan_{date}_{account}.json` |

**Specific tasks**:

1. **Post text creation** (EN and JP separately)
   - Draft post copy for each scheduled slot following the strategy
   - Reference viral post patterns while maintaining originality
   - Apply hashtag strategy
   - Include CTA (e.g., "Follow for more", "RT if you agree")
   - ⚠️ Never start a post with `@` (X treats it as a reply, hiding it from followers' feeds)

2. **Image prompt / brief creation**
   - Detailed AI image prompts for each post (Midjourney / Stable Diffusion format)
   - Style references (describe visual style of competitor viral posts)
   - Aspect ratio specification (X optimal: 16:9 or 4:3)
   - Color tone, mood, subject specification

3. **Reply template creation** (for outbound engagement)
   - Create 5-10 reply templates for Publisher to use
   - Natural language matching target account content styles
   - Varied wording to avoid appearing spammy

4. **Post status management**
   - Create each post with `draft` status
   - Status flow: `draft → approved → media_ready → scheduled → posted → measured`

**Output format**:
```json
{
  "date": "2026-03-01",
  "account": "EN",
  "posts": [
    {
      "id": "en_20260301_01",
      "slot": 1,
      "scheduled_time": "09:00 UTC",
      "status": "draft",
      "text": "She's not real, but the feeling is ✨\n\nSoft light. Gentle gaze. Pure AI magic.\n\n#AIbeauty #AIart",
      "image_prompt": {
        "tool": "midjourney",
        "prompt": "portrait of a young woman, soft natural lighting, golden hour, pastel pink background, gentle expression, photorealistic, 8k, --ar 16:9 --v 6",
        "style_reference": "Similar to @competitor's top post (soft focus, warm tones)",
        "aspect_ratio": "16:9"
      },
      "category": "portrait",
      "hashtags": ["#AIbeauty", "#AIart", "#midjourney"],
      "ab_test_variant": "A"
    }
  ],
  "reply_templates": [
    {"id": "rt_01", "text": "This is incredible work! The lighting is perfect 🔥", "use_for": "compliment on AI art posts"},
    {"id": "rt_02", "text": "Love the composition here. What tool did you use?", "use_for": "engagement question"}
  ]
}
```

---

### Agent 4: 📢 Publisher (Posting & Outbound Agent)

| Item | Details |
|---|---|
| **Role** | Execute approved content posting & outbound engagement |
| **Trigger** | Each scheduled post time (4-5 times/day) + outbound distributed throughout the day |
| **Input** | Posts with `media_ready` status, outbound strategy, reply templates |
| **Output** | Post status updates, outbound logs |
| **X API endpoints** | `POST /2/tweets`, `POST /2/users/:id/likes`, `POST /2/users/:id/following`, `POST /1.1/media/upload.json` |

**Specific tasks**:

1. **Post execution** (X API v2)
   - Fetch posts with `media_ready` status
   - Image upload: `POST /1.1/media/upload.json` (media upload remains on v1.1)
   - Create post: `POST /2/tweets` with `media.media_ids` parameter
   - Record post URL, update status to `posted`
   - ⚠️ Use separate OAuth tokens for EN / JP (account isolation)

2. **Outbound engagement** (X API v2)
   - **Like**: `POST /2/users/:id/likes` — target posts specified by strategy
   - **Reply**: `POST /2/tweets` (with `in_reply_to_tweet_id`) — using Creator's templates
   - **Follow**: `POST /2/users/:id/following` — accounts specified by strategy
   - ⚠️ Insert human-like random delays between operations (30-120 seconds random wait)
   - ⚠️ Strictly enforce daily operation limits (see below)
   - ⚠️ **Compliance note**: Automated likes, follows, and cold replies carry X Terms risk. See [`x-developer-terms-compliance-review.md`](./x-developer-terms-compliance-review.md) Issues 1-3. Risk accepted — implement with awareness; monitor for enforcement changes.

3. **Rate limit management**
   - Track operation counts in `data/rate_limits_{date}.json`
   - Check counter before each operation → auto-stop when limit reached

**Daily operation limits (per account)**:
```
Posts:     5/day    (API limit: 300/3h = plenty of room)
Likes:    30/day    (API limit: 1,000/24h = plenty of room)
Replies:  10/day    (counts toward post limit)
Follows:   5/day    (set conservatively — aggressive following causes BAN)
```

**All operations via X API (no Playwright needed for posting/engagement)**:
```
Post creation    → X API v2 (POST /2/tweets)              ✅ Safe
Image upload     → X API v1.1 (POST media/upload)          ✅ Safe
Like             → X API v2 (POST /2/users/:id/likes)      ⚠️ X Terms risk accepted — see compliance review
Reply            → X API v2 (POST /2/tweets + reply_to)    ⚠️ X Terms risk accepted — see compliance review
Follow           → X API v2 (POST /2/users/:id/following)   ⚠️ X Terms risk accepted — see compliance review
```

---

### Agent 5: 📈 Analyst (Metrics & Analytics Agent)

| Item | Details |
|---|---|
| **Role** | Post performance measurement & data accumulation |
| **Trigger** | Daily 23:00 (end of day) + 6h/24h after each post |
| **Input** | Posts with `posted` status (tweet_id) |
| **Output** | `data/metrics_{date}_{account}.json`, `data/metrics_history.db` (SQLite) |
| **X API endpoints** | `GET /2/tweets/:id` (tweet.fields=public_metrics), `GET /2/users/:id` (user.fields=public_metrics) |
| **Playwright** | Scrape impression counts from own account's post detail pages |

**Specific tasks**:

1. **Post metrics collection**
   - **X API** (public_metrics): `GET /2/tweets/:id?tweet.fields=public_metrics`
     - Likes, retweets, replies, quotes, bookmarks
   - **Playwright** (non_public_metrics workaround): Log into own account, access post detail page
     - Scrape impression count
     - Own posts only (minimal risk)
   - Take snapshots at 6 hours and 24 hours after posting

2. **Account metrics collection** (X API)
   - `GET /2/users/:id?user.fields=public_metrics`
   - Follower count, following count, post count (daily snapshot)

3. **Data storage & analysis**
   - Store all metrics in SQLite database
   - Calculate daily summaries (avg engagement rate, follower delta, best-performing post)
   - EN vs JP comparison data

**Database schema (SQLite)**:
```sql
-- Post metrics
CREATE TABLE post_metrics (
    post_id TEXT NOT NULL,
    tweet_id TEXT NOT NULL,
    account TEXT NOT NULL,                -- 'EN' or 'JP'
    measured_at DATETIME NOT NULL,
    hours_after_post INTEGER NOT NULL,    -- 6 or 24
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    quotes INTEGER DEFAULT 0,
    bookmarks INTEGER DEFAULT 0,
    impressions INTEGER,                  -- From Playwright (NULL when unavailable)
    engagement_rate REAL,                 -- (likes+RT+replies+quotes) / impressions; NULL when impressions is NULL
    source TEXT NOT NULL,                 -- 'api' or 'playwright'
    PRIMARY KEY (post_id, measured_at)
);
-- engagement_rate is NULL when impressions is NULL.
-- Fallback proxy: (likes+RT+replies+quotes) / followers as API-only estimate.

-- Account metrics
CREATE TABLE account_metrics (
    account TEXT NOT NULL,
    date DATE NOT NULL,
    followers INTEGER,
    following INTEGER,
    total_posts INTEGER,
    followers_change INTEGER,             -- vs previous day
    PRIMARY KEY (account, date)
);

-- Outbound log
CREATE TABLE outbound_log (
    date DATE NOT NULL,
    account TEXT NOT NULL,
    action_type TEXT NOT NULL,            -- 'like', 'reply', 'follow'
    target_handle TEXT,
    target_tweet_id TEXT,
    success BOOLEAN NOT NULL DEFAULT 1,
    api_response_code INTEGER
);

-- Error log
CREATE TABLE error_log (
    timestamp DATETIME NOT NULL,
    agent TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT,
    resolution TEXT,                      -- 'auto_retry', 'escalated', 'ignored'
    resolved BOOLEAN NOT NULL DEFAULT 0
);
```

**API usage per Analyst run**: ~22 Read requests/run × 2 runs/day → ~1,320/month

---

## 4. Shared State Architecture

```
project/
├── config/
│   ├── competitors.json          ← Human-managed competitor list
│   ├── accounts.json             ← EN/JP account settings & API tokens
│   ├── global_rules.md            ← Cross-agent rules (accumulated from failures, Markdown format)
│   └── telegram_config.json      ← Telegram Bot settings
│
├── data/
│   ├── scout_report_{date}.json
│   ├── strategy_current.json     ← Latest strategy (always overwritten)
│   ├── strategy_{date}.json      ← Strategy archive
│   ├── content_plan_{date}_{account}.json
│   ├── metrics_{date}_{account}.json
│   ├── metrics_history.db        ← SQLite (all metrics time-series)
│   ├── rate_limits_{date}.json   ← API rate limit counters
│   └── pipeline_state_{date}.json ← Task-based agent coordination state (see Section 14.4)
│
├── docs/                         ← Project documentation
│   ├── specs/                    ← Spec, PRD, compliance review
│   │   ├── x-ai-beauty-spec-v2.3.md
│   │   ├── x-ai-beauty-prd-v1.md
│   │   └── x-developer-terms-compliance-review.md
│   ├── context.md, phase-0-runbook.md, review.md
│   └── autonomous-agent-system-analysis.md
│
├── media/
│   ├── pending/                  ← Human places images here
│   │   ├── en_20260301_01.png
│   │   └── jp_20260301_01.png
│   └── posted/                   ← Posted image archive
│
├── logs/
│   ├── pipeline_{date}.log       ← Marc's pipeline execution log
│   ├── outbound_{date}.log       ← Outbound operation log
│   └── errors_{date}.log         ← Error log
│
├── agents/                       ← Claude Code subagent definition files
│   ├── marc.md                   ← COO / Orchestrator / Reporter
│   ├── scout.md
│   ├── strategist.md
│   ├── creator.md
│   ├── publisher.md
│   └── analyst.md
│
├── scripts/
│   ├── orchestrator.sh           ← cron → launches Marc (full system, Phase 5+)
│   ├── run_pipeline.sh           ← Phase 1 entry point (thin wrapper → Marc)
│   ├── validate.py               ← Deterministic validation (scout/strategist/cross)
│   ├── x_api.py                  ← X API v2 wrapper library
│   ├── media_upload.py           ← Image upload (v1.1 media/upload)
│   ├── playwright_metrics.py     ← Impression scraping (Playwright)
│   ├── telegram_bot.py           ← Telegram Bot (always-on daemon)
│   └── db_manager.py             ← SQLite management utility
│
├── backups/                      ← Daily backups
│
└── browser_profiles/
    ├── en_profile/               ← EN account Playwright profile (impression scraping only)
    └── jp_profile/               ← JP account Playwright profile
```

### Post Status Flow (Lifecycle)

```
draft ──▶ approved ──▶ media_ready ──▶ scheduled ──▶ posted ──▶ measured
  │          │              │              │            │           │
Creator    Human sends  Human places    Marc         Publisher   Analyst
creates    /approve     image in        instructs    posts via   collects
           via          media/pending/  Publisher    X API       metrics
           Telegram     & notifies Marc to post
```

---

## 5. Daily Pipeline Schedule

```
TIME (JST)    AGENT          ACTION                                METHOD
─────────────────────────────────────────────────────────────────────────
 0:30 AM      🎖️ Marc        Pipeline start, health check          Claude Code
 1:00 AM      🔍 Scout       Competitor scraping & trend research   X API v2
 1:30 AM      📊 Strategist  Strategy update                        Claude Code
 2:00 AM      ✍️ Creator     Content drafting & image prompts       Claude Code
 2:30 AM      🎖️ Marc        War Room (lite): output consistency    Claude Code
 3:00 AM      🎖️ Marc        Content preview to Telegram            Telegram API
 6:00 AM      🎖️ Marc        War Room (full): comprehensive review  Claude Code
 7:00 AM      🎖️ Marc        Morning brief to Telegram              Telegram API
 7:00-9:00    HUMAN          Approve posts & prepare images → media/pending/
 9:00         🎖️ Marc        Confirm approval → instruct Publisher
 9:00         📢 Publisher   Post #1 (EN + JP)                      X API v2
10:00-18:00   📢 Publisher   Outbound engagement (distributed)      X API v2
12:00-13:00   📢 Publisher   Post #2 (EN + JP)                      X API v2
15:00         📈 Analyst     6h post-publish metrics collection     X API + Playwright
17:00-18:00   📢 Publisher   Post #3 (EN + JP)                      X API v2
21:00         📢 Publisher   Post #4 (EN + JP)                      X API v2
23:00         📈 Analyst     24h metrics + account snapshot         X API + Playwright
23:30         🎖️ Marc        Daily report to Telegram                Telegram API
23:45         🎖️ Marc        Daily retrospective & rule updates     Claude Code
─────────────────────────────────────────────────────────────────────────
```

---

## 6. Technical Requirements

### Required Components

| Component | Technology | Purpose |
|---|---|---|
| **Scheduler** | crontab | Pipeline triggers + per-post time triggers |
| **Agent execution** | Claude Code CLI (`claude -p`) | Thinking, analysis, content generation |
| **X API** | X API v2 + v1.1 (media) | Posting, likes, replies, follows, metrics |
| **Browser automation** | Playwright (Python) | Impression scraping only |
| **Data storage** | SQLite + JSON files | Metrics accumulation & inter-agent data sharing |
| **Notifications** | python-telegram-bot + Claude API | Telegram Bot |
| **Runtime environment** | VPS (recommended) | 24/7 always-on |

### Monthly Cost Estimate

| Item | Monthly Cost |
|---|---|
| X API Basic | $200 |
| VPS (2 vCPU / 4 GB) | $10-20 |
| Claude Pro/Max subscription | $20-100 |
| Telegram Bot | $0 (free) |
| **Total** | **$230-320/month** |

### Recommended VPS Specs

```
OS:     Ubuntu 24.04 LTS
CPU:    2 vCPU
RAM:    4 GB
SSD:    40 GB
Cost:   ~$10-20/month (Hetzner, Vultr, etc.)

Required software:
- Node.js 22+ (Claude Code)
- Python 3.11+ (X API client, Playwright, Telegram Bot)
- Playwright + Chromium (impression scraping only)
- SQLite3
```

---

## 7. Implementation Phases

### Development Philosophy: Local First, Deploy Later

All development and testing happens on your own machine. You trigger agents from your CLI, inspect outputs, iterate skill files. A VPS is only needed when the system is ready to run autonomously — executing tasks overnight while you sleep.

```
Phases 0-4 (your machine):   CLI → claude -p → inspect → iterate skill files
Phase 5 (VPS deployment):    Provision VPS → copy project → install cron → system runs itself
Phase 6 (autonomous):        Agents operate overnight. You review via Telegram in the morning.
```

### Phase 0: Local Development Setup (Day 1-2)
- [ ] Node.js 22+ and Claude Code installed & authenticated
- [ ] Python 3.11+ with virtual environment and dependencies
- [ ] X Developer Account registration & Basic plan ($200/month)
- [ ] X API key/token generation (for both EN & JP accounts)
- [ ] Telegram Bot creation & test
- [ ] Playwright browser profiles (EN & JP)
- [ ] Project directory structure creation
- [ ] SQLite database initialization
- [ ] CLAUDE.md memory files creation
- [ ] Competitor account list (`config/competitors.json`)

**Detailed steps**: See [Phase 0 Runbook](../phase-0-runbook.md)

### Phase 1: Scout + Strategist + Marc Foundation (Day 3-5)
- [ ] X API wrapper (`x_api.py`) development
- [ ] Scout agent skill file — build, manually trigger, inspect output, iterate
- [ ] Strategist agent skill file — build, manually trigger with Scout's output, iterate
- [ ] Marc foundation — manually trigger pipeline: Scout → validate → Strategist → validate
- [ ] Marc's Telegram reporting: manually trigger morning brief + daily report
- [ ] First real competitor analysis & growth strategy document

**Manual testing pattern**:
```bash
# Test Scout in isolation
claude -p "$(cat agents/scout.md) Analyze all competitors in config/competitors.json." \
  --dangerously-skip-permissions

# Inspect output
cat data/scout_report_$(date +%Y%m%d).json | python3 -m json.tool

# Test Strategist with Scout's real output
claude -p "$(cat agents/strategist.md) Generate growth strategy based on today's scout report." \
  --dangerously-skip-permissions
```

### Phase 2: Creator + Telegram Command Processing (Day 6-8)
- [ ] Creator agent skill file — build, manually trigger with Strategist's output, iterate
- [ ] Telegram Bot command processing implementation (/approve, /status, etc.)
- [ ] Marc's Telegram command interpretation & routing logic
- [ ] Morning brief delivery test with real content plan
- [ ] End-to-end manual test: Scout → Strategist → Creator → Marc brief

### Phase 3: Publisher + X API Posting (Day 9-12)
- [ ] Image upload (media/upload v1.1) implementation & test
- [ ] Post creation (POST /2/tweets) implementation & test
- [ ] Outbound engagement (likes/replies/follows) implementation & test
- [ ] Rate limit management implementation
- [ ] EN / JP account isolation verification
- [ ] First real posts published (manually triggered)

### Phase 4: Analyst + Full Integration (Day 13-16)
- [ ] Analyst agent skill file — build, manually trigger, iterate
- [ ] Playwright impression scraping implementation & test
- [ ] SQLite data accumulation verification
- [ ] Marc's War Room functionality — manually trigger full pipeline review
- [ ] Error handling & escalation notification verification
- [ ] Full manual end-to-end: Scout → Strategist → Creator → [human approval] → Publisher → Analyst
- [ ] Run the full pipeline manually for 2-3 consecutive days to verify reliability

**Phase 4 exit criteria**: All 6 agents produce correct outputs when triggered manually. No intervention needed beyond normal human approval. Ready for deployment.

### Phase 5: VPS Deployment (Day 17-18)
- [ ] Provision VPS (recommended: Vultr Tokyo, $12/month, 2 vCPU / 4 GB RAM / Ubuntu 24.04)
- [ ] Server hardening (service user, SSH keys, firewall, timezone JST)
- [ ] Install Node.js 22+, Claude Code, Python 3.11+, Playwright
- [ ] Copy project directory from local machine to VPS
- [ ] Verify all API credentials work from VPS
- [ ] Install cron with orchestrator script (`orchestrator.sh` — supersedes Phase 1's `run_pipeline.sh`)
- [ ] Run health check on VPS

**Detailed steps**: See [Deployment Procedure (Section 16)](#16-deployment-procedure)

### Phase 6: Autonomous Operation (Day 19+)
- [ ] Enable cron agent jobs — first fully autonomous overnight pipeline
- [ ] Monitor for 3 days: review every log, verify every output
- [ ] First week: review logs daily, add rules to `config/global_rules.md`
- [ ] EN vs JP performance comparison data accumulation
- [ ] Strategist auto-update accuracy improvement
- [ ] Marc's decision logic refinement (based on real error patterns)
- [ ] Posting time optimization (based on Analyst data)
- [ ] Weekly tool/skill review (Section 14.6)

---

## 8. Risk Management

| Risk | Severity | Mitigation |
|---|---|---|
| X API rate limit exceeded | Temporary feature halt | Rate limit counter enforced strictly. Marc auto-waits and retries |
| X API token expiry | Full system halt | Marc detects auth errors, immediate escalation. Token refresh reminders |
| X UI change (Playwright) | Impression scraping breaks | Impression scraping is "nice to have". Core functionality unaffected |
| Claude API cost overrun | Budget exceeded | Daily token usage logging. Marc detects abnormal usage and notifies |
| Low-quality content posted | Brand damage | Human approval flow mandatory. Marc consistency checks. Auto-posting only considered after Phase 5 |
| Account BAN from outbound | Account suspension | All engagement via official API (greatly reduced risk). Conservative operation limits |
| VPS outage | Full system halt | Regular data backup (SQLite + config). Marc health check notifications |
| Monthly Read cap exceeded | Read functions halted | Marc tracks API usage, auto-adjusts Scout frequency near month-end |

---

## 9. Authentication & Credentials

### 9.1 X API Authentication

The system uses **OAuth 2.0 User Context** for all operations that act on behalf of a user (posting, liking, following) and **OAuth 2.0 App-Only** for read operations that don't require user context (public timeline fetching).

**Per-account tokens required**:

| Token | Scope | Used By | Notes |
|---|---|---|---|
| API Key (Consumer Key) | App-level | All agents | Shared across EN + JP; identifies the developer app |
| API Secret (Consumer Secret) | App-level | All agents | Shared across EN + JP |
| Access Token (EN) | User-level (EN account) | Publisher, Analyst | Grants read/write for EN account |
| Access Token Secret (EN) | User-level (EN account) | Publisher, Analyst | Paired with EN Access Token |
| Access Token (JP) | User-level (JP account) | Publisher, Analyst | Grants read/write for JP account |
| Access Token Secret (JP) | User-level (JP account) | Publisher, Analyst | Paired with JP Access Token |
| Bearer Token | App-only | Scout | For public read operations (no user context needed) |

**OAuth 2.0 scopes required**: `tweet.read`, `tweet.write`, `users.read`, `like.read`, `like.write`, `follows.read`, `follows.write`, `offline.access`

**OAuth version support**: The system supports both OAuth 1.0a (Access Token + Access Token Secret) and OAuth 2.0 with PKCE (Access Token + Refresh Token). OAuth 1.0a tokens do not expire. OAuth 2.0 tokens expire after 2 hours and require refresh. The `accounts.json` schema includes fields for both methods to support either authentication flow.

**Token refresh**: Access tokens for OAuth 2.0 with PKCE expire after 2 hours. The `x_api.py` wrapper must implement automatic refresh using the refresh token. If refresh fails, Marc escalates to human.

### 9.2 Telegram Bot Authentication

| Token | Source | Used By |
|---|---|---|
| Bot Token | BotFather (`/newbot`) | `telegram_bot.py` |
| Chat ID (Shimpei) | First message to bot | Marc (for sending messages) |

The Telegram Bot only accepts messages from the registered Chat ID (Shimpei). All other messages are ignored (security measure).

### 9.3 Credential Storage

All credentials are stored in `config/accounts.json` (gitignored, never committed to version control). The file is readable only by the system user (`chmod 600`).

---

## 10. Configuration File Schemas

### 10.1 `config/accounts.json`

```json
{
  "x_api": {
    "consumer_key": "xxxxxxxxxxxxxxxxxxxxxxxx",
    "consumer_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "bearer_token": "AAAAAAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "accounts": {
      "EN": {
        "handle": "@ai_beauty_en",
        "user_id": "123456789",
        "access_token": "123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "access_token_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxx"
      },
      "JP": {
        "handle": "@ai_beauty_jp",
        "user_id": "987654321",
        "access_token": "987654321-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "access_token_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "refresh_token": "xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  },
  "telegram": {
    "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "123456789"
  }
}
```

### 10.2 `config/competitors.json`

```json
{
  "last_updated": "2026-03-01",
  "competitors": [
    {
      "handle": "@competitor_1",
      "user_id": "111111111",
      "category": "ai_beauty",
      "market": "EN",
      "priority": "high",
      "notes": "Top performer, 50K followers, consistent 5% ER"
    },
    {
      "handle": "@competitor_2",
      "user_id": "222222222",
      "category": "ai_beauty",
      "market": "JP",
      "priority": "high",
      "notes": "Japanese AI art account, 30K followers"
    }
  ],
  "tracked_keywords": [
    "#AIbeauty", "#AIart", "#AIgirl", "#AImodel",
    "#midjourney", "#stablediffusion", "#aiイラスト", "#AI美女"
  ]
}
```

### 10.3 `config/global_rules.md`

> **Migration note**: This file was originally specified as `global_rules.json` in v2.1-v2.3. Migrated to Markdown format in v2.4 to align with CLAUDE.md's native `@import` loading (see Section 13.4). Markdown is auto-loaded by Claude Code; JSON required manual parsing.

```markdown
# Global Rules
# Updated: 2026-03-01T23:45:00Z by Marc (retrospective)

## Content Rules
- Never use more than 3 hashtags per post — A/B test showed 2 hashtags outperforms 5. (learned 2026-03-01, applies to: Creator)

## Publishing Rules
- Image upload timeout at media/upload v1.1 is common for images >3MB. Always compress to <2MB before upload. (learned 2026-03-01, applies to: Publisher)
```

### 10.4 `config/telegram_config.json`

```json
{
  "commands": {
    "/approve": {"description": "Approve all or specific posts", "args": "optional: comma-separated post indices"},
    "/edit": {"description": "Edit a post", "args": "required: <index> \"<new text>\""},
    "/status": {"description": "Pipeline health check", "args": "none"},
    "/pause": {"description": "Halt posting & outbound", "args": "none"},
    "/resume": {"description": "Resume after pause", "args": "none"},
    "/strategy": {"description": "Override strategy", "args": "required: \"<directive>\""},
    "/details": {"description": "Full content plan", "args": "none"},
    "/metrics": {"description": "Performance metrics", "args": "optional: en|jp"},
    "/competitors": {"description": "Competitor list & stats", "args": "none"},
    "/help": {"description": "List commands", "args": "none"}
  },
  "notification_settings": {
    "morning_brief_time": "07:00",
    "daily_report_time": "23:30",
    "timezone": "Asia/Tokyo",
    "alert_on_error": true,
    "alert_on_follower_anomaly_threshold": 0.10,
    "api_usage_warning_threshold": 0.80
  }
}
```

### 10.5 `data/rate_limits_{date}.json`

```json
{
  "date": "2026-03-01",
  "EN": {
    "posts": {"used": 3, "limit": 5},
    "likes": {"used": 22, "limit": 30},
    "replies": {"used": 7, "limit": 10},
    "follows": {"used": 3, "limit": 5}
  },
  "JP": {
    "posts": {"used": 4, "limit": 5},
    "likes": {"used": 28, "limit": 30},
    "replies": {"used": 9, "limit": 10},
    "follows": {"used": 5, "limit": 5}
  },
  "api_monthly": {
    "reads": {"used": 8500, "limit": 15000, "warning_at": 12000},
    "writes": {"used": 2100, "limit": 50000}
  }
}
```

---

## 11. Cron Job Definitions

All cron jobs run under the project's system user on the VPS. Times are in JST (UTC+9).

> **Locking recommendation**: For Phase 5 deployment, use `flock`-based locking on all cron entries to prevent concurrent execution if a previous job overruns. Example: `flock -n /tmp/pipeline.lock bash scripts/orchestrator.sh`. The orchestrator script already has a file-based lock, but `flock` provides kernel-level protection.
>
> For Phase 1 (local development), `run_pipeline.sh` uses a simpler `.pipeline.lock` file check. The `flock` approach applies to Phase 5 VPS deployment with `orchestrator.sh`.

### 11.1 Crontab Entries

```crontab
# ═══════════════════════════════════════════════════════════════
# X AI Beauty Growth Agent System — Cron Schedule
# All times JST (UTC+9). Set TZ in environment.
# ═══════════════════════════════════════════════════════════════

# Environment
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin:/home/agent/.npm-global/bin
TZ=Asia/Tokyo
PROJECT_DIR=/home/agent/x-ai-beauty
LOG_DIR=/home/agent/x-ai-beauty/logs

# ─── PIPELINE (Marc orchestrates Scout → Strategist → Creator) ───
30 0 * * *  cd $PROJECT_DIR && bash scripts/orchestrator.sh >> $LOG_DIR/cron_$(date +\%Y\%m\%d).log 2>&1

# ─── WAR ROOM (Marc full review) ───
0 6 * * *   cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Run War Room full review. Check all agent outputs for today." --dangerously-skip-permissions >> $LOG_DIR/warroom_$(date +\%Y\%m\%d).log 2>&1

# ─── MORNING BRIEF (Marc → Telegram) ───
0 7 * * *   cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Send morning brief via Telegram." --dangerously-skip-permissions >> $LOG_DIR/brief_$(date +\%Y\%m\%d).log 2>&1

# ─── PUBLISHING (Marc checks approval → Publisher posts) ───
0 9 * * *   cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Check for approved posts. If media_ready, instruct Publisher to post slot 1." --dangerously-skip-permissions >> $LOG_DIR/publish_$(date +\%Y\%m\%d).log 2>&1
0 12 * * *  cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to post slot 2 if media_ready." --dangerously-skip-permissions >> $LOG_DIR/publish_$(date +\%Y\%m\%d).log 2>&1
0 17 * * *  cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to post slot 3 if media_ready." --dangerously-skip-permissions >> $LOG_DIR/publish_$(date +\%Y\%m\%d).log 2>&1
0 21 * * *  cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to post slot 4 if media_ready." --dangerously-skip-permissions >> $LOG_DIR/publish_$(date +\%Y\%m\%d).log 2>&1

# ─── OUTBOUND ENGAGEMENT (distributed throughout the day) ───
30 10 * * * cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to run outbound batch 1 (10 likes, 3 replies, 2 follows per account)." --dangerously-skip-permissions >> $LOG_DIR/outbound_$(date +\%Y\%m\%d).log 2>&1
30 14 * * * cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to run outbound batch 2 (10 likes, 4 replies, 2 follows per account)." --dangerously-skip-permissions >> $LOG_DIR/outbound_$(date +\%Y\%m\%d).log 2>&1
30 18 * * * cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Publisher to run outbound batch 3 (10 likes, 3 replies, 1 follow per account)." --dangerously-skip-permissions >> $LOG_DIR/outbound_$(date +\%Y\%m\%d).log 2>&1

# ─── METRICS COLLECTION (Analyst) ───
0 15 * * *  cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Analyst to collect 6h metrics for morning posts." --dangerously-skip-permissions >> $LOG_DIR/metrics_$(date +\%Y\%m\%d).log 2>&1
0 23 * * *  cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Instruct Analyst to collect 24h metrics and account snapshots." --dangerously-skip-permissions >> $LOG_DIR/metrics_$(date +\%Y\%m\%d).log 2>&1

# ─── DAILY REPORT (Marc → Telegram) ───
30 23 * * * cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Send daily report via Telegram." --dangerously-skip-permissions >> $LOG_DIR/report_$(date +\%Y\%m\%d).log 2>&1

# ─── DAILY RETROSPECTIVE (Marc) ───
45 23 * * * cd $PROJECT_DIR && claude -p "$(cat agents/marc.md) Run daily retrospective. Review errors, update global_rules.md." --dangerously-skip-permissions >> $LOG_DIR/retro_$(date +\%Y\%m\%d).log 2>&1

# ─── MAINTENANCE ───
0 4 * * *   find $LOG_DIR -name "*.log" -mtime +30 -delete  # Clean logs older than 30 days
0 3 * * *   cp $PROJECT_DIR/data/metrics_history.db $PROJECT_DIR/backups/metrics_history_$(date +\%Y\%m\%d).db  # Daily DB backup
0 3 * * 0   find $PROJECT_DIR/backups -name "*.db" -mtime +90 -delete  # Clean backups older than 90 days
```

### 11.2 Orchestrator Script (`scripts/orchestrator.sh`)

> **Phase note**: This orchestrator script is for the full 7-agent system (Phase 5+ VPS deployment). During Phase 1 (local development), Marc is invoked via `scripts/run_pipeline.sh` — a thin shell wrapper that calls `claude -p` with Marc's skill file. See [Phase 1 Technical Specification](./phase-1-spec.md) Section 4.2 for details.

The orchestrator is the main entry point for the overnight pipeline. It invokes Marc, who then invokes downstream agents in sequence.

```bash
#!/bin/bash
set -euo pipefail

PROJECT_DIR="/home/agent/x-ai-beauty"
DATE=$(date +%Y%m%d)
LOG="$PROJECT_DIR/logs/pipeline_${DATE}.log"
LOCK="$PROJECT_DIR/.pipeline.lock"

# Prevent concurrent execution
if [ -f "$LOCK" ]; then
    echo "[$(date)] ERROR: Pipeline lock exists. Previous run may still be active." >> "$LOG"
    # Send alert via Telegram
    # NOTE: telegram_alert.py must be created during Phase 2 (Telegram Bot implementation)
    python3 "$PROJECT_DIR/scripts/telegram_alert.py" "⚠️ Pipeline lock detected. Possible stuck process."
    exit 1
fi
trap "rm -f $LOCK" EXIT
touch "$LOCK"

echo "[$(date)] ═══ Pipeline start ═══" >> "$LOG"

# Health checks
echo "[$(date)] Running health checks..." >> "$LOG"
python3 "$PROJECT_DIR/scripts/health_check.py" >> "$LOG" 2>&1
if [ $? -ne 0 ]; then
    echo "[$(date)] CRITICAL: Health check failed. Aborting pipeline." >> "$LOG"
    python3 "$PROJECT_DIR/scripts/telegram_alert.py" "🚨 Pipeline aborted: health check failed. Check logs."
    exit 1
fi

# Launch Marc — he orchestrates the full pipeline
echo "[$(date)] Launching Marc (COO)..." >> "$LOG"
cd "$PROJECT_DIR"
claude -p "$(cat agents/marc.md)

Run the nightly pipeline:
1. Invoke Scout agent (competitor analysis)
2. Validate Scout output
3. Invoke Strategist agent (strategy update)
4. Validate Strategist output
5. Invoke Creator agent (content generation for EN + JP)
6. Validate Creator output (cross-check with strategy)
7. Run War Room lite (consistency check)
8. Send content preview to Telegram

Read today's date, load relevant data files, and proceed step by step.
Log all actions to logs/pipeline_${DATE}.log." \
--dangerously-skip-permissions >> "$LOG" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "[$(date)] ERROR: Marc pipeline exited with code $EXIT_CODE" >> "$LOG"
    python3 "$PROJECT_DIR/scripts/telegram_alert.py" "🚨 Pipeline failed (exit code: $EXIT_CODE). Check logs."
else
    echo "[$(date)] ═══ Pipeline complete ═══" >> "$LOG"
fi
```

---

## 12. Environment Variables

### 12.1 System Environment (`/home/agent/.bashrc`)

```bash
# Project
export PROJECT_DIR="/home/agent/x-ai-beauty"
export TZ="Asia/Tokyo"

# Claude Code
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export CLAUDE_MODEL="claude-sonnet-4-20250514"  # default model for agents
# The orchestrator can override CLAUDE_MODEL per agent invocation:
#   CLAUDE_MODEL="claude-opus-4-20250514" claude -p "$(cat agents/marc.md) ..."  # Opus for Marc (judgment-heavy)
#   CLAUDE_MODEL="claude-sonnet-4-20250514" claude -p "$(cat agents/scout.md) ..."  # Sonnet for Scout (data processing)

# Node.js (Claude Code dependency)
export NVM_DIR="$HOME/.nvm"
export PATH="$HOME/.npm-global/bin:$PATH"

# Python
export PYTHONPATH="$PROJECT_DIR/scripts:$PYTHONPATH"

# Playwright
export PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright"
```

### 12.2 Agent-Specific Configuration

Rather than environment variables, agent-specific configuration is passed via:
- **CLAUDE.md files** (behavioral instructions — see Section 13)
- **Config JSON files** (credentials, competitor lists — see Section 10)
- **Inline prompts** (task-specific instructions in cron commands — see Section 11)

This avoids environment variable sprawl and keeps agent context self-contained within each Claude Code session.

---

## 13. Memory Architecture (CLAUDE.md)

Claude Code's native memory system replaces the need for custom file-loading logic. Memory files are automatically loaded into context when Claude Code launches.

### 13.1 Memory Hierarchy

```
/home/agent/.claude/CLAUDE.md              ← User-level: global preferences
/home/agent/x-ai-beauty/CLAUDE.md          ← Project-level: shared rules & agent imports
/home/agent/x-ai-beauty/CLAUDE.local.md    ← Local overrides (gitignored)
/home/agent/x-ai-beauty/agents/CLAUDE.md   ← Agent subtree: common agent instructions
```

### 13.2 Project Root CLAUDE.md

```markdown
# X AI Beauty Growth Agent System

## Global Rules
@config/global_rules.md

## Project Context
- Two accounts: EN (global) and JP (日本市場)
- All X operations use X API v2 Basic plan ($200/month)
- Impressions only via Playwright (own account pages)
- Human approval required before any post goes live
- All Telegram communication goes through Marc (COO)

## Agent Definitions
- @agents/marc.md — COO / Orchestrator / Reporter
- @agents/scout.md — Competitor Research
- @agents/strategist.md — Growth Strategy
- @agents/creator.md — Content Planning
- @agents/publisher.md — X API Posting & Outbound
- @agents/analyst.md — Metrics Collection

## Shared Conventions
- Date format: ISO 8601 (2026-03-01T00:00:00Z)
- All times in JST unless explicitly stated otherwise
- Post IDs follow: {account}_{YYYYMMDD}_{slot} (e.g., en_20260301_01)
- Log format: [YYYY-MM-DD HH:MM:SS] [AGENT] [LEVEL] message
- JSON output must be valid and parseable (no trailing commas, no comments)
```

### 13.3 How Marc Updates Memory

During the daily retrospective (23:45 JST), Marc can edit `config/global_rules.md` (imported by the project CLAUDE.md) to add new rules learned from the day's operations. These rules are automatically loaded into every future Claude Code session.

Example retrospective flow:
1. Marc reviews `logs/errors_{date}.log`
2. Identifies recurring pattern (e.g., "image upload fails for >3MB files")
3. Appends to `config/global_rules.md`: `- Always compress images to <2MB before upload (learned 2026-03-01)`
4. Tomorrow's Publisher session automatically inherits this rule

### 13.4 Migration from JSON to CLAUDE.md

| Data Type | Current (v2.1) | Updated (v2.2) | Reason |
|---|---|---|---|
| Behavioral rules | `config/global_rules.json` | `config/global_rules.md` (imported by CLAUDE.md) | Native loading; no custom parsing needed |
| Agent instructions | `agents/marc.md` (loaded manually via `cat`) | `agents/marc.md` (imported via `@agents/marc.md`) | Auto-loaded by CLAUDE.md import chain |
| Credentials | `config/accounts.json` | `config/accounts.json` (unchanged) | JSON still needed for Python scripts |
| Metrics data | SQLite + JSON | SQLite + JSON (unchanged) | Structured data, not behavioral instructions |
| Rate limit counters | `data/rate_limits_{date}.json` | `data/rate_limits_{date}.json` (unchanged) | Machine-parseable for Publisher logic |

**Principle**: CLAUDE.md for behavioral instructions that Claude Code needs. JSON/SQLite for structured data that Python scripts need. No duplication.

### 13.5 Progressive Disclosure Pattern

Rather than loading all context into every agent session upfront, the system uses **progressive disclosure** — agents incrementally discover relevant context through exploration. This reduces context window pollution and lets agents build the context they actually need.

**How it works in this system**:

The project root CLAUDE.md loads shared rules and conventions (small, always-relevant context). Agent-specific instructions are imported via `@agents/{name}.md` but only loaded when Claude Code accesses that subtree. Within each agent's skill file, further references point to data files and documentation that the agent can read on demand.

```
Layer 0 (always loaded):    CLAUDE.md → global rules, conventions, project context
Layer 1 (loaded on access): @agents/scout.md → Scout-specific instructions
Layer 2 (read on demand):   "Read data/scout_report_{yesterday}.json for previous analysis"
Layer 3 (search if needed):  "Search data/ directory for any anomaly flags"
```

**Why this matters**: Loading everything upfront (all competitor data, all metrics history, all strategy documents) would consume the context window before the agent even starts working. Progressive disclosure means Scout reads yesterday's report only if today's analysis needs comparison. Strategist reads metrics history only when formulating strategy. Marc reads error logs only during retrospective.

**Skill files as context pointers**: Each agent's skill file (`agents/scout.md`, etc.) doesn't contain raw data — it contains instructions on where to find data and how to interpret it. This follows the pattern from Claude Code's own development: skill files reference other files that the model reads recursively, building exactly the context it needs.

---

## 14. Agent Design Principles

This section captures design principles for building effective AI agents, informed by lessons from the development of Claude Code itself (source: *"Lessons from Building Claude Code: Seeing like an Agent"*). These principles are framework-level — they apply to this demo and to any future project using the autonomous agent architecture.

### 14.1 Core Philosophy: See Like an Agent

The central insight is that designing tools for an agent requires understanding the agent's own abilities. You give it tools shaped to what it can do well. You learn this by paying attention to its outputs, experimenting, and iterating. There is no rigid formula — it is as much art as science.

For this system, this means: don't assume what tools each agent needs. Define an initial tool set, observe how agents use them, and adjust based on real outputs.

### 14.2 Principle 1: Minimal Tool Count per Agent

Every tool given to an agent is one more option the model must evaluate before acting. More tools means more cognitive overhead, more chance of selecting the wrong tool, and slower execution.

**Rule**: Each agent gets the minimum tools required for its job. No shared "utility belt" of 20 tools given to every agent.

**Application to this system**:

| Agent | Tools | Rationale |
|---|---|---|
| 🔍 Scout | X API read (user lookup, timeline, search) | Read-only. No write tools — Scout should never post or engage. |
| 📊 Strategist | File read/write only | Pure analysis. No API access — Strategist works with data files produced by Scout and Analyst. |
| ✍️ Creator | File read/write only | Content generation. No API access — Creator produces JSON files consumed by Publisher. |
| 📢 Publisher | X API write (post, like, reply, follow), media upload, rate limit counter | Write-focused. No read/analysis tools — Publisher executes, doesn't analyze. |
| 📈 Analyst | X API read (tweet lookup, user lookup), Playwright (impressions), SQLite write | Measurement-focused. No write tools for X — Analyst observes, doesn't act. |
| 🎖️ Marc | Subagent invocation, file read/write, Telegram send, all agent outputs | Broadest tool set — but Marc orchestrates, not executes. Marc calls agents, doesn't call X API directly. |

**Anti-pattern to avoid**: Giving every agent access to X API, Playwright, Telegram, and SQLite "just in case." This leads to agents using the wrong tool for the job (e.g., Scout deciding to post something it found interesting).

### 14.3 Principle 2: Structured Elicitation over Free Text

When an agent needs input from the human, structured options reduce friction and increase communication bandwidth compared to free-text questions.

**Lesson from Claude Code**: The AskUserQuestion tool went through three iterations — bolting questions onto another tool (confused the model), custom markdown output format (unreliable formatting), and finally a dedicated structured tool (worked well). The key insight: Claude seemed to like calling the structured tool, and its outputs were reliable.

**Application to this system**:

Our Telegram command interface already follows this pattern. Instead of Marc asking "What would you like to do with today's posts?" (free text, high friction), the system uses structured commands:

```
/approve           → Binary: approve all
/approve 1,3,5     → Selection: approve specific items
/pause             → Binary: halt operations
/strategy "..."    → Directive: override with instruction
```

**Enhancement based on this principle**: Marc's morning brief should end with specific, actionable options — not open-ended questions. Instead of "Let me know what you think," use:

```
⚡ ACTION REQUIRED:
• 8 posts need approval
• Reply /approve to approve all
• Reply /details to review each post
• Reply /approve 1,3,5 to approve specific posts
```

The structure lowers the human's cognitive load from "what should I say?" to "which option do I pick?"

### 14.4 Principle 3: Task-Based Subagent Coordination

Simple todo lists keep agents on track but become constraining as agents get smarter. Task-based coordination with dependencies and shared updates is more effective for multi-agent systems.

**Lesson from Claude Code**: TodoWrite was replaced by the Task Tool because: (a) system reminders about the todo list made Claude think it had to rigidly follow the list instead of adapting, and (b) subagents needed to coordinate on shared tasks with dependencies.

**Application to this system**:

Marc coordinates agents through a task-based pipeline, not a rigid checklist. Each agent run produces a task state that downstream agents can reference:

```json
{
  "pipeline_date": "2026-03-01",
  "tasks": [
    {
      "id": "scout_run",
      "agent": "scout",
      "status": "completed",
      "output": "data/scout_report_20260301.json",
      "started_at": "2026-03-01T01:00:00Z",
      "completed_at": "2026-03-01T01:12:00Z",
      "dependencies": [],
      "notes": "10 competitors scraped, 2 new accounts discovered"
    },
    {
      "id": "strategy_update",
      "agent": "strategist",
      "status": "completed",
      "output": "data/strategy_current.json",
      "dependencies": ["scout_run"],
      "notes": "Shifted content mix: portrait 50→60% based on engagement data"
    },
    {
      "id": "content_creation",
      "agent": "creator",
      "status": "in_progress",
      "dependencies": ["strategy_update"],
      "notes": "Generating EN posts, JP pending"
    }
  ]
}
```

**Key behaviors**:
- Marc can modify, reorder, or skip tasks based on runtime conditions (not rigidly following a list)
- Subagents can read the task state to understand what happened upstream
- Dependencies are explicit — Creator won't run until Strategist's task is `completed`
- Task state file (`data/pipeline_state_{date}.json`) serves as both coordination mechanism and audit log

### 14.5 Principle 4: Progressive Disclosure over Upfront Context

Don't put everything in the system prompt. Let agents discover context incrementally through exploration.

**Lesson from Claude Code**: Rather than loading all documentation into the system prompt (causing context rot and interfering with the main job), Claude Code uses progressive disclosure — the model is given a link to docs and searches when needed. Skill files reference other files that are read recursively, building exactly the context needed.

**Application to this system** (see also Section 13.5):

Each agent's CLAUDE.md skill file is a **context pointer**, not a context dump. It tells the agent what to read and when, rather than pre-loading everything:

```markdown
# Scout Agent Instructions

## Your role
Competitor research and trend analysis for AI Beauty accounts on X.

## Before you start
1. Read config/competitors.json for the current competitor list
2. Read data/scout_report_{yesterday}.json for continuity (if it exists)
3. Read config/global_rules.md for any Scout-specific rules

## If you discover a new noteworthy account
Add it to the "new_accounts_discovered" array in your output.
Marc will review and optionally add to competitors.json.

## If an API call fails
Read logs/errors_{recent}.log to check if this is a known pattern.
If the competitor went private, note it and skip — don't retry indefinitely.
```

The agent reads `competitors.json` at the start (it always needs this). It reads yesterday's report only if it exists (incremental). It reads error logs only if something fails (conditional). It never reads metrics history, strategy documents, or content plans — those are other agents' concerns.

**Anti-pattern to avoid**: A monolithic system prompt that includes competitor data, metrics summaries, strategy excerpts, error history, and global rules all at once. This wastes context window, causes the model to fixate on irrelevant details, and makes it harder to determine where a particular behavior came from.

### 14.6 Principle 5: Revisit Tool Assumptions as Models Improve

Tools that were necessary for one model generation may constrain the next. As models get smarter, they need less hand-holding and more autonomy.

**Lesson from Claude Code**: TodoWrite was helpful when models forgot their tasks. As models improved, the rigid todo list became constraining — the model stuck to the list instead of adapting. It was replaced with the more flexible Task Tool.

**Application to this system**:

The spec should be treated as a living document. After Phase 5 launch, Marc's daily retrospective should include a periodic (weekly) review of:

- **Are agents using all their tools?** If Scout never uses the search endpoint, maybe it doesn't need it.
- **Are agents struggling with tool selection?** If Publisher frequently tries to analyze metrics instead of post, the tool boundary may be unclear.
- **Are agents being constrained by their instructions?** If Strategist's output is formulaic and never deviates from the template, the instructions may be too rigid.
- **Could agents handle more autonomy?** If human approval is always "approve all" for 2 weeks straight, consider auto-approval for high-confidence posts (PRD Feature F11).

**Practical schedule**: At the end of each week, review agent logs and outputs. Ask: "If I were this agent, would I want different tools?" Adjust skill files and tool access accordingly.

### 14.7 Principle 6: Add Capabilities Without Adding Tools

Not every new capability requires a new tool. Progressive disclosure, skill files, and subagent delegation can expand what agents can do without increasing tool count.

**Lesson from Claude Code**: When Claude needed to answer questions about itself, instead of adding a documentation tool, they built a Guide subagent with extensive search instructions. This added capability to Claude's action space without adding a tool to its tool list.

**Application to this system**:

If we want Scout to also analyze sentiment in competitor replies (a new capability), we don't add a "sentiment analysis tool." Instead:

- Option A: Update Scout's skill file with instructions on how to assess sentiment from reply text (no new tool — Claude can reason about sentiment natively)
- Option B: Create a Scout sub-skill file (`agents/scout_sentiment.md`) that Scout reads when processing replies (progressive disclosure)
- Option C: If the capability is complex enough, create a subagent that Scout delegates to (subagent, not tool)

**Decision framework for "should this be a tool?"**:
```
Can the model do this with its existing tools + better instructions?
  → YES: Update the skill file. Don't add a tool.
  → NO: Can a subagent handle it?
    → YES: Create a subagent. Don't add a tool to the parent.
    → NO: Add a tool. Document why it's necessary.
```

---

## 15. Testing Strategy

### 15.1 Testing Phases

| Phase | Test Type | What's Tested | Pass Criteria |
|---|---|---|---|
| Unit | Individual agent | Each agent produces valid output given mock input | Output matches expected schema; no errors |
| Integration | Agent-to-agent | Scout → Strategist → Creator data flows correctly | Downstream agent correctly consumes upstream output |
| Pipeline | End-to-end (dry run) | Full pipeline without actual X API writes | All agents complete; Telegram reports arrive; no posting |
| Staging | End-to-end (real) | Full pipeline with real X API calls | Posts appear on X; metrics collected; reports accurate |
| Production | Continuous | Ongoing monitoring after launch | <5% error rate; all scheduled events fire; metrics accurate |

### 15.2 Agent-Level Test Cases

**Scout**:
- [ ] Fetches data for all competitors in `competitors.json`
- [ ] Handles private/suspended competitor accounts gracefully (skip + log)
- [ ] Output JSON is valid and contains all required fields
- [ ] API usage per run stays within budget (~45 reads)

**Strategist**:
- [ ] Produces strategy for both EN and JP accounts
- [ ] Content mix percentages sum to 100%
- [ ] Posting schedule has no time conflicts
- [ ] A/B test design is valid (control + variant defined)

**Creator**:
- [ ] Generates correct number of posts matching strategy schedule
- [ ] No post text starts with `@`
- [ ] All posts include hashtags from strategy
- [ ] Image prompts include tool, aspect ratio, and style description
- [ ] Reply templates are varied (no duplicates)

**Publisher**:
- [ ] Posts with images appear correctly on X
- [ ] Rate limit counter increments after each operation
- [ ] Operations stop when daily limit is reached
- [ ] EN and JP accounts use separate OAuth tokens (no cross-posting)
- [ ] Random delays between outbound operations (30-120s)

**Analyst**:
- [ ] Collects metrics for all `posted` status posts
- [ ] SQLite inserts are correct (no duplicates, correct tweet_id mapping)
- [ ] Playwright impression scraping works for both accounts
- [ ] Handles missing impressions gracefully (NULL, not error)

**Marc**:
- [ ] Pipeline executes agents in correct order
- [ ] Detects agent failure and retries (max 3)
- [ ] Telegram morning brief contains accurate data
- [ ] `/approve` command updates post statuses correctly
- [ ] `/pause` halts Publisher operations
- [ ] Error escalation sends Telegram alert with correct severity

### 15.3 Dry Run Mode

All agents support a `DRY_RUN` flag that prevents real X API writes:

```bash
# Dry run: logs what WOULD happen without executing
DRY_RUN=true claude -p "$(cat agents/marc.md) Run pipeline in dry-run mode." --dangerously-skip-permissions
```

In dry-run mode:
- Scout: Reads from X API normally (reads are non-destructive)
- Strategist: Runs normally (no external side effects)
- Creator: Runs normally (no external side effects)
- Publisher: Logs the API call that would be made, but does NOT execute it
- Analyst: Reads from X API normally; Playwright runs but results are logged only
- Marc: All Telegram messages are sent to a test channel instead of the main chat

---

## 16. Deployment Procedure

### 16.1 VPS Setup (Phase 5)

```bash
# 1. Provision VPS (Ubuntu 24.04 LTS, 2 vCPU, 4 GB RAM, 40 GB SSD)
# 2. SSH in and secure the server
ssh root@<vps-ip>
apt update && apt upgrade -y
adduser agent
usermod -aG sudo agent
# Set up SSH key auth, disable password login, enable firewall (ufw)

# 3. Switch to agent user
su - agent

# 4. Install Node.js 22+ (for Claude Code)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22

# 5. Install Claude Code
npm install -g @anthropic-ai/claude-code

# 6. Authenticate Claude Code
claude auth login
# Follow browser-based auth flow

# 7. Install Python 3.11+
sudo apt install -y python3.11 python3-pip python3.11-venv

# 8. Create project directory
mkdir -p ~/x-ai-beauty/{config,data,media/pending,media/posted,logs,agents,scripts,browser_profiles,backups}

# 9. Set up Python virtual environment
cd ~/x-ai-beauty
python3.11 -m venv .venv
source .venv/bin/activate

# 10. Install Python dependencies
pip install tweepy python-telegram-bot anthropic playwright aiohttp aiosqlite
playwright install chromium

# 11. Set up Playwright browser profiles (log into EN + JP X accounts)
python3 scripts/setup_browser_profiles.py

# 12. Initialize SQLite database
python3 scripts/db_manager.py init

# 13. Create configuration files
# Copy templates and fill in credentials
cp config/accounts.example.json config/accounts.json
chmod 600 config/accounts.json
# Edit with actual API keys and tokens

# 14. Set up CLAUDE.md memory files
# Copy CLAUDE.md templates into place

# 15. Set up Telegram Bot
# Create bot via @BotFather on Telegram
# Add bot token to config/accounts.json
# Send /start to bot to get chat_id

# 16. Install crontab
crontab scripts/crontab.txt

# 17. Verify everything
python3 scripts/health_check.py
```

### 16.2 Deployment Checklist

| # | Check | Command / Verification | Status |
|---|---|---|---|
| 1 | VPS is accessible via SSH | `ssh agent@<vps-ip>` | [ ] |
| 2 | Claude Code is installed and authenticated | `claude --version` + `claude -p "hello"` | [ ] |
| 3 | Node.js 22+ is installed | `node --version` | [ ] |
| 4 | Python 3.11+ is installed | `python3 --version` | [ ] |
| 5 | Playwright + Chromium is installed | `playwright install --dry-run` | [ ] |
| 6 | X API credentials work (Bearer token) | `python3 scripts/test_x_api.py --read` | [ ] |
| 7 | X API credentials work (EN write) | `python3 scripts/test_x_api.py --write EN --dry-run` | [ ] |
| 8 | X API credentials work (JP write) | `python3 scripts/test_x_api.py --write JP --dry-run` | [ ] |
| 9 | Telegram Bot responds | Send `/help` to bot | [ ] |
| 10 | Telegram Bot can send messages | `python3 scripts/test_telegram.py` | [ ] |
| 11 | SQLite database is initialized | `sqlite3 data/metrics_history.db ".tables"` | [ ] |
| 12 | Playwright can log into EN account | `python3 scripts/test_playwright.py EN` | [ ] |
| 13 | Playwright can log into JP account | `python3 scripts/test_playwright.py JP` | [ ] |
| 14 | Cron jobs are installed | `crontab -l` | [ ] |
| 15 | CLAUDE.md files are in place | `cat CLAUDE.md` in project root | [ ] |
| 16 | Config files are populated | `python3 scripts/health_check.py` | [ ] |
| 17 | Log directory is writable | `touch logs/test.log && rm logs/test.log` | [ ] |
| 18 | Backup directory exists | `ls -la backups/` | [ ] |
| 19 | Disk space is sufficient | `df -h` (>20 GB free) | [ ] |
| 20 | Timezone is set correctly | `date` shows JST | [ ] |

### 16.3 Rollback Procedure

If something goes wrong after deployment:

1. **Halt all automation**: `crontab -r` (removes all cron jobs)
2. **Stop Telegram Bot**: `systemctl stop telegram-bot` (or kill the process)
3. **Assess damage**: Check `logs/` for errors, check X accounts for unintended posts
4. **Delete problematic posts**: Manual deletion via X web interface if needed
5. **Fix the issue**: Update agent code, config, or rules
6. **Restore cron**: `crontab scripts/crontab.txt`
7. **Resume**: Send `/resume` via Telegram

### 16.4 Update Procedure

For updating agent logic, config, or scripts on the running system:

1. SSH into VPS
2. `cd ~/x-ai-beauty`
3. Edit the relevant files (or `git pull` if using version control)
4. Test the change: run the affected agent manually with `DRY_RUN=true`
5. If good, the next scheduled cron run will pick up the changes automatically
6. No restart needed — each cron invocation is a fresh Claude Code session

---

*Document version: 2.4 (Technical Specification)*
*Updated: March 2, 2026*
*Changes from v2.3: Document review fixes — removed duplicate Section 17, added compliance warnings inline, migrated global_rules to Markdown, fixed VPS phase numbering, added SQLite constraints, added OAuth clarification, added flock recommendation, fixed Analyst API calc, and 14 other consistency/cross-reference fixes. See changelog in header.*
*Language: English (JP market-specific terms in 日本語 where applicable)*
*Related: [PRD v1.1](./x-ai-beauty-prd-v1.md), [Compliance Review](./x-developer-terms-compliance-review.md)*
