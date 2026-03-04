# X-Agents Harness Architecture

## Three-Layer Model

```
Layer 1: Shell Entry Points
  run_pipeline.sh, run_task.sh
  Lock files, env setup, Claude invocation

Layer 2: Marc Orchestrator
  agents/marc.md (hub) + marc_pipeline.md / marc_publishing.md
  Task routing, subagent spawning, review loops, state tracking

Layer 3: Specialist Agents
  agents/*.md (skill files) + scripts/*.py (deterministic execution)
  Isolated execution, deterministic validation
```

## Harness = OS Analogy

Based on the agent harness pattern (Schmid 2026):

| Concept | Maps To |
|---|---|
| CPU | Claude model (reasoning engine) |
| RAM | Context window (per-invocation) |
| Operating System | Agent harness (shell scripts + validate.py + pipeline state) |
| Application | Agent instance (marc.md + task prompt) |
| File System | `data/` directory (JSON state files, SQLite) |
| IPC | File-based: agents write JSON, next agent reads it |

## Key Architectural Patterns

### Validation-First
Every agent output passes through `scripts/validate.py` before the pipeline continues. Deterministic checks catch schema violations, missing fields, and constraint failures.

### Iterative Retry (H3)
When a subagent fails, Marc reads the error, crafts a targeted retry prompt including the specific failure, and retries once. Errors become context for the retry — not just "try again" but "fix this specific issue."

### Human Gating
Content follows a strict status flow: `draft -> approved -> posted`. No content reaches X without human approval via Telegram.

### State Machine
`data/pipeline_state_{YYYYMMDD}.json` tracks the full lifecycle. Each task has an ID, status, timestamps, and output path. This enables resumability and audit.

### Progressive Disclosure
Marc's instructions are split across files:
- `marc.md` — Identity, task handling, agent team (~120 lines)
- `marc_pipeline.md` — Pipeline steps, loaded only during pipeline runs
- `marc_publishing.md` — Publishing steps, loaded only during publish runs
- `marc_schemas.md` — Schemas and formats, loaded on demand

### Specialist Isolation
Each `claude -p` invocation is a fresh context. Agents never share state through the context window — only through files. This prevents cross-contamination and makes each agent independently testable.

## File Layout

```
agents/
  marc.md              — Orchestrator hub (identity + task handling)
  marc_pipeline.md     — Pipeline Steps 1-13
  marc_publishing.md   — Publishing Steps P1-P8
  marc_schemas.md      — Schemas & report formats
  scout.md             — Competitor research
  strategist.md        — Growth strategy
  creator.md           — Content planning
  publisher.md         — X API posting
  analyst.md           — Metrics collection

scripts/
  run_pipeline.sh      — Entry point: lock + invoke Marc for pipeline
  run_task.sh          — Entry point: lock + invoke Marc for tasks
  scout.py             — X API data collection
  publisher.py         — X API posting + outbound
  analyst.py           — Metrics collection + SQLite
  validate.py          — Deterministic output validation
  db_manager.py        — SQLite operations
  telegram_send.py     — Telegram messaging
  telegram_bot.py      — Telegram bot (commands)

config/
  global_rules.md      — Engagement limits, posting constraints
  competitors.json     — Tracked accounts

data/
  pipeline_state_*.json  — Pipeline lifecycle state
  scout_report_*.json    — Daily competitor data
  strategy_*.json        — Daily growth strategies
  content_plan_*.json    — Daily content plans
  rate_limits_*.json     — Daily rate limit counters
  outbound_log_*.json    — Outbound engagement log
  metrics_*.json         — Daily metrics summaries
  metrics_history.db     — SQLite historical data
```

## Related Documentation

- [Agent Building Guidelines](guides/agent-building-guidelines.md) — How to build new agents: principles, templates, checklist
