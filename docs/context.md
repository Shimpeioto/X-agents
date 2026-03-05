# Project Context Document
# Autonomous AI Agent System

**Purpose of this document**: Enable any third party to fully understand the project vision, decision history, current state, and deliverables without needing to read the full conversation transcript.

**Last updated**: March 5, 2026 (Session 23: Phase 5 E2E Testing — 20-Test Battery Complete)

---

## 1. The Big Picture

### 1.1 Vision

Build a **general-purpose system in which AI agents can think and act independently, cooperate with each other, and operate autonomously** — even while the operator is sleeping. The system should be adaptable to any task domain, not tied to a single use case.

This vision was directly inspired by the article *"I'm good at one thing. So my OpenClaw agent, Marc, automated the other 100 things"*, in which a podcaster built 11 specialized agents coordinated by a COO agent (Marc) that ran an entire podcast production pipeline overnight — from content creation to posting to analytics — all while the operator slept.

### 1.2 What This Is NOT

This is **not** a project to build a specific product (podcast automation, social media tool, etc.). The goal is to establish:

1. **An architectural pattern** for multi-agent autonomous systems
2. **A reusable framework** built on Claude Code + cron + Telegram that can be applied to any task domain
3. **Validated best practices** for agent coordination, error handling, memory persistence, and human-in-the-loop workflows

### 1.3 The Demo Project: X (Twitter) AI Beauty Growth

To validate the architecture in a real-world scenario, the first demonstration project is an autonomous X (Twitter) growth system for AI-generated beauty content. This demo was chosen because it exercises all the core capabilities the framework needs:

| Framework Capability | How the Demo Exercises It |
|---|---|
| Multi-agent coordination | 6 agents with dependency chains (Scout → Strategist → Creator) |
| External API integration | X API v2 for posting, engagement, and metrics |
| Scheduled autonomous operation | Overnight pipeline + distributed daytime posting |
| Human-in-the-loop at decision points | Content approval via Telegram before posting |
| Data-driven strategy adaptation | Daily metrics feed back into next day's strategy |
| Error handling & escalation | API failures, rate limits, anomaly detection |
| Persistent memory across sessions | CLAUDE.md for behavioral rules, SQLite for metrics |
| Reporting & communication | Telegram briefs, reports, alerts, and commands |

The X Beauty demo is a means to an end. The real deliverable is the proven architecture, patterns, and tooling that emerge from building it.

### 1.4 Future Applications

Once the framework is validated through the X Beauty demo, it can be applied to other domains within Shimpei's business interests, potentially including:

- AI content monetization across multiple platforms
- Automated market research and competitive intelligence
- Business operations automation for Amarry Technologies
- Any domain requiring coordinated autonomous agents

---

## 2. Who Is Building This

**Shimpei** — Founder & CEO of Amarry Technologies Inc. (Delaware C-Corporation, incorporated October 2025). He is a 31-year-old Japanese national based in Japan (currently in Kagoshima). The company is building UniModel, an AI model marketplace and intelligent routing system. This autonomous agent system is being developed to explore AI-driven automation capabilities and validate agent architectures that can be applied across the business.

**Key constraints**:
- Solo operator — no team, no co-founder
- Available ~1 hour/day for the demo project (7-9 AM JST morning window)
- Based in Japan (JST timezone), which affects pipeline scheduling
- Budget-conscious — prefers cost-efficient solutions over premium ones
- Has experience with prompt engineering, Claude Code, and AI tool evaluation

---

## 3. Conversation Timeline & Decision Log

The conversation spanned from **February 28, 2026 (04:00 UTC)** to **March 1, 2026 (~06:00 UTC)** across multiple sessions. The first three sessions focused on the general autonomous agent architecture. The remaining sessions applied that architecture to the X Beauty demo.

---

### Phase A: General Architecture Research

#### Session 1: Article Analysis & Framework Comparison (Feb 28, 04:00-04:40 UTC)

**Trigger**: Shimpei shared the OpenClaw article and stated his core intent clearly:

> *"I would like to build a system in which agents can act independently and cooperate with each other to suit my own tasks. I'm not trying to build the specific agents that are built in the article."*

He wanted to use Claude Code instead of OpenClaw, and asked for a clear analysis of what Claude Code can and cannot do.

**Key analysis delivered**:

8 core architectural principles were extracted from the article as framework-agnostic patterns:

1. **Single-responsibility agents** — each agent does one thing well
2. **Hierarchical coordination** — a COO agent orchestrates all others
3. **Cron-based scheduling** — time-triggered execution for overnight pipelines
4. **Persistent memory** — agents retain knowledge across sessions
5. **Skill files** — reusable instruction sets that define agent behavior
6. **Error compounding awareness** — upstream failures cascade; must be handled
7. **Human-in-the-loop** — human approval at critical decision points
8. **Messaging-based communication** — real-time reporting via Telegram/WhatsApp/Slack

Feature-by-feature comparison of Claude Code vs OpenClaw across 7 categories:

| Capability | Claude Code | OpenClaw |
|---|---|---|
| Scheduled execution | ⚠️ Needs OS cron | ✅ Built-in daemon |
| Multi-agent coordination | ✅ Subagents + orchestrator script | ✅ Native multi-agent |
| Persistent memory | ✅ CLAUDE.md (native) + filesystem | ✅ Built-in state management |
| Skill files | ✅ Markdown-based skill system | ✅ Native skill system |
| External tool integration | ✅ Full bash/Python access | ✅ Built-in tool framework |
| Error handling | ⚠️ Must build in orchestrator | ✅ Built-in error handling |
| Always-on operation | ❌ Session-based (needs cron) | ✅ Daemon-based |
| Messaging channels | ❌ Must build custom bot | ✅ Native Telegram/WhatsApp/Slack |

**Core finding**: Claude Code handles ~80% of requirements natively. The two gaps are:
- **Scheduled execution**: Claude Code is a CLI tool (starts → executes → exits). It needs an external trigger (cron, GitHub Actions) to run at 2 AM.
- **Messaging channels**: No native Telegram/WhatsApp integration. Requires a custom Python bot (~50-100 lines).

**Decision 1**: Claude Code + cron is sufficient for the autonomous agent framework. OpenClaw is unnecessary.

**Deliverable**: `autonomous-agent-system-analysis.md`

#### Session 2: Infrastructure & Scheduling Deep Dive (Feb 28, 04:37-05:00 UTC)

**Shimpei's follow-up questions**:

1. *"Why is a Mac Mini necessary?"*

   Answer: It's not specifically a Mac Mini — any always-on compute works. The core issue is that **something must be awake at 2 AM to trigger the agents**. Claude Code is not a daemon; if the operator's laptop is closed, nothing runs.

   | Option | Cost | Notes |
   |---|---|---|
   | Mac Mini | ~$600 one-time | Physical device, needs power/internet |
   | VPS (Hetzner, Vultr) | $5-20/month | Cloud, no physical hardware |
   | GitHub Actions | Free (2,000 min/month) | No server at all |

2. *"Are there issues with OS cron?"*

   Cron itself is reliable (50-year-old tech). The concerns are Claude Code-specific:
   - **`--dangerously-skip-permissions`**: Required for unattended execution (no human to click "approve" at 2 AM). Means agent can execute any command.
   - **No native dependency chains**: If Agent A fails, cron still fires Agent B at its scheduled time. Mitigated by an orchestrator script that runs agents sequentially with error checking.
   - **No built-in alerting**: Cron doesn't notify on failure. Mitigated by Telegram notifications from the orchestrator.
   - **Session isolation**: Each `claude -p` call is a fresh session. Agents communicate via shared filesystem (JSON, SQLite), not in-memory state.

**Decision 2**: Use VPS for always-on compute. Use cron with an orchestrator shell script for dependency management.

#### Session 3: Messaging Integration (Feb 28, 13:00 UTC)

**Shimpei's question** (in Japanese): "If not using OpenClaw, do I need to develop a custom solution for Telegram/WhatsApp messaging?"

**Answer**: Yes, but it's far simpler than expected:
- **Telegram Bot**: ~50-100 lines Python using `python-telegram-bot` + Anthropic SDK. Free. Full-featured.
- **WhatsApp**: Much harder — requires Meta Business account, review process, monthly fees, or unofficial libraries with BAN risk.

**Decision 3**: Use Telegram Bot for all human-agent communication. Skip WhatsApp.

**Architecture pattern established**:
```
cron → claude -p (batch pipeline) → results to filesystem
Telegram Bot (always-on Python daemon) → receives human messages → Claude API → responds
```

This pattern is framework-agnostic — it works for any task domain, not just X Beauty.

---

### Phase B: Demo Project — X (Twitter) AI Beauty Growth

#### Session 4: Demo Project Design (Feb 28, 16:20-16:40 UTC)

**Shimpei's request**: "As a demonstration, let's build an agent that can autonomously operate X. Specifically, AI Beauty theme. Start from scratch, gain 10,000 followers as quickly as possible."

This was explicitly framed as a demonstration — a real-world test of the autonomous agent architecture.

**Clarification Q&A**:

| Question | Shimpei's Answer |
|---|---|
| X API access? | No API — use browser automation (Playwright) |
| Post language? | Create both EN and JP accounts, A/B test which works better |
| Outbound automation risk tolerance? | Accept BAN risk, automate fully |
| Posts per day? | 3-5 (standard) |
| Media type? | Static AI images only (no video) |
| Competitor accounts? | Already has benchmark candidates |

**Design delivered**: 6-agent system (Scout, Strategist, Creator, Publisher, Analyst, Commander) applying all 8 architectural principles from the framework research. Included pipeline schedule, shared state architecture, and 5-phase implementation plan.

**Deliverable**: `x-ai-beauty-agent-config.md` (v1.0)

#### Session 5: COO Agent & X API Pivot (Mar 1, 02:50 UTC)

**Shimpei raised two issues**:

1. **Missing COO agent**: The v1.0 design had a "Commander" that only reported — it didn't orchestrate. Shimpei correctly identified this: *"In the article, Marc (COO) coordinates agents, holds meetings, and reports to me."* The COO pattern from the original article — the architectural principle of hierarchical coordination — was not properly implemented.

2. **X API preference**: *"If it's possible to do it officially via X API, that would be better than Playwright."* This reversed the initial browser automation approach.

**X API research conducted**:
- Free: $0 (write-only, 500 posts/month)
- Basic: $200/month (15K reads, 50K writes)
- Pro: $5,000/month (1M reads, full metrics including impressions)
- Enterprise: $42,000+/month

**Critical limitation**: Basic plan only provides `public_metrics` (likes, RTs, replies). Impression counts require `non_public_metrics` at Pro ($5,000/month).

**Decision 4**: Hybrid strategy — X API for all operations + Playwright only for impression scraping from own account pages. $200/month with near-zero BAN risk.

**Decision 5**: Add Marc (COO) as a true orchestrator — pipeline control, War Room reviews, error handling, Telegram commands, daily retrospectives. This properly implements the hierarchical coordination principle.

**Deliverable**: `x-ai-beauty-agent-config-v2.0-en.md`

#### Session 6: Reporter Merge & Architecture Refinement (Mar 1, 03:45-04:30 UTC)

**Shimpei's argument**: Marc should own reporting, not delegate it to a separate Reporter agent. His reasoning: *"The article states that the COO is also creating the report. Marc has the full context from orchestration."*

**Analysis**: Correct. A separate Reporter is an unnecessary indirection. The value of a status report is judgment — what to highlight, what to deprioritize, what decisions to escalate. That judgment comes from orchestration context that only the COO holds. A separate Reporter would need the same context re-loaded, producing worse output at additional cost. Reporting is the communication layer of orchestration, not a separate domain.

**Decision 6**: Merge Reporter into Marc. Agent count: 7 → 6.

**Language fix**: Claude had been responding in Japanese since one early Japanese message. Shimpei corrected this.

**Decision 7**: Documents in English with JP market-specific terms preserved in 日本語.

**Deliverable**: `x-ai-beauty-agent-config-v2.1-en.md`

#### Session 7: CLAUDE.md Memory Integration (Mar 1, ~05:00 UTC)

**Shimpei's input**: Pointed out that Claude Code has built-in memory functionality via CLAUDE.md files, providing documentation link.

**Key finding**: Claude Code's CLAUDE.md provides a 4-tier hierarchy (enterprise → project → user → local) with auto-loading at launch and `@path` import syntax. This directly addresses the "persistent memory" principle from the framework research.

**Impact on the general framework pattern**:
- Agent instructions can be auto-loaded via CLAUDE.md imports (no manual `cat` commands)
- Behavioral rules learned from errors persist across sessions automatically
- Structured data stays in JSON/SQLite for Python scripts
- **This is a reusable pattern**: any future project using this framework gets the same memory architecture

**Decision 8**: CLAUDE.md for behavioral instructions; JSON/SQLite for machine-parseable data. No duplication.

#### Session 8: Specification & PRD (Mar 1, ~05:30 UTC)

**Shimpei's request**: Create proper specification and PRD documents for the demo project.

**Decision 9**: Treat the existing config document as the Technical Specification (updated to v2.2 with 7 new sections covering auth, config schemas, cron definitions, env vars, memory architecture, testing, and deployment). Create a separate PRD covering the product layer.

**Deliverables**: `specs/x-ai-beauty-spec-v2.3.md` + `specs/x-ai-beauty-prd-v1.md`

#### Session 9: Agent Design Principles & Phase 0 Runbook (Mar 1-2, ~15:00-02:00 UTC)

**Shimpei's input**: Shared "Lessons from Building Claude Code: Seeing like an Agent" article with 6 core principles for building effective AI agents.

**Principles integrated**: (1) Minimal tool count per agent — tool assignment table created, (2) Structured elicitation over free text — Telegram command interface, (3) Task-based subagent coordination — `pipeline_state_{date}.json` replaces rigid sequences, (4) Progressive disclosure — agents discover context incrementally, (5) Revisit tool assumptions weekly, (6) Add capabilities without adding tools.

**Impact**: Spec updated to v2.3 (Section 14: Agent Design Principles, Section 13.5: Progressive Disclosure). PRD Section 7 added.

**Blocking decisions resolved**:
- **OQ-3**: Use existing X accounts (not fresh ones)
- **OQ-6**: Vultr Tokyo VPS ($12/mo) — selected for JST timezone proximity
- **OQ-7**: Claude Max subscription ($100/mo)

**Phase 0 Runbook created**: 12-step VPS-based environment setup guide (later revised in Session 10).

**File cleanup**: 10 files reduced to 5 — all superseded config versions deleted.

#### Session 10: Local-First Development & Compliance Review (Mar 2, ~02:00+ UTC)

**Shimpei's key insight**: VPS is only needed for autonomous operation — not during development. During development, you sit at your own machine and trigger agents from the CLI. VPS deployment should be deferred to when all agents are proven reliable.

**Decision 10**: Local-first development. Phases 0-4 run on your own machine (CLI). VPS provisioning moves to Phase 6. Autonomous cron operation is Phase 7.

**Phase 0 Runbook rewritten**: Completely replaced VPS-centric 12-step guide with local development setup (9 steps). No server provisioning, hardening, or cron setup.

**Implementation phases restructured**: 5 phases → 7 phases:
- Phases 0-4: Your machine (build, test, iterate)
- Phase 5: Claude hybrid agent conversion (Analyst, Scout, Publisher intelligence)
- Phase 6: VPS deployment (provision, copy project, install cron)
- Phase 7: Autonomous operation (cron triggers agents overnight)

**X Developer Terms compliance review**: Full review of Developer Agreement, Developer Policy, and Automation Rules against our project design.

**Decision 11**: Record compliance concerns without making spec changes — review each issue during the relevant implementation phase.

**7 issues identified**:
- 🔴 Automated likes prohibited (Phase 3)
- 🔴 Automated follows risk bulk/aggressive violation (Phase 3)
- 🔴 Cold outbound replies require prior user interaction (Phase 3)
- 🔴 Playwright scraping is banned non-API automation (Phase 4)
- 🟡 Bot account labeling required (Phase 0/3)
- 🟡 Cross-account content must be genuinely unique (Phase 2)
- 🟡 Use case description is binding (Phase 0)

**Deliverable**: `specs/x-developer-terms-compliance-review.md`

#### Session 11: Phase 0 Execution & GitHub Setup (Mar 3, ~00:00+ UTC)

**Phase 0 runbook executed**: All 9 steps completed successfully. 30/30 health check passed — CLI tools, X API credentials, Telegram bot, project directory structure, CLAUDE.md hierarchy, and config files all verified working.

**Git initialization**: Repository initialized with comprehensive `.gitignore` excluding secrets (`config/accounts.json`, `.env`, `*.sqlite`, etc.). `accounts.example.json` template created for safe credential sharing.

**GitHub repository created**: `https://github.com/Shimpeioto/X-agents` (private). Initial commit pushed with full project structure. Phase 0 is now complete and version-controlled.

**Decision 13**: Initialize git and push to GitHub at Phase 0 completion — establishes version control before any agent development begins.

#### Session 12: Phase 1 Specification & PRD (Mar 3, 2026)

**Phase 1 Spec and PRD written**: Full technical specification and product requirements for Phase 1 (Scout + Strategist + Marc Foundation).

**Key architecture decision — Marc-as-Claude agent**:

The original parent spec assumed a Python orchestrator script (`run_pipeline.py`) would sequence agents. This was rearchitected: Marc is now a **Claude agent** invoked via `scripts/run_pipeline.sh` (thin shell wrapper), with `scripts/validate.py` providing deterministic validation as a feedback loop.

| Component | Role |
|---|---|
| `scripts/run_pipeline.sh` | Thin shell wrapper — sets date, checks `.pipeline.lock`, invokes `claude -p` with Marc's skill file |
| `agents/marc.md` | Marc's full instruction set — orchestration logic, sequencing, error recovery, semantic cross-validation |
| `scripts/validate.py` | Deterministic pass/fail validation (scout, strategist, cross modes) — Marc calls this via bash tool |

**Rationale**: Orchestration involves judgment (error recovery, cross-validation reasoning, adaptive retry prompts) — Claude's strength. Deterministic checks (schema validation, field presence, data bounds) stay in Python. This avoids a Phase 2 rewrite since the parent spec already defines Marc as a Claude agent in all cron jobs.

**Decision 14**: Marc implemented as a Claude agent (`agents/marc.md`) with `scripts/validate.py` for deterministic validation and `scripts/run_pipeline.sh` as the entry point. Replaces the originally-assumed Python orchestrator script.

**Decision 15**: Strategist writes only the dated file (`strategy_{YYYYMMDD}.json`). Marc copies to `strategy_current.json` only after all validations pass — preventing unvalidated data from corrupting the current strategy.

**Parent docs updated for consistency**:
- Parent spec (`x-ai-beauty-spec-v2.3.md`): project structure updated, Section 11.2 annotated as Phase 6+, locking recommendation extended, Phase 6 checklist annotated
- Parent PRD (`x-ai-beauty-prd-v1.md`): F7 note updated to link Phase 1 spec
- Review doc (`review.md`): Issues 3.15 and 3.16 annotated with Phase 1 resolution status

**Self-review found and fixed 10 issues** (2 HIGH, 2 MEDIUM, 6 LOW):
- **HIGH**: `strategy_current.json` write conflict (Strategist vs Marc) — resolved: Marc is sole writer after validation
- **HIGH**: Strategist invocation mechanism ambiguous (`$(cat)` vs progressive disclosure) — resolved: standardized on progressive disclosure
- **MEDIUM**: `run_pipeline.sh` missing `.pipeline.lock` implementation — added
- **MEDIUM**: `competitors.json` schema missing — added cross-reference to parent spec Section 10.2
- **LOW**: Date format conversion undocumented, hardcoded competitor counts, `--dry-run` undefined, Scout output path convention, Phase 0 prerequisite missing from PRD, `--dangerously-skip-permissions` security note missing — all fixed

**Deliverables**: `specs/phase-1-spec.md` (v1.0) + `specs/phase-1-prd.md` (v1.0)

#### Session 20: Architecture Review & Agent Building Guidelines (Mar 5, 2026)

**Post-Phase 4 architecture documentation sprint**: With all 6 agents implemented and tested through Phase 4, codified the implicit patterns into explicit documentation.

**Architecture Review** (completed before this session):
- Split `marc.md` (~400+ lines) into hub + 3 reference files following Progressive Disclosure principle: `marc.md` (hub, ~131 lines), `marc_pipeline.md` (Steps 1-13, ~201 lines), `marc_publishing.md` (Steps P1-P8, ~138 lines), `marc_schemas.md` (schemas & formats, ~140 lines)
- Added metadata comment headers to all 9 agent files (name, role, invocation, modes, inputs, outputs, dependencies)
- Created `docs/harness.md` — Three-layer architecture model (Shell → Marc → Specialists), OS analogy (Schmid 2026), 5 key patterns (Validation-First, H3 Retry, Human Gating, State Machine, Progressive Disclosure), file layout reference

**Agent Building Guidelines** (this session):
- Created `docs/guides/agent-building-guidelines.md` (~1000 lines) — comprehensive guide for building new agents
- 10 sections: Principles (8), Decision Framework, Agent Anatomy (template included), Script Companion (Python template), I/O Contract (file naming, data flow map), Orchestration Integration (5 registration locations), Validation & Error Handling (7 check levels, H3 protocol), Testing (6-step pipeline testing sequence), New Agent Checklist, References (7 articles)
- Updated `docs/harness.md` with "Related Documentation" link to the guide
- Updated `CLAUDE.md` Documentation section with guide reference

**Deliverables**: `docs/guides/agent-building-guidelines.md`, updated `docs/harness.md`, updated `CLAUDE.md`

#### Session 21: Phase 5 Spec & PRD — Claude Hybrid Agent Conversion (Mar 5, 2026)

**Deep exploration of all three Python-only agents** (Scout, Publisher, Analyst) to identify where Claude reasoning adds value vs. where Python should stay.

**Scout analysis**: Found 36.9% reply contamination (151/409 sampled tweets are @replies), hardcoded trending threshold (`like_count >= 100`) returns zero results, 59 unfiltered new accounts mixing bots with 200K-follower accounts, impression data collected but never used, 92.7% of competitors use zero hashtags.

**Publisher analysis**: `random.choice(reply_templates)` with no semantic matching, always targets `recent_tweets[0]` regardless of content, no relevance filtering, identical error logging for all failure types.

**Analyst analysis**: Zero interpretation layer — computes only `hours_after_post`, `engagement_rate` (always NULL from API), and `followers_change`. Marc manually owns anomaly detection, report composition, and A/B test evaluation in Step P8.

**Approved conversion plan** — "Claude Brain, Python Hands":
- Analyst Intelligence Mode: Claude reads raw metrics, detects anomalies, composes daily report. Python collect/summary/import unchanged.
- Scout Intelligence Mode: Claude runs `scout.py --raw --compact`, analyzes compact output (457KB→30KB), writes enriched report with `analysis` section (backward compatible).
- Publisher Smart Outbound Mode: Claude reads target tweets via new `publisher_outbound_data.py`, selects relevant tweets, crafts contextual replies, writes outbound plan. New `smart-outbound` subcommand executes plan. Post subcommand unchanged.
- All three have fallback to Phase 4 behavior if Claude fails.

**Phase renumbering**: Phase 5 = Claude Hybrid Agent Conversion, Phase 6 = VPS Deployment (was 5), Phase 7 = Autonomous Operation (was 6). Total phases: 7.

**Deliverables**: `docs/specs/phase-5-spec.md` (1456 lines), `docs/specs/phase-5-prd.md` (258 lines), updated `docs/context.md`

---

#### Session 22: Phase 5 Implementation — Claude Hybrid Agent Conversion (Mar 5, 2026)

**Implemented all three sub-phases** of the "Claude Brain, Python Hands" hybrid agent conversion:

**Sub-Phase 1 — Analyst Intelligence**:
- `agents/analyst.md` — Added "Intelligence Mode" section (Steps 1-4: read inputs, analyze per account, outbound effectiveness, compose report)
- `scripts/validate.py` — Added `validate_analyst_report()` (8 checks), `validate_scout_analysis()` (6 checks), `validate_outbound_plan()` (7 checks) + CLI routing for all three
- `agents/marc_publishing.md` — Replaced Step P8 with P8a (Claude subagent) → P8b (validate) → P8c (send report + alerts via Telegram)

**Sub-Phase 2 — Scout Intelligence**:
- `scripts/scout.py` — Added `--raw`/`--compact` CLI flags, `compute_pre_analysis()` (reply contamination, impression engagement, dynamic trending threshold, hashtag usage), `compact_report()` (457KB→~30KB)
- `agents/scout.md` — Added "Daily Intelligence Mode" section (Steps 1-3: collect raw+compact, analyze using _pre_analysis stats, write enriched backward-compatible report)
- `agents/marc_pipeline.md` — Replaced Step 2 with Claude Scout subagent invocation + H3 retry + fallback to plain `python3 scripts/scout.py`

**Sub-Phase 3 — Publisher Smart Outbound**:
- `scripts/publisher_outbound_data.py` — **New file** (~120 lines): `OutboundDataFetcher` class, fetches target account info + 5 recent tweets, JSON output to stdout
- `scripts/publisher.py` — Added `run_smart_outbound()` function + `smart-outbound` CLI subcommand (reads Claude-generated plan, executes with same rate limits/delays)
- `agents/publisher.md` — Added "Smart Outbound Mode" section (Steps 1-4: read inputs, fetch target data, analyze and plan, write outbound plan)
- `agents/marc_publishing.md` — Replaced Step P4 with P4a (Claude subagent generates plan) → P4b (validate) → P4c (publisher.py smart-outbound executes) + fallback to legacy outbound

**Files modified** (9): `agents/analyst.md`, `agents/scout.md`, `agents/publisher.md`, `agents/marc_pipeline.md`, `agents/marc_publishing.md`, `scripts/scout.py`, `scripts/publisher.py`, `scripts/validate.py`, `docs/context.md`
**Files created** (1): `scripts/publisher_outbound_data.py`
**Files unchanged** (as designed): `scripts/analyst.py` — Python collect/summary/import stays as-is

**Deliverables**: All code changes per `docs/specs/phase-5-spec.md` §5.1-5.9.

---

### Session 23 — Phase 5 E2E Testing: 20-Test Battery Complete (March 5, 2026)

**Goal**: Execute the full 20-test E2E battery defined in `docs/specs/phase-5-spec.md` §8, validating all Phase 5 Claude hybrid agent conversions end-to-end.

**Test Phases**:
- **Phase A (Dry-Run / Script-Level)**: Tests 8, 15, 16 — Scout `--raw --compact` produces 15KB compact file with `_pre_analysis`, publisher rate limits enforced correctly, legacy outbound fallback works
- **Phase B (API-Level)**: Test 12 — `publisher_outbound_data.py` fetches real target data, returns valid JSON with user info + recent tweets
- **Phase C (Claude Subagent Intelligence)**: Tests 1-7, 9-11, 13-14, 17 — All Claude intelligence modes verified (Analyst Intelligence, Scout Intelligence, Publisher Smart Outbound), validators accept enriched outputs, cross-check passes
- **Phase D (Full E2E Pipeline)**: Tests 18-20 — Full pipeline with Claude subagents, live posting (8 tweets: 4 EN + 4 JP, Day 2), fallback resilience confirmed

**Issues Found & Resolved**:
- Schema drift between Claude output and `validate.py` — validators updated to accept both `string` and `null` for optional fields (`anomaly_detail`, `reasoning`)
- Null handling in outbound plans — `validate_outbound_plan` relaxed to accept `null` for optional `reply_to` and `reasoning` fields when target is skipped
- X API 402 (Payment Required) during testing — intermittent, resolved on retry

**Test Artifacts Created**:
- `scripts/run_phase5_tests.sh` — Phase A+B test runner
- `scripts/run_phase5_tests_c.sh` — Phase C test runner (Claude subagents)
- `scripts/run_phase5_tests_d.sh` — Phase D test runner (full E2E + live posting)
- `data/scout_report_enriched_test.json` — Fixture for Claude intelligence tests
- `data/scout_report_fallback_test.json` — Fixture for fallback resilience tests
- `data/strategy_fallback_test.json` — Fixture for fallback testing
- `data/strategy_test_enriched.json` — Fixture for enriched strategy testing

**Live Posts**: 4 EN + 4 JP tweets posted successfully (Day 2, March 5, 2026)

**Result**: **20/20 PASS** — All tests passed. Phase 5 complete.

---

## 4. Decision Summary

### Framework-Level Decisions (Apply to All Future Projects)

| # | Decision | Rationale |
|---|---|---|
| D1 | Claude Code + cron as the agent execution framework | Handles 80% natively; cron fills scheduling gap; avoids dependency on OpenClaw |
| D2 | VPS for always-on compute (Phase 6 deployment) | Cheaper than hardware ($12/mo Vultr Tokyo); only needed for autonomous operation |
| D3 | Telegram Bot for human-agent communication | Simple (~50 lines Python), free, feature-rich; universal across any project |
| D8 | CLAUDE.md for persistent behavioral memory | Native auto-loading; rules persist across sessions; no custom code needed |

### Demo-Specific Decisions (X Beauty Project)

| # | Decision | Rationale |
|---|---|---|
| D4 | X API Basic + Playwright hybrid | Official API for safety ($200/mo); Playwright only for impressions. ⚠️ Playwright may be removed per compliance review |
| D5 | Marc (COO) as orchestrator agent | Implements hierarchical coordination principle from article |
| D6 | Merge Reporter into Marc (7→6 agents) | COO already holds full context; separate Reporter loses judgment |
| D7 | English docs with JP terms preserved | Operator preference |
| D9 | Separate PRD + Technical Spec | Config = spec (how); PRD = product layer (why, success criteria) |
| D10 | Local-first development; VPS deferred to Phase 6 | VPS only needed for autonomous operation; development uses your own machine + CLI |
| D11 | Log compliance concerns, resolve during implementation | Avoids premature spec changes; each issue reviewed at relevant phase |
| D12 | Accept X Terms risks for likes/follows/replies/Playwright | Risk accepted for all 4 critical compliance issues — implement with awareness; monitor for enforcement changes |
| D13 | Git + GitHub at Phase 0 completion | Version control established before agent development; private repo with secrets excluded via `.gitignore` |
| D14 | Marc as Claude agent + `validate.py` + `run_pipeline.sh` | Orchestration = judgment (Claude's strength); deterministic checks = Python; avoids Phase 2 rewrite |
| D15 | Marc is sole writer of `strategy_current.json` | Prevents unvalidated Strategist output from corrupting the current strategy file |

---

## 5. The Framework Architecture (Reusable Pattern)

This is the general-purpose architecture that emerged from the research and is being validated through the X Beauty demo:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENT FRAMEWORK                │
│                                                              │
│  ┌─────────┐     ┌──────────────────────────────────────┐   │
│  │  cron   │────▶│  Orchestrator Script (entry point)    │   │
│  └─────────┘     └──────────────┬───────────────────────┘   │
│                                  │                           │
│                                  ▼                           │
│                    ┌─────────────────────────┐               │
│                    │  COO Agent (Marc)        │               │
│                    │  - Pipeline control      │               │
│                    │  - Agent sequencing      │◀──┐           │
│                    │  - Error handling        │   │           │
│                    │  - War Room reviews      │   │  Telegram │
│                    │  - Human communication   │───┤  Bot      │
│                    │  - Rule updates          │   │  (daemon) │
│                    └────────┬────────────────┘   │           │
│                             │                     │           │
│              ┌──────────────┼──────────────┐     │           │
│              ▼              ▼              ▼      │           │
│         ┌────────┐    ┌────────┐    ┌────────┐   │           │
│         │Agent 1 │    │Agent 2 │    │Agent N │   └──▶[HUMAN] │
│         │(domain │    │(domain │    │(domain │               │
│         │specific)│   │specific)│   │specific)│              │
│         └───┬────┘    └───┬────┘    └───┬────┘               │
│             │             │             │                     │
│             ▼             ▼             ▼                     │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Shared State Layer                       │    │
│  │  CLAUDE.md (behavioral rules, auto-loaded)           │    │
│  │  JSON files (agent-to-agent data exchange)           │    │
│  │  SQLite (structured metrics & history)               │    │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  Tech stack: Claude Code CLI + cron + Telegram Bot +         │
│              CLAUDE.md memory + SQLite + JSON + Python        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key principles** (from the original article, validated and refined):

1. **Single-responsibility agents** — each agent does one thing well
2. **Hierarchical coordination via COO** — one agent orchestrates all others and owns human communication
3. **Cron-triggered batch pipelines** — overnight execution, no always-listening daemon needed
4. **Persistent memory via CLAUDE.md** — behavioral rules auto-loaded; learned knowledge persists
5. **Filesystem-based shared state** — agents communicate via JSON/SQLite, not in-memory
6. **Human-in-the-loop at decision points** — approval gates before irreversible actions
7. **Error handling with classification** — auto-retry vs. escalate vs. halt based on error type
8. **Telegram as the single communication channel** — reports, alerts, commands, all unified
9. **Hybrid agents ("Claude Brain, Python Hands")** — Agents that need both deterministic execution (API calls, rate limits, data storage) AND reasoning (analysis, filtering, composition) use a hybrid pattern: Python handles execution, Claude handles intelligence. Failures degrade gracefully to Python-only behavior.

---

## 6. Demo Project: X Beauty System

### 6.1 Agent Architecture

```
Human (Shimpei)
└── Telegram (unified communication)
    └── 🎖️ Marc (COO / Orchestrator / Reporter)
        ├── 🔍 Scout ──────── Competitor research & trend analysis      [X API v2 + Claude Intelligence]
        ├── 📊 Strategist ─── Data-driven growth strategy               [Claude Code]
        ├── ✍️ Creator ─────── Content drafting & image prompts          [Claude Code]
        ├── 📢 Publisher ──── Posting [X API v2] + Smart outbound       [X API v2 + Claude Intelligence ⚠️]
        └── 📈 Analyst ────── Metrics collection + daily reporting      [X API + Claude Intelligence]
```

⚠️ = X Developer Terms compliance concerns logged. See `specs/x-developer-terms-compliance-review.md`.

#### 6.1.1 Hybrid Agent Pattern (Phase 5)

Three agents operate as "Claude Brain, Python Hands" hybrids. Python scripts handle all API calls, rate limiting, and data storage. Claude subagents add intelligence: anomaly detection (Analyst), reply filtering & executive summaries (Scout), contextual engagement planning (Publisher outbound). If Claude fails, each agent falls back to Phase 4 Python-only behavior. Post publishing remains Python-only (safety-critical, human-gated). See `docs/specs/phase-5-spec.md` §4.1 for the full pattern.

### 6.2 Key Details

- **Goal**: 0 → 10,000 followers on at least one account (EN or JP)
- **Tech stack**: Claude Code CLI + cron + X API v2 (Basic $200/mo) + Playwright (under compliance review) + python-telegram-bot + SQLite + CLAUDE.md
- **Monthly cost**: ~$227-245/month (X API $200, Claude subagent tokens ~$27-45). Vultr VPS ($12/mo) added at Phase 6 deployment.
- **Daily pipeline**: 0:30 AM pipeline start → 7:00 AM morning brief → 7-9 AM human approval → 9 AM-9 PM posting & engagement → 11 PM metrics → 11:30 PM daily report → 11:45 PM retrospective
- **Estimated timeline**: ~22 days from Phase 0 start to autonomous operation (Phases 0-5 local development, Phase 6 VPS deployment, Phase 7 autonomous). Updated from ~19 days after Phase 5 (Claude Hybrid Agent Conversion) was added.

### 6.3 Open Questions (Unresolved)

| # | Question | Impact | Status |
|---|---|---|---|
| OQ-1 | Which AI image generation tool (Midjourney, SD, Flux)? | Affects Creator's prompt format | Open |
| OQ-2 | Initial competitor list (10+ accounts)? | Blocks Phase 1 testing | **Resolved: 41 unique accounts (26 EN + 17 JP, 2 overlap)** |
| OQ-3 | Fresh X accounts or existing ones? | Affects Phase 0 setup | **Resolved: Use existing accounts** |
| OQ-4 | Monthly budget ceiling above $350? | Determines scope constraints | Open |
| OQ-5 | Operate on weekends/holidays? | Affects scheduling | Open |
| OQ-6 | VPS provider preference? | Affects Phase 6 deployment | **Resolved: Vultr Tokyo ($12/mo)** |
| OQ-7 | Claude subscription tier (Pro $20 vs Max $100)? | Affects cost and capability | **Resolved: Claude Max ($100/mo)** |
| OQ-8 | Backup destination (S3, Google Drive, local)? | Affects Phase 4 implementation | Open |

**Updated monthly cost**: ~$227-245/month (X API $200, Claude subagent tokens ~$27-45). Vultr VPS ($12/mo) added at Phase 6.

---

## 7. Deliverables Directory Structure

```
./
│
├── .gitignore                              ← GIT IGNORE RULES
│   Excludes: secrets (accounts.json, .env), databases, logs,
│             media files, node_modules, OS files
│
├── CLAUDE.md                               ← CLAUDE CODE PROJECT CONFIG
│   Auto-loaded at session start. References agents/ and config/.
│
├── docs/                                   ← PROJECT DOCUMENTATION
│   ├── context.md                          ← THIS FILE
│   │   Purpose: Third-party orientation document
│   │   Scope:   Full project (framework + demo)
│   │
│   ├── autonomous-agent-system-analysis.md ← FRAMEWORK ANALYSIS
│   │   Purpose: OpenClaw vs Claude Code comparison
│   │   Contains: 8 architectural principles, feature comparison
│   │   Status:  Complete (historical reference)
│   │
│   ├── phase-0-runbook.md                  ← PHASE 0 SETUP GUIDE
│   │   Purpose: Local development environment setup
│   │   Contains: 9 steps, test scripts, health check
│   │   Status:  ✅ Complete — 30/30 health check passed
│   │
│   ├── competitor-accounts.md              ← COMPETITOR REFERENCE
│   │   Purpose: Human-readable competitor account list
│   │   Contains: 26 EN + 17 JP accounts (41 unique, 2 overlap)
│   │   Status:  Current
│   │
│   ├── review.md                           ← REVIEW NOTES
│   │
│   ├── harness.md                          ← ARCHITECTURE DOCUMENT
│   │   Purpose: Three-layer architecture model, OS analogy, key patterns
│   │   Contains: Shell → Marc → Specialists model, file layout reference
│   │   Status:  Current
│   │
│   ├── guides/                             ← PRACTICAL GUIDES
│   │   └── agent-building-guidelines.md   ← AGENT BUILDING GUIDE
│   │       Purpose: How to build new agents for the system
│   │       Contains: 8 principles, decision framework, templates, I/O contracts,
│   │                 validation patterns, testing sequence, new-agent checklist
│   │       Status:  Current
│   │
│   ├── procedures/                         ← OPERATIONAL PROCEDURES
│   │   └── add-competitor.md              ← ADD/REMOVE COMPETITOR PROCEDURE
│   │       Purpose: Step-by-step guide for adding/removing competitor accounts
│   │       Contains: Duplicate check, JSON template, validation commands,
│   │                 removal procedure, example walkthrough, checklist
│   │       Status:  Current
│   │
│   └── specs/                              ← SPECIFICATIONS & COMPLIANCE
│       ├── x-ai-beauty-spec-v2.3.md       ← TECHNICAL SPECIFICATION (Demo)
│       │   Purpose: How to build the X Beauty demo system
│       │   Contains: Agent roster, API strategy, pipeline, config schemas,
│       │             cron, auth, memory, agent design, testing, deployment
│       │   Status:  Current (v2.4, updated for Phase 1 consistency)
│       │
│       ├── x-ai-beauty-prd-v1.md          ← PRODUCT REQUIREMENTS (Demo)
│       │   Purpose: What to build and why
│       │   Contains: Goals, user stories, features, launch criteria
│       │   Status:  Current (v1.1, F7 updated to link Phase 1)
│       │
│       ├── phase-1-spec.md                ← PHASE 1 TECHNICAL SPECIFICATION
│       │   Purpose: How to build Phase 1 (Scout + Strategist + Marc)
│       │   Contains: Agent definitions, file specs, output schemas,
│       │             validation rules, testing strategy, edge cases
│       │   Status:  Current (v1.0)
│       │
│       ├── phase-1-prd.md                 ← PHASE 1 PRODUCT REQUIREMENTS
│       │   Purpose: What Phase 1 delivers and why
│       │   Contains: Goals, success criteria, user stories, exit criteria,
│       │             risks, timeline, feature-to-spec mapping
│       │   Status:  Current (v1.0)
│       │
│       ├── phase-5-spec.md                 ← PHASE 5 TECHNICAL SPECIFICATION
│       │   Purpose: How to build Phase 5 (Claude Hybrid Agent Conversion)
│       │   Contains: 3 sub-phases (Analyst, Scout, Publisher intelligence),
│       │             hybrid pattern, validation rules, E2E test battery
│       │   Status:  Current (v1.0)
│       │
│       ├── phase-5-prd.md                  ← PHASE 5 PRODUCT REQUIREMENTS
│       │   Purpose: What Phase 5 delivers and why
│       │   Contains: Goals, success criteria, sub-phase breakdown
│       │   Status:  Current (v1.0)
│       │
│       └── x-developer-terms-compliance-review.md ← COMPLIANCE REVIEW
│           Purpose: X Developer Terms concerns log
│           Contains: 7 issues (4 critical, 3 medium)
│           Status:  Living document
│
├── config/
│   ├── accounts.json                       ← CREDENTIALS (git-ignored)
│   ├── accounts.example.json               ← CREDENTIAL TEMPLATE (safe to share)
│   ├── competitors.json                    ← COMPETITOR DATA (machine-readable)
│   │   Contains: 41 accounts with handle, category, market, priority
│   │   user_id resolved by Scout on first run
│   └── global_rules.md                     ← BEHAVIORAL RULES
│
├── agents/                                 ← AGENT SKILL FILES
│   ├── marc.md                            ← COO / Orchestrator hub (Phase 4)
│   ├── marc_pipeline.md                   ← Pipeline Steps 1-13 (Phase 5: Step 2 Claude subagent)
│   ├── marc_publishing.md                 ← Publishing Steps P1-P8 (Phase 5: Steps P4, P8 Claude subagents)
│   ├── marc_schemas.md                    ← Schemas & report formats (loaded on demand)
│   ├── scout.md                           ← Competitor Research (Phase 5: Daily Intelligence Mode)
│   ├── strategist.md                      ← Growth Strategy
│   ├── creator.md                         ← Content Planning & Image Prompts (Phase 2)
│   ├── publisher.md                       ← X API Posting & Outbound Engagement (Phase 5: Smart Outbound Mode)
│   └── analyst.md                         ← Metrics Collection & Data Storage (Phase 5: Intelligence Mode)
│
├── scripts/                                ← PIPELINE & UTILITY SCRIPTS
│   ├── run_pipeline.sh                    ← Pipeline entry point (thin wrapper → Marc)
│   ├── run_task.sh                        ← Operator task entry point (reads task file → Marc)
│   ├── validate.py                        ← Deterministic validation (Phase 5: analyst_report, scout_analysis, outbound_plan)
│   ├── x_api.py                           ← X API v2 wrapper library (read + write + batch)
│   ├── db_manager.py                      ← SQLite database layer (WAL mode, insert/query)
│   ├── scout.py                           ← Scout agent script (Phase 5: --raw/--compact + pre-analysis)
│   ├── publisher.py                       ← Publisher agent script (Phase 5: smart-outbound subcommand)
│   ├── publisher_outbound_data.py         ← Outbound data fetcher for Claude analysis (Phase 5)
│   ├── analyst.py                         ← Analyst agent script (collect + summary + import) (Phase 4)
│   ├── telegram_send.py                   ← Telegram send helper (Phase 2)
│   ├── telegram_bot.py                    ← Telegram bot daemon (commands + /metrics + screenshot) (Phase 4)
│   ├── run_phase5_tests.sh               ← Phase 5 E2E test runner — Phase A+B (dry-run + API)
│   ├── run_phase5_tests_c.sh             ← Phase 5 E2E test runner — Phase C (Claude subagents)
│   └── run_phase5_tests_d.sh             ← Phase 5 E2E test runner — Phase D (full E2E + live posting)
├── data/.gitkeep                           ← PIPELINE STATE (empty, git-tracked)
├── logs/.gitkeep                           ← AGENT LOGS (empty, git-tracked)
├── backups/.gitkeep                        ← DAILY BACKUPS (empty, git-tracked)
└── media/
    ├── pending/.gitkeep                    ← IMAGES AWAITING APPROVAL
    └── posted/.gitkeep                     ← PUBLISHED IMAGES
```

**GitHub**: `https://github.com/Shimpeioto/X-agents` (private)

### Reading Order for Third Parties

1. **Start here** → `context.md` — understand the vision, decisions, and current state
2. **Understand the product** → `specs/x-ai-beauty-prd-v1.md` — what's being built and why
3. **Understand the implementation** → `specs/x-ai-beauty-spec-v2.3.md` — how it's built
4. **Check compliance** → `specs/x-developer-terms-compliance-review.md` — known policy concerns and resolution schedule
5. **Background research** → `autonomous-agent-system-analysis.md` — how the architecture was chosen
6. **Execute Phase 0** → `phase-0-runbook.md` — set up local development environment

### Document Relationships

```
context.md (this file)
    │
    │  "The big picture & all decisions"
    │
    ├──▶ autonomous-agent-system-analysis.md
    │       │
    │       │  "8 architectural principles"
    │       │  "Claude Code vs OpenClaw"
    │       │
    │       └──▶ Findings feed into ──▶ spec + PRD
    │
    ├──▶ specs/x-ai-beauty-prd-v1.md
    │       │
    │       │  "What to build & why"
    │       │  "Success = 10K followers"
    │       │
    │       └──▶ References ──▶ spec for "how"
    │
    ├──▶ specs/x-ai-beauty-spec-v2.3.md
    │       │
    │       │  "How to build it"
    │       │  "Agents, APIs, cron, deployment"
    │       │
    │       ├──▶ References ──▶ PRD for "why"
    │       ├──▶ Constrained by ──▶ compliance review
    │       └──▶ Parent of ──▶ phase-1-spec.md + phase-1-prd.md
    │
    ├──▶ specs/phase-1-spec.md + specs/phase-1-prd.md
    │       │
    │       │  "Phase 1: Scout + Strategist + Marc foundation"
    │       │  "Marc-as-Claude architecture, validate.py, run_pipeline.sh"
    │       │
    │       └──▶ Child of ──▶ parent spec + parent PRD
    │
    ├──▶ specs/x-developer-terms-compliance-review.md
    │       │
    │       │  "7 policy concerns"
    │       │  "Review schedule by phase"
    │       │
    │       └──▶ May require changes to ──▶ spec (Phases 2-4)
    │
    ├──▶ phase-0-runbook.md
    │       │
    │       │  "Local dev setup (9 steps)"
    │       │  "First step of implementation"
    │       │
    │       └──▶ Implements ──▶ Phase 0 of spec
    │
    ├──▶ procedures/add-competitor.md
    │       │
    │       │  "Add/remove competitor accounts"
    │       │  "Keeps competitor-accounts.md + competitors.json in sync"
    │       │
    │       └──▶ Operates on ──▶ competitor-accounts.md + competitors.json
    │
    ├──▶ harness.md
    │       │
    │       │  "Three-layer architecture (Shell → Marc → Specialists)"
    │       │  "OS analogy, key patterns, file layout"
    │       │
    │       └──▶ Referenced by ──▶ guides/agent-building-guidelines.md
    │
    └──▶ guides/agent-building-guidelines.md
            │
            │  "How to build new agents"
            │  "Principles, templates, checklist"
            │
            └──▶ References ──▶ all agent files + harness.md
```

---

## 8. Deliverables Summary

| File | Type | Description |
|---|---|---|
| `autonomous-agent-system-analysis.md` | Framework | OpenClaw vs Claude Code comparison; 8 architectural principles; capability gap analysis |
| `specs/x-ai-beauty-spec-v2.3.md` | Demo Spec | Technical Specification — agents, API strategy, pipeline, config schemas, cron, auth, memory, agent design principles, testing, deployment |
| `specs/x-ai-beauty-prd-v1.md` | Demo PRD | Product Requirements — goals, user stories, features, agent design philosophy, launch criteria, open questions |
| `phase-0-runbook.md` | Runbook | Step-by-step Phase 0 local development setup with verification scripts |
| `specs/x-developer-terms-compliance-review.md` | Compliance | X Developer Terms concerns log — 7 issues to resolve during implementation |
| `.gitignore` | Config | Git ignore rules — excludes secrets, databases, logs, media, OS files |
| `config/accounts.example.json` | Template | Credential template with placeholder values for safe sharing |
| `competitor-accounts.md` | Reference | Human-readable competitor list — 26 EN + 17 JP accounts (41 unique, 2 overlap) |
| `config/competitors.json` | Data | Machine-readable competitor list — 41 entries with handle, category, market, priority |
| `procedures/add-competitor.md` | Procedure | Step-by-step guide for adding/removing competitor accounts — JSON template, validation commands, example walkthrough |
| `specs/phase-1-spec.md` | Demo Spec | Phase 1 Technical Specification — Scout, Strategist, Marc foundation, validation rules, output schemas, testing strategy, edge cases |
| `specs/phase-1-prd.md` | Demo PRD | Phase 1 Product Requirements — goals, success criteria, user stories, exit criteria, risks, timeline, feature mapping |
| `harness.md` | Architecture | Three-layer architecture model (Shell → Marc → Specialists), OS analogy, key patterns, file layout |
| `guides/agent-building-guidelines.md` | Guide | How to build new agents — principles, templates, I/O contracts, validation, checklist |
| `context.md` | Meta | This document — full project context for third-party understanding |
| `scripts/run_phase5_tests*.sh` (×3) | Testing | Phase 5 E2E test runners — Phase A+B (dry-run + API), Phase C (Claude subagents), Phase D (full E2E + live posting) |

---

## 9. Implementation Status

### Development Approach

All development happens on your own machine. A VPS is only needed when the system is ready to run autonomously. Phases 0-5 are local CLI development. Phase 6 is VPS deployment. Phase 7 is autonomous operation.

**Latest**: Phase 5 complete (March 5, 2026). 20/20 E2E tests passed (spec §8). 8 live tweets posted (Day 2).

Phase 5 files added/modified (10 files):
- `agents/analyst.md` — Added "Intelligence Mode" section (anomaly detection, category breakdown, A/B test evaluation, trend comparison, report composition)
- `agents/scout.md` — Added "Daily Intelligence Mode" section + updated CLI usage with `--raw`/`--compact` flags
- `agents/publisher.md` — Added "Smart Outbound Mode" section (relevance check, tweet selection, contextual reply crafting, outbound plan)
- `agents/marc_pipeline.md` — Step 2 replaced with Claude Scout subagent invocation + fallback
- `agents/marc_publishing.md` — Step P4 replaced with smart outbound flow (P4a-P4c), Step P8 replaced with analyst intelligence flow (P8a-P8c)
- `scripts/scout.py` — Added `--raw`/`--compact` flags, `compute_pre_analysis()`, `compact_report()` functions
- `scripts/publisher.py` — Added `smart-outbound` subcommand and `run_smart_outbound()` function
- `scripts/publisher_outbound_data.py` — **New** OutboundDataFetcher (~120 lines): fetch target account data for Claude analysis
- `scripts/validate.py` — Added 3 new validation functions: `validate_analyst_report` (8 checks), `validate_scout_analysis` (6 checks), `validate_outbound_plan` (7 checks)
- `docs/context.md` — Updated architecture sections (principle #9, agent tree, hybrid pattern subsection, cost estimate)

Phase 4 files added/modified (8 files):
- `scripts/db_manager.py` — Extended with WAL mode, `_connect()` helper, `timestamp` column migration, 4 insert functions, 5 query functions
- `scripts/x_api.py` — Added `get_tweets_batch()` method to XApiClient (batch tweet lookup, chunks at 100)
- `scripts/analyst.py` — **New** Analyst agent script (~300 lines): `Analyst` class with `collect_post_metrics`, `collect_account_metrics`, `generate_summary`, `import_manual_metrics` (CSV+JSON), CLI with `collect`/`summary`/`import` subcommands + `--dry-run`
- `scripts/validate.py` — Extended with `analyst` mode (8 checks on summary JSON) and `analyst_metrics` mode (6 checks on SQLite integrity)
- `scripts/telegram_bot.py` — Added `/metrics` (view + input modes), screenshot handling via Claude Vision API, `/confirm`, `/cancel`, photo message handler
- `scripts/publisher.py` — Added SQLite dual-write for outbound log (best-effort, JSON remains primary)
- `agents/analyst.md` — Full skill file replacing placeholder (role, data collection, CLI, output schema, error handling, schedule)
- `agents/marc.md` — Updated to Phase 4: War Room Lite → Full War Room (6-criterion rubric, 0-100 scoring), added Steps P6-P8 (Analyst collect, summary+validate, follower anomaly detection, daily report), updated pipeline state task IDs

Phase 4 testing — all passed:

| Test | Description | Result |
|---|---|---|
| 1 | db_manager insert/query (post_metrics + account_metrics + daily_summary) | **PASS** — insert, replace, and query all work |
| 2 | Analyst dry-run collect | **PASS** — found 4 EN + 4 JP posted tweets, logged correctly |
| 3 | analyst_metrics validation (6 checks on SQLite) | **PASS** — all tables, columns, migration verified |
| 4 | Analyst live collect (real API) | **PASS** — 8 tweets fetched, 2 account snapshots (EN: 7 followers, JP: 140 followers) |
| 5 | Analyst summary generation (EN + JP) | **PASS** — both JSON summaries written |
| 6 | Analyst summary validation (8 checks) | **PASS** — EN 8/8, JP 8/8 |
| 7 | Publisher dry-run outbound with dual-write | **PASS** — 25 outbound rows in SQLite alongside JSON |
| 8 | CSV manual metrics import | **PASS** — 2 rows imported |
| 9 | JSON manual metrics import | **PASS** — 2 entries imported |
| 10 | Follower anomaly detection simulation | **PASS** — correctly detects -15% as anomaly |
| 11 | E2E P6-P8: Collect → Summary → Validate → Anomaly → Daily Report → Telegram | **PASS** — full flow, daily report sent to Telegram |

Phase 4 E2E Day 1 results:
- EN: 4 posts measured (1-1-0-1 likes), 7 followers (first day)
- JP: 4 posts measured (2-2-2-0 likes), 140 followers (first day)
- Outbound: EN 15 likes, 5 replies, 5 follows (from Phase 3 test); JP not yet run
- Daily report delivered to Telegram successfully

Remaining Phase 4 E2E tests (require consecutive calendar days):
- E2E Day 2: Verify `followers_change` calculated, anomaly detection with real delta
- E2E Day 3: 3 consecutive days in SQLite, historical queries work

Phase 5 E2E testing — 20/20 passed:

| Test | Phase | Description | Result |
|---|---|---|---|
| 1 | C | Analyst Intelligence — reads metrics + content plans, produces daily report | **PASS** |
| 2 | C | Analyst Intelligence — anomaly detection flags >10% follower change | **PASS** |
| 3 | C | Analyst Intelligence — category breakdown matches content plan categories | **PASS** |
| 4 | C | Analyst Intelligence — A/B test evaluation with variant comparison | **PASS** |
| 5 | C | Analyst Intelligence — `validate.py analyst_report` accepts output (8 checks) | **PASS** |
| 6 | C | Scout Intelligence — reads compact data, produces enriched analysis | **PASS** |
| 7 | C | Scout Intelligence — `validate.py scout_analysis` accepts output (6 checks) | **PASS** |
| 8 | A | Scout `--raw --compact` — produces compact file (~15KB) with `_pre_analysis` | **PASS** |
| 9 | C | Pipeline cross-check — scout analysis + strategy consistency verified | **PASS** |
| 10 | C | Publisher Smart Outbound — reads target data, generates contextual plan | **PASS** |
| 11 | C | Publisher Smart Outbound — `validate.py outbound_plan` accepts output (7 checks) | **PASS** |
| 12 | B | `publisher_outbound_data.py` — fetches real target data via API | **PASS** |
| 13 | C | Smart Outbound — reply text does not start with `@`, language matches account | **PASS** |
| 14 | C | Smart Outbound — skip decision with reasoning for irrelevant targets | **PASS** |
| 15 | A | Publisher rate limits — enforced correctly across post + outbound actions | **PASS** |
| 16 | A | Legacy outbound fallback — works when Claude subagent unavailable | **PASS** |
| 17 | C | Full pipeline with Claude Scout + Analyst intelligence modes | **PASS** |
| 18 | D | Full E2E pipeline — Scout → Strategist → Creator → War Room → approval | **PASS** |
| 19 | D | Live posting — 8 tweets (4 EN + 4 JP) posted via Publisher | **PASS** |
| 20 | D | Fallback resilience — pipeline completes when Claude subagent fails | **PASS** |

Phase 3 files added/modified (6 files):
- `scripts/x_api.py` — Extended with `XApiWriteClient` class (OAuth 1.0a, create_post, upload_media, like_tweet, reply_to_tweet, follow_user)
- `scripts/publisher.py` — New Publisher script (post + outbound subcommands, --dry-run, --slot filtering, rate limit tracking, media upload)
- `scripts/validate.py` — Extended with `publisher` mode (8 checks) and `publisher_rate_limits` mode (5 checks)
- `agents/publisher.md` — Full skill file replacing placeholder (role, CLI, post/outbound flows, rate limits, compliance)
- `agents/marc.md` — Updated to Phase 3 (added Publishing Sequence steps P1-P5, PUBLISHER logging agent, expanded task IDs)
- `scripts/telegram_bot.py` — Added `/publish` command, fixed status emoji mapping (`"posted"` not `"published"`)

Phase 3 dry-run testing — all passed:

| Test | Description | Result |
|---|---|---|
| 1 | Dry-run post EN (4 approved posts) | **PASS** — 4 posted, 0 failed |
| 2 | Dry-run post JP (4 approved posts) | **PASS** — 4 posted, 0 failed |
| 3 | Rate limits validation (5 checks) | **PASS** — all counters within limits |
| 4 | Dry-run outbound EN (5 targets) | **PASS** — 15 likes, 5 replies, 5 follows logged |
| 5 | Rate limits after outbound (5 checks) | **PASS** — no overages |
| 6 | Outbound log validation | **PASS** — 25 actions logged correctly |

Phase 3 real API tests — all passed (March 4, 2026):

| Test | Description | Result |
|---|---|---|
| 7 | Auth test — XApiWriteClient for EN + JP | **PASS** — EN user_id: 2024417575887917057, JP user_id: 1147717472 |
| 8 | Single slot post — real tweet on EN | **PASS** — https://x.com/iammeruru/status/2029059847917093267 |
| 9 | Publisher validation after real post | **PASS** — 8/8 checks |
| 10 | JP publish — 4 real tweets | **PASS** — 4 posted, 0 failed |
| 11 | Full validation (EN + JP + rate limits) | **PASS** — EN 8/8, JP 8/8, rate limits 5/5 |

Note: Initial Test 8 attempt failed with 403 (app permissions were Read-only). Fixed by updating X Developer Console to "Read and Write" + "Web App, Automated App or Bot" and regenerating access tokens.

Phase 2 files added/modified (5 files):
- `agents/creator.md` — Creator skill file (content planning, image prompts, reply templates, output schema)
- `agents/marc.md` — Updated to Phase 2 (13-step pipeline: Scout → Strategist → Creator EN/JP → War Room Lite → Telegram)
- `scripts/validate.py` — Extended with `creator` mode (12 checks) and `creator_cross` mode (3 checks)
- `scripts/telegram_send.py` — Telegram send helper (auto-splits >4096 chars, --file mode)
- `scripts/telegram_bot.py` — Telegram bot daemon (/approve, /status, /details, /pause, /resume, /help)

Phase 2 testing — all tests passed:

| Test | Description | Result |
|---|---|---|
| 1 | Telegram send helper | **PASS** — message delivered to chat |
| 2 | Telegram bot startup | **PASS** — daemon runs, accepts commands |
| 3 | Full pipeline (Scout + Strategist + Creator EN/JP) | **PASS** — completed in 7m, all 13 tasks succeeded |
| 4 | Creator EN validation (12 checks) | **PASS** — 4 posts, 8 reply templates |
| 5 | Creator JP validation (12 checks) | **PASS** — 4 posts, 8 reply templates |
| 6 | Creator EN cross-validation (3 checks) | **PASS** — categories, hashtags, post count match strategy |
| 7 | Creator JP cross-validation (3 checks) | **PASS** |
| 8 | War Room Lite | **PASS** — no semantic issues across all outputs |
| 9 | Telegram preview delivery | **PASS** — content preview arrived in Telegram |
| 10 | Bot /details command | **PASS** — all posts shown with draft status |
| 11 | Bot /approve EN | **PASS** — EN posts updated to approved |
| 12 | Bot /approve JP 1,2 | **PASS** — specific JP slots approved |
| 13 | Bot /status | **PASS** — pipeline summary with task counts |
| 14 | Bot /pause + /resume | **PASS** — pause flag created/removed |
| 15 | Bot /help | **PASS** — command list displayed |

All 7 Phase 1 files implemented:
- `scripts/x_api.py` — X API v2 wrapper (tweepy-based, retry logic, rate limit handling)
- `scripts/scout.py` — Scout agent script (41 competitors, 8 keyword searches, user_id caching)
- `scripts/validate.py` — Deterministic validation (scout, strategist, cross modes)
- `scripts/run_pipeline.sh` — Shell wrapper (lock file, date handling, Marc invocation)
- `agents/marc.md` — Marc orchestration skill file (7-step pipeline, error recovery, logging)
- `agents/scout.md` — Scout skill file (data collection scope, error handling, CLI usage)
- `agents/strategist.md` — Strategist skill file (analysis steps, output schema, validation rules)

Phase 1 manual testing — all 12 tests passed:

| Test | Description | Result |
|---|---|---|
| 1 | X API wrapper — resolve 1 handle | **PASS** — returned user_id, username, name, description, public_metrics |
| 2 | X API wrapper — fetch 1 timeline | **PASS** — 5 tweets with full metrics including impression_count |
| 3 | Scout --max-competitors 1 | **PASS** — resolved 41 user_ids, fetched 1 competitor, 59 new accounts discovered |
| 4 | Scout --max-competitors 5 | **PASS** — 5 competitors fetched, user_ids cached (0 new resolves) |
| 5 | Scout --dry-run | **PASS** — mock data generated instantly, no API calls |
| 6 | Full Scout (all 41 competitors) | **PASS** — 41 fetched, 0 skipped, 55 new accounts, ~18 seconds |
| 7 | Verify user_ids cached | **PASS** — all user_ids resolved and saved to competitors.json |
| 8 | Validate Scout report | **PASS** — all 8 validation checks passed |
| 9 | Validate Strategist (missing file) | **PASS** — correctly rejected with "file_not_found" |
| 10 | Full Marc pipeline (run_pipeline.sh) | **PASS** — completed in 3m17s, all steps executed |
| 11 | Verify pipeline outputs | **PASS** — strategy validates (14/14), strategy_current matches, pipeline log exists. Cross-validation: 5 warnings (justified — gap-fill hashtags + discovered account) |
| 12 | Lock file cleanup | **PASS** — lock file removed after pipeline completion |

Pipeline fix applied: `run_pipeline.sh` updated to unset `CLAUDECODE` env var (prevents nested session error) and include non-interactive override in Marc prompt (ensures Marc runs commands directly instead of asking for user input).

| Phase | Description | Where | Status |
|---|---|---|---|
| Phase 0 | Local Development Setup (CLI, APIs, Telegram, project structure) | Local machine | **✅ Complete** — 30/30 health check, pushed to GitHub |
| Phase 1 | Scout + Strategist + Marc Foundation | Local machine | **✅ Complete** — 7 files implemented, all 12 tests passed, pipeline runs end-to-end |
| Phase 2 | Creator + Telegram Command Processing | Local machine | **✅ Complete** — 5 files added/modified, all 15 tests passed, pipeline runs end-to-end with Telegram integration |
| Phase 3 | Publisher + X API Posting | Local machine | **✅ Complete** — 6 dry-run tests + 5 real API tests passed, 8 tweets posted live (4 EN + 4 JP) |
| Phase 4 | Analyst + Manual Metrics + War Room Upgrade | Local machine | **✅ Complete** — 11 tests passed, E2E Day 1 verified, daily report sent to Telegram. Days 2-3 E2E pending (consecutive calendar days). |
| Phase 5 | Claude Hybrid Agent Conversion (Analyst, Scout, Publisher intelligence) | Local machine | **✅ Complete** — 10 files modified/created, all 3 sub-phases implemented. 20/20 E2E tests passed. |
| Phase 6 | VPS Deployment (provision, copy project, install cron) | VPS | Not started |
| Phase 7 | Autonomous Operation (cron runs agents overnight) | VPS | Not started |

---

## 10. Key Technical Decisions Explained

### Why Claude Code + cron instead of OpenClaw?

OpenClaw is a daemon-based framework with native messaging and always-listening capabilities. Claude Code is a session-based CLI tool. Despite this, Claude Code was chosen because: (a) it handles ~80% of requirements natively, (b) cron fills the scheduling gap reliably, (c) a 50-line Telegram bot fills the messaging gap, (d) staying within Anthropic's ecosystem avoids the security risks of OpenClaw's broad permissions and community skill vulnerabilities, (e) it avoids learning a second framework. The key insight was that the project needs a batch pipeline (run overnight, review in morning), not a real-time conversational daemon.

### Why a COO agent (Marc) instead of a simple orchestrator script?

A shell script can handle sequencing (run A, then B, then C) and basic error handling (retry on failure). But it cannot make judgment calls: "Creator produced 3 posts but Strategist said 4 — should I ask Creator to regenerate or adjust the strategy?" "Follower count dropped 15% — is this a data error, a shadowban, or normal variance?" These require the reasoning capability of an LLM. Marc is the layer where orchestration meets judgment.

### Why X API + Playwright hybrid for the demo?

Pure X API (Basic, $200/month) cannot provide impression counts — that requires Pro at $5,000/month. Pure Playwright risks account bans. The hybrid uses official API for everything except impression scraping from own post pages — minimal risk, full functionality, $200/month. **Note**: Compliance review (Session 10) found that Playwright scraping — even on own pages — may violate X's ban on non-API automation of the website. This will be re-evaluated at Phase 4; Playwright may be removed entirely.

### Why CLAUDE.md instead of a database for agent memory?

CLAUDE.md files are automatically loaded by Claude Code at session start with zero custom code. For behavioral instructions ("never use more than 3 hashtags"), this is ideal. Structured data (metrics, rate limits, credentials) stays in JSON/SQLite because Python scripts need machine-parseable formats. This split — CLAUDE.md for behavior, JSON/SQLite for data — is a reusable pattern for any project using this framework.

### Why 6 agents for the demo instead of fewer or more?

Each agent maps to a distinct skill domain. Combining any two would bloat context windows. Splitting further would add coordination overhead without benefit. The COO-over-specialists pattern matches the original article's architecture and scales well — adding a new capability means adding one agent, not restructuring the whole system.

---

## 11. Glossary

| Term | Definition |
|---|---|
| **Autonomous Agent Framework** | The general-purpose architecture for multi-agent systems being developed — the main project |
| **X Beauty Demo** | The first demonstration project validating the framework: growing an AI beauty X account |
| **Marc (COO)** | The orchestrator agent that coordinates all other agents, makes judgment calls, and communicates with the human via Telegram |
| **Scout** | Demo agent: scrapes competitor data and identifies trends using X API |
| **Strategist** | Demo agent: formulates growth strategy based on Scout and Analyst data |
| **Creator** | Demo agent: drafts post content and image prompts |
| **Publisher** | Demo agent: executes posting and outbound engagement via X API |
| **Analyst** | Demo agent: collects post metrics via X API batch lookup, account snapshots, stores in SQLite, generates JSON summaries. Manual impression input via Telegram /metrics, screenshot parsing (Claude Vision), or CSV/JSON import. |
| **War Room** | Marc's daily review session where all agent outputs are cross-checked for consistency |
| **Pipeline** | The agent execution sequence — during development, triggered manually via CLI; in production, triggered by cron overnight |
| **CLAUDE.md** | Claude Code's native memory system — markdown files auto-loaded at session start |
| **Orchestrator Script** | Shell script that cron triggers; launches Marc who then invokes agents in sequence |
| **Shared State** | The filesystem layer (JSON + SQLite) through which agents exchange data between sessions |
| **OpenClaw** | Open-source agent framework evaluated and rejected in favor of Claude Code + cron |
| **Compliance Review** | Living document tracking 7 X Developer Terms issues to resolve during implementation |
| **Amarry Technologies** | Shimpei's company — the broader corporate context |
| **UniModel** | Amarry's primary product — an AI model marketplace (separate from this project) |
