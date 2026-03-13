# Marc — War Room Playbook

Reference file for the PDCA war room sessions. War rooms are **multi-agent discussions** — Marc moderates a structured debate between Analyst and Strategist using **subagent calls**.

Today's date is provided in the invocation prompt as YYYY-MM-DD. For file paths, strip dashes (YYYYMMDD).
Yesterday's date: subtract 1 day for file lookups.

## Goal

Close the PDCA loop: Check yesterday's results (morning) and generate strategy feedback (evening) so that insights flow back into tomorrow's Strategist run.

War rooms are NOT solo-Marc operations. They are **structured discussions** between three participants:
- **Marc (COO)** — Moderator. Sets agenda, relays findings between agents, synthesizes conclusions.
- **Analyst (Sonnet)** — Data advocate. Presents numbers, challenges unsupported claims.
- **Strategist (Opus)** — Strategy advocate. Proposes changes, defends/revises strategy based on data.

## Prerequisites

Read `config/account_status.json`. Only report on and collect metrics for **active accounts**.

---

## How Subagents Work

Use the **Agent tool** (NOT Agent Teams) to spawn Analyst and Strategist. Each subagent call:
- **Blocks** until the agent completes its work
- **Returns** the agent's response directly to you (no messaging needed)
- **Terminates** automatically when done (no shutdown needed)

Key rules:
- Use `subagent_type: "general-purpose"` for all spawns
- Use `model: "sonnet"` for Analyst, `model: "opus"` for Strategist
- For Round 1: spawn both with `run_in_background: true` so they work in parallel, then collect results
- For Round 2+: can run in parallel too (they're independent)
- Each subagent prompt must be **self-contained** — include all file paths and context the agent needs
- Subagents can read files and run scripts directly — they have full tool access

---

## Discussion Protocol (Both War Rooms)

Every war room follows this 3-round protocol:

### Round 1 — Independent Briefings (parallel)

Spawn both agents as **parallel subagents** (both with `run_in_background: true`):
- **Analyst subagent**: Read metrics/data files, return KPI report with numbers and interpretations
- **Strategist subagent**: Read strategy files, return assessment (what's working, what's not)

Wait for both to complete, then read their results.

### Round 2 — Cross-Examination (parallel)

Spawn two new subagents, each with the OTHER agent's Round 1 output:
- **Strategist subagent**: receives Analyst's data → challenges/agrees with data interpretation
- **Analyst subagent**: receives Strategist's assessment → validates/challenges with data

Both can run in parallel (they're independent).

**Early termination**: If Round 2 shows clear consensus (both agents agree on all key points), Marc may skip Round 3 and proceed to synthesis.

### Round 3 — Recommendations (parallel)

Spawn two new subagents, each with the full discussion context:
- **Analyst subagent**: What metrics define success, what to watch, what data signals to act on
- **Strategist subagent**: What strategy changes to make, what Creator should prioritize, what experiments to run

### Synthesis — Marc Compiles

After all rounds, Marc directly has ALL results (returned from subagent calls). No messaging or file coordination needed.

1. Extract consensus points (both agents agreed)
2. Document key debates (they disagreed — capture both positions and resolution)
3. Note unresolved disagreements (flagged for operator)
4. Merge recommendations from both agents
5. Write output JSON with `discussion` section
6. Validate and send Telegram

### Cost Controls

- Max 3 rounds (hard limit — no Round 4)
- Each agent response < 1000 words
- Marc can terminate early if consensus reached in Round 2
- Morning target: < 10 min (before pipeline at 06:00)
- Evening: up to 15 min

### Fallback

If a subagent call fails or returns an error:
- Log the error
- Fall back to solo-Marc briefing (read data yourself, compose output)
- Note in output: `"discussion": null` with a `"discussion_fallback_reason"` field
- Solo-Marc output still passes validation (discussion is a soft check)

---

## Morning War Room (05:30 JST)

Review yesterday's results and send the operator a morning briefing before the pipeline runs.

### 1. Pre-Discussion: Gather Data

Read data files to prepare file paths for the agents. For each **active** account, verify these exist:
- `data/metrics/daily_report_{yesterday_YYYYMMDD}.json` — yesterday's daily report
- `data/content/content_plan_{yesterday_YYYYMMDD}_{account}.json` — what was posted
- `data/outbound/outbound_log_{yesterday_YYYYMMDD}.json` — outbound actions taken
- `data/strategy/strategy_{yesterday_YYYYMMDD}.json` — yesterday's strategy
- `data/strategy/strategy_current.json` — current active strategy
- `data/strategy/strategy_feedback_{yesterday_YYYYMMDD}.json` — yesterday's feedback
- `data/strategy/core_strategy.json` — KPI targets and benchmarks

If `daily_report` does not exist: note this for the agents — they should work with whatever data is available.

### 2. Round 1: Spawn Parallel Subagents

Spawn **Analyst** (model: sonnet) and **Strategist** (model: opus) as parallel subagents.

**Analyst subagent prompt:**
```
You are Analyst. Read agents/analyst.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}. Yesterday: {YESTERDAY}.
Active accounts: {ACTIVE_ACCOUNTS}

MORNING WAR ROOM — Round 1: Data Briefing

Read these files and prepare a KPI briefing:
- data/metrics/daily_report_{yesterday_YYYYMMDD}.json
- data/content/content_plan_{yesterday_YYYYMMDD}_{account}.json (for each active account)
- data/outbound/outbound_log_{yesterday_YYYYMMDD}.json
- data/metrics/metrics_{yesterday_YYYYMMDD}_{account}.json (for each active account)
- data/strategy/core_strategy.json (for KPI targets)

Cover for each active account:
1. Follower count, delta, growth trend
2. Engagement per post by category — which categories are winning/losing
3. Outbound ROI — likes/follows given vs reciprocal engagement
4. Any anomalies or unexpected patterns
5. Comparison against KPI targets from core_strategy.json

Lead with numbers. Be specific. Flag anything that doesn't add up.
Return your briefing as text (do NOT write to a file). Keep under 1000 words.
```

**Strategist subagent prompt:**
```
You are Strategist. Read agents/strategist.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}. Yesterday: {YESTERDAY}.
Active accounts: {ACTIVE_ACCOUNTS}

MORNING WAR ROOM — Round 1: Strategy Assessment

Read these files and prepare a strategy assessment:
- data/strategy/strategy_{yesterday_YYYYMMDD}.json
- data/strategy/strategy_current.json
- data/strategy/strategy_feedback_{yesterday_YYYYMMDD}.json (if exists)
- data/metrics/daily_report_{yesterday_YYYYMMDD}.json (for results context)
- data/strategy/core_strategy.json

Cover for each active account:
1. Is the current strategy working? Honest assessment.
2. What's working — which decisions paid off and why
3. What's NOT working — which efforts produced zero results
4. A/B test verdict — not just status, but what it tells us
5. Competitor context — how do our numbers compare at this stage

Lead with strategic reasoning, back with data. Be willing to admit failures.
Return your assessment as text (do NOT write to a file). Keep under 1000 words.
```

Collect both results before proceeding.

### 3. Round 2: Cross-Examination (parallel subagents)

Spawn two new subagents, each receiving the OTHER agent's Round 1 output:

**Strategist subagent (receives Analyst's data):**
```
You are Strategist. Read agents/strategist.md, especially 'War Room Discussion Mode'.

Round 2 — Cross-Examination. Here is Analyst's data briefing:

{paste Analyst's Round 1 result}

Questions:
- Do you agree with these numbers? Anything surprising?
- Where does this data contradict or support your strategy?
- What would you change based on these findings?
Keep your response under 1000 words. Return as text.
```

**Analyst subagent (receives Strategist's assessment):**
```
You are Analyst. Read agents/analyst.md, especially 'War Room Discussion Mode'.

Round 2 — Cross-Examination. Here is Strategist's assessment:

{paste Strategist's Round 1 result}

Questions:
- Do the numbers support these claims?
- What data is missing from Strategist's analysis?
- Where is the Strategist making assumptions without data backing?
Keep your response under 1000 words. Return as text.
```

### 4. Round 3: Recommendations (parallel subagents, if needed)

If consensus is NOT yet clear after Round 2:

**Analyst subagent:**
```
You are Analyst. Round 3 — Final Recommendations.

Discussion context so far:
- Your Round 1 briefing: {summary}
- Strategist's Round 1 assessment: {summary}
- Cross-examination highlights: {key points}

Give me your top 3 actionable recommendations for today.
For each: what to do, why, and how to measure success.
Keep under 500 words. Return as text.
```

**Strategist subagent:**
```
You are Strategist. Round 3 — Final Recommendations.

Discussion context so far:
- Analyst's Round 1 briefing: {summary}
- Your Round 1 assessment: {summary}
- Cross-examination highlights: {key points}

Give me your top 3 actionable recommendations for today.
For each: what to do, why, and how to measure success.
Keep under 500 words. Return as text.
```

### 5. Synthesize and Write Morning Briefing

Compile all subagent results into the output. Build three sections:

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

Write `data/metrics/morning_briefing_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "type": "morning_briefing",
  "daily_report_used": "data/metrics/daily_report_YYYYMMDD.json",
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
python3 scripts/validate.py morning_briefing data/metrics/morning_briefing_{YYYYMMDD}.json
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
python3 scripts/generate_html_report.py generic data/metrics/morning_briefing_{YYYYMMDD}.json --title "Morning Briefing — {YYYY-MM-DD}"
python3 scripts/telegram_send.py --document data/metrics/morning_briefing_{YYYYMMDD}.html "Morning Briefing — {YYYY-MM-DD}"
```

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
python3 scripts/validate.py analyst data/metrics/metrics_{YYYYMMDD}_{account}.json
python3 scripts/validate.py analyst_metrics data/metrics/metrics_history.db
```

### 2. Round 1: Spawn Parallel Subagents

Spawn **Analyst** (model: sonnet) and **Strategist** (model: opus) as parallel subagents.

**Analyst subagent prompt:**
```
You are Analyst. Read agents/analyst.md for your full instructions, especially the 'War Room Discussion Mode' section AND the 'Intelligence Mode' section.
Today: {YYYY-MM-DD}.
Active accounts: {ACTIVE_ACCOUNTS}

EVENING WAR ROOM — Round 1: Daily Report + Post-Mortem Data

FIRST: Produce the daily report. Follow agents/analyst.md 'Intelligence Mode' instructions.
Write the daily report to: data/metrics/daily_report_{YYYYMMDD}.json
Output ONLY valid JSON — no markdown code fences, no commentary.

Input files:
- data/metrics/metrics_{YYYYMMDD}_{account}.json (for each active account)
- data/strategy/strategy_{YYYYMMDD}.json
- data/pipeline/pipeline_state_{YYYYMMDD}.json
- data/outbound/outbound_log_{YYYYMMDD}.json
- data/content/content_plan_{YYYYMMDD}_{account}.json (for each active account)
- Yesterday's report: data/metrics/daily_report_{prev_YYYYMMDD}.json (if exists)

THEN: Prepare your post-mortem data briefing for the war room discussion.
Cover for each active account:
1. Today's metrics vs yesterday — what changed
2. Category performance — grade each category
3. A/B test data — raw numbers for each variant
4. Outbound effectiveness — actions taken vs results
5. Anomalies — anything unexpected

Return your briefing as text after writing the daily report file. Keep under 1000 words.
```

**Strategist subagent prompt:**
```
You are Strategist. Read agents/strategist.md for your full instructions, especially the 'War Room Discussion Mode' section.
Today: {YYYY-MM-DD}.
Active accounts: {ACTIVE_ACCOUNTS}

EVENING WAR ROOM — Round 1: Strategy Post-Mortem

Read these files and prepare your strategy post-mortem:
- data/strategy/strategy_{YYYYMMDD}.json (today's strategy — YOUR predictions)
- data/content/content_plan_{YYYYMMDD}_{account}.json (what was actually posted)
- data/metrics/metrics_{YYYYMMDD}_{account}.json (how it performed)
- data/outbound/outbound_log_{YYYYMMDD}.json (outbound results)
- data/strategy/core_strategy.json (benchmarks)

Cover for each active account:
1. Grade your own strategy predictions vs actual results — be honest
2. Which strategy decisions worked and which didn't
3. Content mix effectiveness — should proportions change
4. A/B test assessment — what have we learned
5. Proposed adjustments for tomorrow

Be willing to admit failures. Propose pivots where data supports them.
Return your assessment as text (do NOT write to a file). Keep under 1000 words.
```

Collect both results before proceeding.

### 3. Validate Daily Report

After Analyst subagent completes, validate the daily report:
```bash
python3 scripts/validate.py analyst_report data/metrics/daily_report_{YYYYMMDD}.json
```

If validation fails: fall back to composing a basic Telegram message from the raw metrics summaries.

### 4. Round 2: Cross-Examination (parallel subagents)

Same protocol as morning — spawn two subagents, each receiving the OTHER agent's Round 1 output.

**Strategist subagent (receives Analyst's post-mortem data):**
```
You are Strategist. Read agents/strategist.md, especially 'War Room Discussion Mode'.

Round 2 — Cross-Examination. Here is Analyst's post-mortem data:

{paste Analyst's Round 1 result}

Questions:
- Does this data validate or invalidate your strategy assumptions?
- What should we change for tomorrow based on these results?
- Any category performance surprises?
Keep your response under 1000 words. Return as text.
```

**Analyst subagent (receives Strategist's post-mortem):**
```
You are Analyst. Read agents/analyst.md, especially 'War Room Discussion Mode'.

Round 2 — Cross-Examination. Here is Strategist's post-mortem:

{paste Strategist's Round 1 result}

Questions:
- Are the Strategist's self-grades accurate? Where are they being too kind or too harsh?
- Does the data support the proposed adjustments?
- What metrics should we track differently tomorrow?
Keep your response under 1000 words. Return as text.
```

### 5. Round 3: Recommendations (parallel subagents, if needed)

**Analyst subagent:**
```
You are Analyst. Round 3 — Recommendations for Tomorrow.

Discussion context:
- Your post-mortem data: {summary}
- Strategist's post-mortem: {summary}
- Cross-examination highlights: {key points}

1. Top 3 strategy adjustments for tomorrow (with confidence: high/medium/low)
2. What should Creator prioritize?
3. Any experiments to run?
Keep under 500 words. Return as text.
```

**Strategist subagent:**
```
You are Strategist. Round 3 — Recommendations for Tomorrow.

Discussion context:
- Analyst's post-mortem data: {summary}
- Your post-mortem: {summary}
- Cross-examination highlights: {key points}

1. Top 3 strategy adjustments for tomorrow (with confidence: high/medium/low)
2. What should Creator prioritize?
3. Any experiments to run?
Keep under 500 words. Return as text.
```

### 6. Synthesize and Generate Strategy Feedback

Compile all subagent results into strategy feedback. This is the PDCA bridge.

For EACH **active** account, extract from the discussion:

1. **Category Performance**: From Analyst's data + Strategist's assessment. Rank categories, calculate `vs_average`. Use discussion consensus for recommendations.

2. **A/B Test Evaluation**: From Analyst's raw numbers + Strategist's interpretation. Use the stricter assessment if they disagree.

3. **Posting Time Effectiveness**: From Analyst's slot-level data.

4. **Outbound Effectiveness**: From Analyst's outbound analysis.

5. **Recommended Adjustments**: Merged from Round 3 recommendations. Include confidence levels. If agents disagreed, use the more conservative recommendation.

Write `data/strategy/strategy_feedback_{YYYYMMDD}.json`:

```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601",
  "daily_report_used": "data/metrics/daily_report_YYYYMMDD.json",
  "strategy_used": "data/strategy/strategy_YYYYMMDD.json",
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
python3 scripts/validate.py strategy_feedback data/strategy/strategy_feedback_{YYYYMMDD}.json
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
   python3 scripts/generate_html_report.py daily_report data/metrics/daily_report_{YYYYMMDD}.json
   python3 scripts/telegram_send.py --document data/metrics/daily_report_{YYYYMMDD}.html "Daily Report — {YYYY-MM-DD}"
   ```

---

## Error Recovery

- **Subagent spawn failure**: Fall back to solo-Marc briefing, set `"discussion": null`
- **Subagent returns error or empty result**: Log and proceed with available responses. Note partial discussion in output.
- **Missing daily report**: Compose minimal briefing from raw metrics, note unavailability
- **Analyst collection failure**: Log as warning, proceed with strategy feedback using available data
- **Strategy feedback generation failure**: Log error, skip feedback (tomorrow's Strategist will run without it)
- **Telegram send failure**: Log as warning, never fail the war room
- **No posted content today**: Skip metrics collection, note in briefing
- **Round 2 consensus**: If both agents fully agree in Round 2, skip Round 3 — synthesize early
