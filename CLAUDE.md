# X AI Beauty Growth Agent System

## Global Rules
@config/global_rules.md

## Project Context
- Two accounts: EN (global) and JP (日本市場)
- All X operations use X API v2 Basic plan ($200/month)
- Impressions only via Playwright (own account pages)
- Human approval required before any post goes live
- All Telegram communication goes through Marc (COO)
- Task coordination via data/pipeline_state_{date}.json

## Agent Definitions
- @agents/marc.md — COO / Orchestrator / Reporter
- @agents/scout.md — Competitor Research
- @agents/strategist.md — Growth Strategy
- @agents/creator.md — Content Planning
- @agents/publisher.md — X API Posting & Outbound
- @agents/analyst.md — Metrics Collection

## Shared Conventions
- Date format: ISO 8601
- All times in JST
- Post IDs: {account}_{YYYYMMDD}_{slot}
- Log format: [YYYY-MM-DD HH:MM:SS] [AGENT] [LEVEL] message

## Tool Assignment (minimal per agent)
- Scout: X API read only
- Strategist: File read/write only
- Creator: File read/write only
- Publisher: X API write + media upload + rate limit counter
- Analyst: X API read + Playwright (impressions) + SQLite write
- Marc: Subagent invocation + file read/write + Telegram send

## Preferences
- Don't try to run scripts with bash tool. Write the script and tell me how to execute it, asking me for its output instead.
