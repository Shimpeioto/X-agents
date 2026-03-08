# X AI Beauty Growth Agent System

## Architecture

Marc operates as **Team Leader** using Claude Code Agent Teams (experimental).
The operator communicates with Marc via Telegram through two layers:

1. **Conversational Layer** (Anthropic API) — Fast, responsive. Marc receives messages, reasons about them, asks clarifying questions, and decides when to execute.
2. **Execution Layer** (Claude Code Agent Teams) — Marc spawns teammates (Scout, Strategist, Creator, Publisher, Analyst) for parallel work with shared task coordination.

Entry points:
- `scripts/telegram_bot.py` — Main bot (conversational + execution)
- `scripts/run_pipeline.sh` — Direct pipeline execution (fallback)
- `scripts/run_task.sh` — Direct task execution (fallback)

## Global Rules
@config/global_rules.md

## Documentation
- All project docs live in `docs/` (context, analysis, runbook, review)
- Spec, PRD, and compliance review live in `docs/specs/`
- Agent building guide: `docs/guides/agent-building-guidelines.md`

## Project Context
- Two accounts: EN (global) and JP (日本市場)
- All X operations use X API v2 Basic plan ($200/month)
- Impressions only via Playwright (own account pages)
- Human approval required before any post goes live
- All Telegram communication goes through Marc (COO)
- Task coordination via shared task list (Agent Teams) or data/pipeline_state_{date}.json

## Agent Definitions (Teammates)
- @agents/marc.md — COO / Team Leader
- @agents/marc_conversation.md — Conversational Marc (Anthropic API layer)
- @agents/scout.md — Competitor Research (teammate)
- @agents/strategist.md — Growth Strategy (teammate)
- @agents/creator.md — Content Planning (teammate)
- @agents/publisher.md — X API Posting (teammate)
- @agents/outbound.md — Community Engagement & Growth (teammate)
- @agents/analyst.md — Metrics Collection (teammate)

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
- Outbound: X API read (target data) + X API write (via publisher.py smart-outbound) + SQLite read (history)
- Analyst: X API read + Playwright (impressions) + SQLite write
- Marc: Teammate spawning + file read/write + Telegram send

## Preferences
- In interactive sessions (direct CLI use): Don't try to run scripts with bash tool. Write the script and tell me how to execute it, asking me for its output instead.
- In non-interactive sessions (telegram bot execution, run_task.sh, run_pipeline.sh): Execute ALL scripts directly using bash tool. The operator is not watching — you must run everything yourself.
