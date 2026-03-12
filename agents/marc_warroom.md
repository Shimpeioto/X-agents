# Marc — War Room Playbook

Reference file for the PDCA war room sessions. War rooms are **multi-agent discussions** — Marc moderates a structured debate between Analyst and Strategist.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).
Yesterday's date: subtract 1 day for file lookups.

## Goal

Close the PDCA loop: Check yesterday's results (morning) and generate strategy feedback (evening) so that insights flow back into tomorrow's Strategist run.

War rooms are NOT solo-Marc operations. They are **structured discussions** between three participants:
- **Marc (COO)** — Moderator. Sets agenda, asks probing questions, synthesizes conclusions.
- **Analyst (Sonnet)** — Data advocate. Presents numbers, challenges unsupported claims.
- **Strategist (Opus)** — Strategy advocate. Proposes changes, defends/revises strategy based on data.

## Prerequisites

Read `config/account_status.json`. Only report on and collect metrics for **active accounts**.

---

## Discussion Protocol (Both War Rooms)

Every war room follows this 3-round protocol:

### Round 1 — Independent Briefings (parallel)

Create 2 tasks and spawn both agents as teammates:
- **Analyst task**: Read metrics/data files, prepare KPI report with numbers and interpretations
- **Strategist task**: Read strategy files, prepare assessment (what's working, what's not)

Both work in parallel and message Marc when ready.

### Round 2 — Cross-Examination

Marc sends each agent's findings to the other for challenge:
- Send Analyst's data summary to Strategist: "Do you agree with these numbers? Where does the data contradict your strategy assumptions?"
- Send Strategist's assessment to Analyst: "Do the numbers support these claims? What data is missing?"

Both respond with challenges, agreements, and counter-arguments.

**Early termination**: If Round 2 shows clear consensus (both agents agree on all key points), Marc may skip Round 3 and proceed to synthesis.

### Round 3 — Recommendations

Marc asks both: "Top 3 actionable recommendations for today/tomorrow"
- **Analyst**: What metrics define success, what to watch, what data signals to act on
- **Strategist**: What strategy changes to make, what Creator should prioritize, what experiments to run

### Synthesis — Marc Compiles

After all rounds:
1. Extract consensus points (both agents agreed)
2. Document key debates (they disagreed — capture both positions and resolution)
3. Note unresolved disagreements (flagged for operator)
4. Merge recommendations from both agents
5. Write output JSON with `discussion` section
6. Validate and send Telegram

### Cost Controls

- Max 3 rounds (hard limit — no Round 4)
- Each agent message < 1000 words
- Marc can terminate early if consensus reached in Round 2
- Morning target: < 10 min (before pipeline at 06:00)
- Evening: up to 15 min

### Fallback

If a teammate fails to respond or errors out:
- Wait up to 2 minutes for the response
- If still no response: fall back to solo-Marc briefing (read data yourself, compose output)
- Note in output: `"discussion": null` with a `"discussion_fallback_reason"` field
- Solo-Marc output still passes validation (discussion is a soft check)

---

## Morning War Room (05:30 JST)

Review yesterday's results and send the operator a morning briefing before the pipeline runs.

### 1. Pre-Discussion: Gather Data

Read data files to prepare file paths for the agents. For each **active** account, verify these exist:
- `data/daily_report_{yesterday_YYYYMMDD}.json` — yesterday's daily report
- `data/content_plan_{yesterday_YYYYMMDD}_{account}.json` — what was posted
- `data/outbound_log_{yesterday_YYYYMMDD}.json` — outbound actions taken
- `data/strategy_{yesterday_YYYYMMDD}.json` — yesterday's strategy
- `data/strategy_current.json` — current active strategy
- `data/strategy_feedback_{yesterday_YYYYMMDD}.json` — yesterday's feedback
- `data/core_strategy.json` — KPI targets and benchmarks

If `daily_report` does not exist: note this for the agents — they should work with whatever data is available.

### 2. Spawn Discussion Team

Spawn **Analyst** (model: sonnet) and **Strategist** (model: opus) as teammates.

**Analyst spawn prompt:**
```
You are Analyst. Read agents/analyst.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}. Yesterday: {YESTERDAY}.
Active accounts: {ACTIVE_ACCOUNTS}

MORNING WAR ROOM — Round 1: Data Briefing

Read these files and prepare a KPI briefing for the team:
- data/daily_report_{yesterday_YYYYMMDD}.json
- data/content_plan_{yesterday_YYYYMMDD}_{account}.json (for each active account)
- data/outbound_log_{yesterday_YYYYMMDD}.json
- data/metrics_{yesterday_YYYYMMDD}_{account}.json (for each active account)
- data/core_strategy.json (for KPI targets)

Cover for each active account:
1. Follower count, delta, growth trend
2. Engagement per post by category — which categories are winning/losing
3. Outbound ROI — likes/follows given vs reciprocal engagement
4. Any anomalies or unexpected patterns
5. Comparison against KPI targets from core_strategy.json

Lead with numbers. Be specific. Flag anything that doesn't add up.
Message Marc when your briefing is ready.
```

**Strategist spawn prompt:**
```
You are Strategist. Read agents/strategist.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}. Yesterday: {YESTERDAY}.
Active accounts: {ACTIVE_ACCOUNTS}

MORNING WAR ROOM — Round 1: Strategy Assessment

Read these files and prepare a strategy assessment:
- data/strategy_{yesterday_YYYYMMDD}.json
- data/strategy_current.json
- data/strategy_feedback_{yesterday_YYYYMMDD}.json (if exists)
- data/daily_report_{yesterday_YYYYMMDD}.json (for results context)
- data/core_strategy.json

Cover for each active account:
1. Is the current strategy working? Honest assessment.
2. What's working — which decisions paid off and why
3. What's NOT working — which efforts produced zero results
4. A/B test verdict — not just status, but what it tells us
5. Competitor context — how do our numbers compare at this stage

Lead with strategic reasoning, back with data. Be willing to admit failures.
Message Marc when your assessment is ready.
```

### 3. Run Cross-Examination (Round 2)

When both agents have sent their Round 1 messages:

**To Strategist:**
```
Round 2 — Cross-Examination. Here is Analyst's data briefing:

{paste Analyst's Round 1 message}

Questions:
- Do you agree with these numbers? Anything surprising?
- Where does this data contradict or support your strategy?
- What would you change based on these findings?
Keep your response under 1000 words.
```

**To Analyst:**
```
Round 2 — Cross-Examination. Here is Strategist's assessment:

{paste Strategist's Round 1 message}

Questions:
- Do the numbers support these claims?
- What data is missing from Strategist's analysis?
- Where is the Strategist making assumptions without data backing?
Keep your response under 1000 words.
```

### 4. Run Recommendations (Round 3)

If consensus is NOT yet clear after Round 2:

**To both agents (separate messages):**
```
Round 3 — Final Recommendations.

Based on the discussion so far, give me your top 3 actionable recommendations for today.
For each: what to do, why, and how to measure success.
Keep your response under 500 words.
```

### 5. Synthesize and Write Morning Briefing

Compile all discussion rounds into the output. Build three sections from the discussion:

#### Section A: KPI Dashboard (from Analyst's data)
- Followers, delta, growth trend
- Engagement per post by category
- Outbound ROI
- Anomalies

#### Section B: Strategy Assessment (from Strategist + challenges)
- Overall verdict (incorporate Analyst's challenges)
- What's working / not working (with data backing from the discussion)
- A/B test verdict
- Competitor context

#### Section C: Recommendations & Action Items (merged from Round 3)
- Merged recommendations from both agents
- Blockers for operator
- Today's priorities

### 6. Write Output File

Write `data/morning_briefing_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "type": "morning_briefing",
  "daily_report_used": "data/daily_report_YYYYMMDD.json",
  "discussion": {
    "participants": ["Marc (COO)", "Analyst", "Strategist"],
    "rounds": [
      {
        "round": 1,
        "type": "data_briefing",
        "contributions": [
          {"agent": "Analyst", "summary": "KPI briefing highlights..."},
          {"agent": "Strategist", "summary": "Strategy assessment highlights..."}
        ]
      },
      {
        "round": 2,
        "type": "cross_examination",
        "exchanges": [
          {"from": "Strategist", "re": "Analyst's data", "summary": "Agreed on X, challenged Y..."},
          {"from": "Analyst", "re": "Strategist's assessment", "summary": "Data supports A, contradicts B..."}
        ]
      },
      {
        "round": 3,
        "type": "recommendations",
        "analyst_recs": ["rec 1", "rec 2", "rec 3"],
        "strategist_recs": ["rec 1", "rec 2", "rec 3"]
      }
    ],
    "key_debates": [
      {
        "topic": "...",
        "analyst_position": "...",
        "strategist_position": "...",
        "resolution": "agreed|analyst_won|strategist_won|unresolved"
      }
    ],
    "consensus_points": ["Point both agents agreed on..."],
    "unresolved": ["Disagreement flagged for operator..."]
  },
  "accounts": {
    "EN": {
      "kpi_dashboard": {
        "followers": 1250,
        "followers_change": 12,
        "followers_growth_trend": "+12 today, +45 this week, 6.4/day avg",
        "avg_engagement_per_post": 35.2,
        "engagement_trend": "up 15% vs previous 3-day avg",
        "best_category": {"name": "engagement_questions", "avg_engagement": 51, "vs_account_avg": "+45%"},
        "worst_category": {"name": "image_showcase", "avg_engagement": 12, "vs_account_avg": "-65%"},
        "outbound_roi": "60 likes, 12 follows given → 3 reciprocal follows (5% conversion)"
      },
      "strategy_assessment": {
        "overall_verdict": "Substantive assessment incorporating both data and strategic reasoning...",
        "whats_working": ["..."],
        "whats_not_working": ["..."],
        "ab_test_verdict": "...",
        "competitor_context": "..."
      },
      "recommendations": [
        "Merged recommendation from discussion..."
      ],
      "action_items": [
        "Action for operator..."
      ]
    }
  },
  "summary": "Strategic summary covering discussion highlights, KPIs, and recommendations",
  "telegram_message": "Pre-composed Telegram message with discussion highlights"
}
```

### 7. Validate and Send

```bash
python3 scripts/validate.py morning_briefing data/morning_briefing_{YYYYMMDD}.json
```

Compose Telegram message that includes discussion highlights:

```
☀️ Morning Briefing — {date}

📊 KPIs: [dashboard summary from Analyst]

💬 Discussion Highlights:
• Analyst: "[key finding]"
• Strategist: "[key assessment]"
• Debate: [topic] → [resolution]
• Consensus: [agreed point]

📋 Recommendations: [merged from discussion]
⚠️ Action Items: [for operator]
```

```bash
python3 scripts/telegram_send.py "<morning briefing telegram message>"
```

Generate and send HTML:
```bash
python3 scripts/generate_html_report.py generic data/morning_briefing_{YYYYMMDD}.json --title "Morning Briefing — {YYYY-MM-DD}"
python3 scripts/telegram_send.py --document data/morning_briefing_{YYYYMMDD}.html "Morning Briefing — {YYYY-MM-DD}"
```

### 8. Shutdown Teammates

Send shutdown requests to both Analyst and Strategist after synthesis is complete.

---

## Evening War Room (22:00 JST)

Collect today's metrics, run a post-mortem discussion, produce strategy feedback for tomorrow, and send the operator a daily summary.

### 1. Pre-Discussion: Collect Metrics

For each **active** account:
```bash
python3 scripts/analyst.py collect --account {account}
```

If no posted tweets exist today: log and skip collection (not an error).

Generate metric summaries:
```bash
python3 scripts/analyst.py summary --account {account}
```

Validate:
```bash
python3 scripts/validate.py analyst data/metrics_{YYYYMMDD}_{account}.json
python3 scripts/validate.py analyst_metrics data/metrics_history.db
```

### 2. Spawn Discussion Team

Spawn **Analyst** (model: sonnet) and **Strategist** (model: opus) as teammates.

**Analyst spawn prompt:**
```
You are Analyst. Read agents/analyst.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}.
Active accounts: {ACTIVE_ACCOUNTS}

EVENING WAR ROOM — Round 1: Post-Mortem Data

FIRST: Produce the daily report. Read agents/analyst.md, section 'Intelligence Mode' for instructions.
Write output to: data/daily_report_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary.

Input files:
- data/metrics_{YYYYMMDD}_{account}.json (for each active account)
- data/strategy_{YYYYMMDD}.json
- data/pipeline_state_{YYYYMMDD}.json
- data/outbound_log_{YYYYMMDD}.json
- data/content_plan_{YYYYMMDD}_{account}.json (for each active account)
- Yesterday's report: data/daily_report_{prev_YYYYMMDD}.json (if exists)

THEN: Prepare your post-mortem data briefing for the war room discussion.
Cover for each active account:
1. Today's metrics vs yesterday — what changed
2. Category performance — grade each category
3. A/B test data — raw numbers for each variant
4. Outbound effectiveness — actions taken vs results
5. Anomalies — anything unexpected

Message Marc when BOTH the daily report file and your briefing are ready.
```

**Strategist spawn prompt:**
```
You are Strategist. Read agents/strategist.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}.
Active accounts: {ACTIVE_ACCOUNTS}

EVENING WAR ROOM — Round 1: Strategy Post-Mortem

Read these files and prepare your strategy post-mortem:
- data/strategy_{YYYYMMDD}.json (today's strategy — YOUR predictions)
- data/content_plan_{YYYYMMDD}_{account}.json (what was actually posted)
- data/metrics_{YYYYMMDD}_{account}.json (how it performed)
- data/outbound_log_{YYYYMMDD}.json (outbound results)
- data/core_strategy.json (benchmarks)

Cover for each active account:
1. Grade your own strategy predictions vs actual results — be honest
2. Which strategy decisions worked and which didn't
3. Content mix effectiveness — should proportions change
4. A/B test assessment — what have we learned
5. Proposed adjustments for tomorrow

Be willing to admit failures. Propose pivots where data supports them.
Message Marc when your assessment is ready.
```

### 3. Validate Daily Report

After Analyst completes Round 1, validate the daily report:
```bash
python3 scripts/validate.py analyst_report data/daily_report_{YYYYMMDD}.json
```

If validation fails: fall back to composing a basic Telegram message from the raw metrics summaries.

### 4. Run Cross-Examination (Round 2)

Same protocol as morning — send each agent's findings to the other with challenge questions.

**To Strategist:**
```
Round 2 — Cross-Examination. Here is Analyst's post-mortem data:

{paste Analyst's Round 1 message}

Questions:
- Does this data validate or invalidate your strategy assumptions?
- What should we change for tomorrow based on these results?
- Any category performance surprises?
Keep your response under 1000 words.
```

**To Analyst:**
```
Round 2 — Cross-Examination. Here is Strategist's post-mortem:

{paste Strategist's Round 1 message}

Questions:
- Are the Strategist's self-grades accurate? Where are they being too kind or too harsh?
- Does the data support the proposed adjustments?
- What metrics should we track differently tomorrow?
Keep your response under 1000 words.
```

### 5. Run Recommendations (Round 3)

**To both agents (separate messages):**
```
Round 3 — Recommendations for Tomorrow.

Based on today's results and this discussion:
1. Top 3 strategy adjustments for tomorrow (with confidence: high/medium/low)
2. What should Creator prioritize?
3. Any experiments to run?
Keep your response under 500 words.
```

### 6. Synthesize and Generate Strategy Feedback

Compile the discussion into strategy feedback. This is the PDCA bridge.

For EACH **active** account, extract from the discussion:

1. **Category Performance**: From Analyst's data + Strategist's assessment. Rank categories, calculate `vs_average`. Use discussion consensus for recommendations.

2. **A/B Test Evaluation**: From Analyst's raw numbers + Strategist's interpretation. Use the stricter assessment if they disagree.

3. **Posting Time Effectiveness**: From Analyst's slot-level data.

4. **Outbound Effectiveness**: From Analyst's outbound analysis.

5. **Recommended Adjustments**: Merged from Round 3 recommendations. Include confidence levels. If agents disagreed, use the more conservative recommendation.

Write `data/strategy_feedback_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "daily_report_used": "data/daily_report_YYYYMMDD.json",
  "strategy_used": "data/strategy_YYYYMMDD.json",
  "discussion": {
    "participants": ["Marc (COO)", "Analyst", "Strategist"],
    "rounds": [
      {
        "round": 1,
        "type": "post_mortem",
        "contributions": [
          {"agent": "Analyst", "summary": "Post-mortem data highlights..."},
          {"agent": "Strategist", "summary": "Strategy self-grade highlights..."}
        ]
      },
      {
        "round": 2,
        "type": "cross_examination",
        "exchanges": [
          {"from": "Strategist", "re": "Analyst's data", "summary": "..."},
          {"from": "Analyst", "re": "Strategist's assessment", "summary": "..."}
        ]
      },
      {
        "round": 3,
        "type": "recommendations",
        "analyst_recs": ["rec 1", "rec 2", "rec 3"],
        "strategist_recs": ["rec 1", "rec 2", "rec 3"]
      }
    ],
    "key_debates": [
      {
        "topic": "...",
        "analyst_position": "...",
        "strategist_position": "...",
        "resolution": "agreed|analyst_won|strategist_won|unresolved"
      }
    ],
    "consensus_points": ["..."],
    "unresolved": ["..."]
  },
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
          "rationale": "engagement_questions outperformed by 85% over 3 days — consensus from Analyst data and Strategist assessment"
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

### 7. Send Daily Report + Alerts via Telegram

1. Read `daily_report_{YYYYMMDD}.json`
2. Send `telegram_report` field:
   ```bash
   python3 scripts/telegram_send.py "<telegram_report content>"
   ```
3. For each entry in `telegram_alerts`:
   ```bash
   python3 scripts/telegram_send.py "<alert content>"
   ```
4. Compose and send discussion highlights:
   ```
   🌙 Evening War Room — {date}

   📊 Today's Results: [from Analyst]

   💬 Discussion Highlights:
   • Analyst: "[key finding]"
   • Strategist: "[key assessment]"
   • Debate: [topic] → [resolution]
   • Consensus: [agreed point]

   📋 Tomorrow's Adjustments: [from strategy_feedback]
   ⚠️ Unresolved: [for operator decision]
   ```
5. Generate and send HTML reports:
   ```bash
   python3 scripts/generate_html_report.py daily_report data/daily_report_{YYYYMMDD}.json
   python3 scripts/telegram_send.py --document data/daily_report_{YYYYMMDD}.html "Daily Report — {YYYY-MM-DD}"
   ```

### 8. Shutdown Teammates

Send shutdown requests to both Analyst and Strategist after synthesis is complete.

---

## Error Recovery

- **Teammate spawn failure**: Fall back to solo-Marc briefing, set `"discussion": null`
- **Teammate unresponsive**: Wait 2 min max, then proceed with available responses. Note partial discussion in output.
- **Missing daily report**: Compose minimal briefing from raw metrics, note unavailability
- **Analyst collection failure**: Log as warning, proceed with strategy feedback using available data
- **Strategy feedback generation failure**: Log error, skip feedback (tomorrow's Strategist will run without it)
- **Telegram send failure**: Log as warning, never fail the war room
- **No posted content today**: Skip metrics collection, note in briefing
- **Round 2 consensus**: If both agents fully agree in Round 2, skip Round 3 — synthesize early
