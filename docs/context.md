# Project Context Document
# Autonomous AI Agent System

**Purpose of this document**: Enable any third party to fully understand the project vision, decision history, current state, and deliverables without needing to read the full conversation transcript.

**Last updated**: June 8, 2026 (Session 51: daily automation actually halted. Session 50's `launchctl unload` was not persistent — macOS auto-loaded every `.plist` in `~/Library/LaunchAgents/` at the next login, so all 5 daily jobs had been firing every day since Session 50. Today's `create` ran 06:02→08:15 and pushed a Telegram message + HTML doc, which is what the operator noticed. Fix: moved the 5 daily plists into `~/Library/LaunchAgents/xagents-disabled/` and `launchctl bootout`'d each. Structurally impossible to auto-reload now. Verified: `launchctl list` shows only the 3 expired `publish-slot.20260322-en-*` (harmless).)

**Previous**: May 20, 2026 (Session 50: daily automation thought to be halted — `launchctl unload` run on all 5 daily LaunchAgents. In fact only effective until next login; see Session 51 for actual halt.)

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
| Multi-agent coordination | 7 agents with dependency chains (Scout → Strategist → Creator) |
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

**Design delivered**: 6-agent system (Scout, Strategist, Creator, Publisher, Analyst, Commander) applying all 8 architectural principles from the framework research. Later expanded to 7 agents (Session 30: Outbound extracted from Publisher). Included pipeline schedule, shared state architecture, and 5-phase implementation plan.

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
- `data/misc/scout_report_enriched_test.json` — Fixture for Claude intelligence tests
- `data/misc/scout_report_fallback_test.json` — Fixture for fallback resilience tests
- `data/misc/strategy_fallback_test.json` — Fixture for fallback testing
- `data/misc/strategy_test_enriched.json` — Fixture for enriched strategy testing

**Live Posts**: 4 EN + 4 JP tweets posted successfully (Day 2, March 5, 2026)

**Result**: **20/20 PASS** — All tests passed. Phase 5 complete.

### Session 24 — Agent Teams Migration: Conversational Marc + Teammate Architecture (March 5, 2026)

**Goal**: Migrate from pipeline-driven subagent architecture (`claude -p` isolated subagents) to Claude Code Agent Teams with a two-layer conversational architecture.

**Architecture Change**:
- **Before**: Shell scripts → `claude -p` Marc → nested `claude -p` subagents (isolated, no coordination)
- **After**: Telegram → Conversational Marc (`claude -p`, lightweight) → Execution Layer (Agent Teams: Marc as Team Leader, teammates with shared task list + messaging)

**Two-Layer Design**:
- **Conversational Layer**: Marc receives Telegram messages via `claude -p`, reasons about them, asks clarifying questions, decides when to execute. Uses `START_TASK:` JSON marker to signal task execution.
- **Execution Layer**: Claude Code Agent Teams — Marc spawns teammates (Scout, Strategist, Creator, Publisher, Analyst) with shared task coordination via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`.

**Files created** (1): `agents/marc_conversation.md`
**Files rewritten** (3): `agents/marc.md`, `agents/marc_pipeline.md`, `agents/marc_publishing.md`
**Files edited** (9): `agents/scout.md`, `agents/strategist.md`, `agents/creator.md`, `agents/publisher.md`, `agents/analyst.md`, `CLAUDE.md`, `scripts/run_task.sh`, `scripts/run_pipeline.sh`, `scripts/telegram_bot.py`

**Key changes**:
- `agents/marc.md`: Rewritten as Team Leader (spawns teammates via Agent tool instead of nested `claude -p`)
- `agents/marc_conversation.md`: New system prompt for conversational Marc (identity, team reference, decision rules, START_TASK tool)
- `agents/marc_pipeline.md`: Transformed from 13 rigid steps to goal-oriented playbook with parallel teammate spawning
- `agents/marc_publishing.md`: Transformed from P1-P8 steps to goal-oriented playbook with teammate spawning
- All 5 agent skill files: Added "Teammate Mode" section for autonomous operation when spawned as teammates
- `scripts/telegram_bot.py`: Major rewrite (~645→~910 lines) — added conversational layer via `claude -p`, `_execute_task()` spawner, default text handler, `/pipeline` command, `/running` command
- `scripts/run_task.sh` + `run_pipeline.sh`: Added `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` env var, updated prompts for Team Leader role
- `CLAUDE.md`: Added Architecture section describing two-layer design

**Issues encountered & resolved**:
1. Anthropic API key not available → switched conversational layer from Anthropic API to `claude -p` (uses Max subscription)
2. `--no-input` flag doesn't exist in claude CLI → removed invalid flag

**Result**: Marc responds conversationally via Telegram, spawns Agent Teams for execution.

---

### Session 25 — Production Testing: First Real Task Execution + Pipeline Run (March 6-7, 2026)

**Goal**: Test the agent system end-to-end with real tasks via Telegram — verify Marc can receive tasks, reason about them, spawn teammates, and deliver results autonomously.

**Tasks Executed** (5 total, via Telegram → Marc):

| Task | Type | Duration | Result |
|---|---|---|---|
| 001 | Ad-hoc (competitor strategy) | 47s | Failed — no output (silent completion) |
| 002 | Ad-hoc (retry of 001) | 73s | Failed — same issue |
| 003 | Ad-hoc (retry after fix) | 10m | **Success** — 456KB scout report + 86KB HTML strategy report |
| 004 | Ad-hoc (competitor image analysis) | 2.5m | **Success** — 60KB image analysis JSON with real media URLs |
| 005 | Daily pipeline | 10m | **Success** — Full pipeline completed, all validations passed, War Room 100/100 |

**Critical Bug Found & Fixed — Non-Interactive Execution**:
- **Symptom**: Tasks 001-002 completed with exit_code 0 but produced no output files (47s/73s — too fast)
- **Root cause**: Two issues combined:
  1. `telegram_bot.py`'s `_execute_task()` was missing the non-interactive instruction that `run_task.sh` already had
  2. `CLAUDE.md`'s "Don't try to run scripts with bash tool" preference was not scoped — applied in non-interactive mode where the operator isn't watching
- **Fix 1**: Added `IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly...` to `_execute_task()` prompt in `telegram_bot.py`
- **Fix 2**: Scoped CLAUDE.md preferences to differentiate interactive vs non-interactive sessions

**Image/Media Data Collection Added**:
- **Problem**: Scout collected `profile_image_url` via API but discarded it; tweet media (photos/videos) not collected at all
- **Fix**: Added `MEDIA_FIELDS` and `expansions=["attachments.media_keys"]` to `x_api.py`'s `get_user_timeline()`, added `profile_image_url` to `scout.py`'s competitor output
- **Cost**: Zero additional API calls — expansions are free data in the same response
- **Verified**: Task 004 produced image analysis with real `pbs.twimg.com` URLs for all image posts

**Pipeline Issue — Creator `status: "approved"` instead of `"draft"`**:
- **Symptom**: Task 005 content plans had all posts as `status: "approved"`, bypassing the human approval gate
- **Root cause**: Creator agent didn't follow its own validation rule #6. Marc didn't catch it because he validated by reasoning instead of running `validate.py`
- **Fix**: Added explicit `status: "draft"` reminder in `creator.md` (Step 2) and in `marc_pipeline.md` Creator spawn prompts

**Agent Philosophy Established**:
- Marc operates like a **human agent with SOP**: daily/repetitive tasks follow the SOP (pipeline playbook) faithfully including running validation scripts; ad-hoc tasks require free reasoning where Marc decides his own approach
- Marc decides which mode applies — "Is this a daily pipeline → follow SOP" vs "Is this ad-hoc → think freely"
- Scripts like `validate.py` are **tools Marc uses**, not robotic steps — they serve Marc's reasoning, not replace it

**Files modified** (5):
- `scripts/telegram_bot.py` — Added non-interactive override to `_execute_task()`
- `CLAUDE.md` — Scoped preferences for interactive vs non-interactive sessions
- `scripts/x_api.py` — Added `MEDIA_FIELDS`, media expansions to `get_user_timeline()`, media lookup from response includes
- `scripts/scout.py` — Added `profile_image_url` to `fetch_competitor()` return dict
- `agents/creator.md` — Added bold `status: "draft"` reminder at Step 2
- `agents/marc_pipeline.md` — Added `status: "draft"` instruction to Creator spawn prompts

**Key outputs produced** (verified end-to-end, later cleaned up in Session 27):
- `data/scout/scout_report_20260306.json` (538KB) — 41 competitors with media data
- `data/reports/strategy_report_20260306.html` (86KB) — Professional HTML report with competitor analysis + EN/JP strategies
- `data/misc/image_analysis_report_20260306.json` (60KB) — Image post analysis with real URLs, category performance, engagement comparison
- `data/strategy/strategy_20260306.json` (7.6KB) — Daily strategy with data-driven insights
- `data/content/content_plan_20260306_EN.json` + `_JP.json` — 4 posts each with image prompts, A/B test variants, reply templates
- `data/pipeline/pipeline_state_20260306.json` — Full pipeline state, all tasks completed

### Session 26 — HTML Report Generation for Telegram Review (March 7, 2026)

**Goal**: Generate HTML versions of all reports Marc sends to Telegram, so the operator can review them in a mobile browser instead of reading truncated JSON in chat.

**Problem**: Telegram's 4096 character limit truncates inline previews. JSON files are hard to read on mobile. The strategy report HTML from task 003 (86KB, dark theme) proved HTML works well for review.

**Solution**: Created `scripts/generate_html_report.py` with 3 report types:

| Report Type | CLI Command | JSON Input | HTML Output |
|---|---|---|---|
| `content_preview` | `generate_html_report.py content_preview <EN> <JP> --strategy <path> [--pipeline-state <path>]` | Content plans + strategy + pipeline state | `data/reports/content_preview_{date}.html` |
| `daily_report` | `generate_html_report.py daily_report <report.json>` | Daily report JSON | `data/metrics/daily_report_{date}.html` |
| `publish_report` | `generate_html_report.py publish_report <EN> <JP> [--outbound-log <path>] [--rate-limits <path>]` | Content plans (posted) + outbound log + rate limits | `data/reports/publish_report_{date}.html` |

**Design**: Reuses CSS design system from the Session 25 strategy report (dark theme, cards, stat boxes, tags, bar charts, responsive). Standard library only — no external dependencies.

**HTML reports are read-only visualization** — they consume existing JSON, never create or modify it. Agents continue to produce and consume JSON; HTML is purely for human review on mobile.

**Files created/modified** (3):
- `scripts/generate_html_report.py` — **New** HTML report generator (~550 lines, 3 report types)
- `agents/marc_pipeline.md` — Step 9 updated: generates `content_preview_{date}.html` and sends via `telegram_send.py --document`
- `agents/marc_publishing.md` — Steps 4 and 8 updated: generates `publish_report_{date}.html` and `daily_report_{date}.html`

**Verified**: Content preview (31KB) and daily report (22KB) generated from existing March 6 data and opened in browser.

### Session 27 — Remove Mar 6 Pipeline Test Output (March 7, 2026)

**Goal**: Clean up test output files from the Mar 6 pipeline run (Session 25, task 005) now that end-to-end verification is complete.

**Rationale**: The Mar 6 pipeline was a production test to verify the system works. With that confirmed, the test output is no longer needed and was cluttering the `data/` directory. Mar 3-5 data (earlier test runs) is retained.

**Files removed** (11):
- `data/content/content_plan_20260306_EN.json` — Test content plan (EN)
- `data/content/content_plan_20260306_JP.json` — Test content plan (JP)
- `data/reports/content_preview_20260306.html` — Session 26 HTML report derived from Mar 6 test data
- `data/misc/image_analysis_report_20260306.json` — Image analysis from test run
- `data/pipeline/pipeline_state_20260306.json` — Pipeline state from test run
- `data/scout/scout_compact_20260306.json` — Compact scout data
- `data/scout/scout_raw_20260306.json` — Raw scout data
- `data/scout/scout_report_20260306.json` — Enriched scout report
- `data/strategy/strategy_20260306.json` — Strategy from test run
- `data/reports/strategy_report_20260306.html` — Strategy HTML report from test run
- `data/strategy/strategy_current.json` — Copy of strategy_20260306.json (will regenerate on next real pipeline run)

**Note**: No posts were published to X from the Mar 6 pipeline — all posts stayed at `approved` status locally, so no X API cleanup was needed.

### Session 28 — URL Reading for Conversational Marc (March 7, 2026)

**Goal**: Enable Marc to read web page content when the operator shares URLs via Telegram.

**Problem**: When the operator shared a URL in Telegram, Marc only saw the raw URL text — he couldn't read the content behind it. This prevented the operator from sharing articles, references, or competitor pages for Marc to analyze.

**Solution**: Added automatic URL detection and content fetching in the Telegram bot's message handler. When a message contains URLs, the bot fetches each page's content and appends it to the message before sending to Marc.

**How it works**:
1. `handle_message` detects URLs in incoming text (regex, up to 3 URLs per message)
2. Fetches each URL via `scripts/fetch_url.py` (async via executor to avoid blocking)
3. Appends extracted text between `--- Content from <url> ---` markers
4. Marc receives the enriched message and can reason about the page content

**Files created/modified** (3):
- `scripts/fetch_url.py` — **New** URL fetcher using `requests` + stdlib `html.parser` (~100 lines). Extracts readable text from HTML, handles plain text/JSON directly. Truncates at 5000 chars. Also works as CLI.
- `scripts/telegram_bot.py` — Added `_extract_urls()`, `_fetch_url_content()`, `_enrich_message_with_urls()` helpers; modified `handle_message` to enrich messages with URL content before sending to Marc
- `agents/marc_conversation.md` — Added "URL Reading" section documenting the content markers and how to use fetched content

### Session 29 — Competitor Image Analysis Pipeline + Higgsfield Prompt Upgrade (March 8, 2026)

**Goal**: (1) Give Creator visual intelligence by analyzing top competitor images via Claude Vision. (2) Upgrade all content plan image prompts to full Higgsfield schema. (3) Show structured prompt fields in HTML preview with one-click copy.

**Problem**: Scout collects media URLs but Creator had zero insight into competitor visuals. Existing content plan prompts used old midjourney/stable_diffusion format (short generic text, no structured fields). HTML preview only showed flat prompt text — structured fields were invisible and required per-section copy-paste.

**Solution**:
1. New `image_analyzer.py` script — reads scout report, picks top 5 images by likes, calls Anthropic Vision API (Claude Sonnet), outputs Higgsfield-format references + visual patterns summary to `data/content/image_references_{YYYYMMDD}.json`. Creator uses these as (a) pattern awareness and (b) per-post style matching.
2. Rewrote all 4 content plan image prompts (EN_01, EN_02, JP_01, JP_02) to full Higgsfield schema: 150+ word prompts, standard negative prompts, all structured fields (meta, subject, outfit, pose, scene, camera, lighting, mood), locked character profiles.
3. Updated HTML report generator to render structured fields as syntax-highlighted JSON with "Copy JSON" button — one click copies the entire image_prompt object.

**Character profile compliance review**: Fixed 3 issues found during review:
- EN body_type was missing "curvaceous" from locked profile → added
- JP body_type used generic "full curves" instead of locked "large full chest, slim waist, wide full hips" → fixed
- EN_01 skin had unlocked "light warm tan" addition → removed

**Pipeline integration**: Image analysis added as Step 3.5 (optional — pipeline continues on failure).

**Files created/modified** (7):
- `scripts/image_analyzer.py` — **New** (~300 lines). Vision API analysis, `--top N`, `--dry-run`, rate limit retry, structured output.
- `agents/creator.md` — Added image references input step #5, "Using Image References" section (2 modes)
- `agents/marc_pipeline.md` — Added Step 3.5, updated dependency diagram and Creator spawn prompts
- `scripts/validate.py` — Added `image_references` validation mode (6 checks)
- `scripts/generate_html_report.py` — Structured Higgsfield fields rendered as syntax-highlighted JSON block with "Copy JSON" button
- `data/content/content_plan_20260308_EN.json` — Full Higgsfield rewrite (was midjourney)
- `data/content/content_plan_20260308_JP.json` — Full Higgsfield rewrite (was stable_diffusion)

**Verification**: Dry-run found 206 images, analyzed top 5 with mock data, validator passed 6/6 checks. Content plan validator passed 12/12 checks for both EN and JP. Character profile review passed all checks after fixes.

### Session 30 — Outbound Agent: Separate Engagement from Publishing (March 8, 2026)

**Goal**: Extract outbound engagement (likes, replies, follows) from Publisher into a dedicated Outbound agent with safety reasoning, cooldown enforcement, and history awareness.

**Problem**: Publisher owned both posting (mechanical script execution) and outbound planning (strategic reasoning about who to engage, what to say, when to hold back). These are fundamentally different jobs. Posting is deterministic; outbound requires safety reasoning, cooldown checks, and contextual reply crafting.

**Solution**: Created a new **Outbound agent** that owns the full outbound engagement lifecycle. Publisher stays lean for posting only. The Outbound agent adds safety layers that the old Publisher Smart Outbound Mode lacked:
1. **History awareness** — queries SQLite + JSON logs for past engagement before planning
2. **Cooldown enforcement** — 7-day follow, 3-day reply, 2-day like cooldowns per target
3. **Follow deduplication** — never re-follows already-followed accounts
4. **Tweet deduplication** — never re-likes already-liked tweets
5. **Volume budgets** — conservative safety margins below global API limits (EN: 20 likes, 5 replies, 3 follows; JP: 15 likes, 5 replies, 2 follows)
6. **Target rotation** — Strategist now rotates targets from the full 31+ competitor pool

**Architecture change**:
```
Before: Strategist → strategy.json → Publisher (plans + executes outbound)
After:  Strategist → strategy.json → Outbound agent (plans with safety reasoning) → publisher.py smart-outbound (executes)
```

**Files created** (3):
- `agents/outbound.md` — Full agent definition with 6-step workflow (read inputs → safety reasoning → fetch targets → analyze/plan → write plan → execute)
- `scripts/outbound_history.py` — History query tool; reads from SQLite + JSON logs; outputs human-readable summaries with per-target engagement counts, follow status, liked tweet IDs, and budget usage. Three CLI modes: `--days N`, `--target @handle`, `--check-tweets "id1,id2"`
- `config/outbound_rules.json` — Safety parameters (margins per account, cooldown periods, target rotation rules)

**Files modified** (7):
- `agents/publisher.md` — Removed Smart Outbound Mode section, added brief execution-only note pointing to Outbound agent
- `agents/strategist.md` — Added Target Rotation Rules subsection (draw from full pool, check recent logs, market matching, mix sizes, target count per account)
- `agents/marc_publishing.md` — Step 3 now spawns Outbound agent instead of Publisher; error recovery updated
- `agents/marc.md` — Updated team table, publishing flow, logging agents, dependencies
- `agents/marc_conversation.md` — Updated team table and task types to separate Publisher/Outbound
- `agents/creator.md` — Reply templates now reference Outbound agent
- `CLAUDE.md` — Added Outbound to agent definitions and tool assignments

**Verification**: Python syntax check passed. JSON validation passed. All 3 CLI modes of `outbound_history.py` tested against live data (EN: 54 actions across 5 targets found; JP: no history, fresh-run path verified; tweet dedup correctly identifies already-liked tweets). Cross-reference check found and fixed 2 additional stale references in `marc_conversation.md` and `creator.md`.

### Session 32 — First Production Outbound: OAuth Fix, Follow Verification, Agent Escalation Pattern (March 9, 2026)

**Goal**: Execute the first production outbound engagement run for EN (@meruru_tcbn sub-account) using the full Outbound agent workflow built in Session 30.

**Problem 1 — Wrong OAuth tokens**: All accounts in `config/accounts.json` shared the same `access_token` (prefix `777944572160724996-`), which belonged to the app owner's personal account — not @meruru_tcbn (`1962081689238491136`). The X API returned success for likes/follows/replies, but actions were applied to the wrong account. No activity appeared on @meruru_tcbn.

**Fix**: Ran PIN-based OAuth 1.0a 3-legged flow (`tweepy.OAuth1UserHandler` with `callback='oob'`) while logged into X as @meruru_tcbn. Generated new tokens with correct prefix `1962081689238491136-`. Updated EN and EN-subaccount entries in `config/accounts.json`.

**Verification method**: To confirm follows actually work, the system must query the authenticated user's following list via API (`client.get_users_following` with bearer token) rather than trusting the follow API's success response. Tested by following @JosephinaM3131 (confirmed not in following list), then re-querying — following count went from 22 to 23 with the account present.

**Problem 2 — Reply 403 restriction**: All reply attempts failed with `"Reply to this conversation is not allowed because you have not been mentioned or otherwise engaged by the author"`. This is an X platform restriction on newer/low-follower accounts, not a credentials issue.

**Problem 3 — Agent philosophy gap**: The original implementation just logged reply failures and stopped. The operator's feedback: *"An agent should think autonomously and make every effort to achieve the goal. If it can't reply via API, it should ask a human to reply — specifying which account, which post, and what text."* Reporting a blocker and stopping is script behavior, not agent behavior.

**Solution**: Implemented a **failed action escalation pattern** — when API actions fail, the system collects them with exact actionable instructions (tweet URL + reply text) for the human operator to complete manually.

**Production results** (2 outbound rounds):

| Action | Round 1 (API) | Round 2 (API) | Manual | Total |
|---|---|---|---|---|
| Likes | 12 | 8 | — | 20 |
| Follows | 3 | 1 | — | 4 (+1 test) |
| Replies | 0 (all 403) | 0 (403) | 5 | 5 |

Accounts engaged: @Angelwithcakee, @yogana_19, @IvoryLane_plus, @HannaJonso (Round 1), @IsabellaCruz_47, @Estherbron1 (Round 2), @JosephinaM3131 (test follow kept).

**Files modified** (4):
- `config/accounts.json` — EN and EN-subaccount tokens updated to @meruru_tcbn's OAuth tokens
- `scripts/publisher.py` — Smart-outbound reply failure now tracks `failed_replies` array in outbound log with tweet URL and reply text for human escalation
- `agents/outbound.md` — Added Step 7: after execution, check `failed_replies` and escalate to Marc with actionable instructions for manual posting
- `agents/marc_publishing.md` — After outbound, check outbound log for `failed_replies` and send Telegram message with manual reply instructions

**Rules added** (1):
- `config/global_rules.md` — "When an API action fails, don't just report and stop — find an alternative path. Agents think and adapt; scripts just fail."

**Key lesson**: The distinction between an agent and a script is not the technology — it's the behavior when blocked. A script fails and reports. An agent reasons about alternatives and finds a path to the goal, even if that path involves escalating to a human with exact instructions.

**Also in this session — Telegram Image Support Fix**:

The operator shared an AI-generated image via Telegram with a caption asking Marc to evaluate it. The bot's `handle_photo` function failed with `"error: unknown option '-a'"` — it was using a non-existent `-a` flag on `claude -p` and was hardcoded to only parse metrics screenshots.

**Fix**: Rewrote `handle_photo` to route images through conversational Marc via `claude -p --dangerously-skip-permissions`. The image is saved locally and its path is embedded in the prompt so Claude reads it via the Read tool (which supports images). The caption becomes the user's message. This uses the same Max subscription auth as the text conversation — no API key needed.

**Additional file modified** (1):
- `scripts/telegram_bot.py` — `handle_photo` rewritten: general-purpose image + caption → conversational Marc (was: hardcoded metrics screenshot parser with broken `-a` flag)

### Session 33 — Third Outbound Run + Scheduling Architecture Decision (March 10-11, 2026)

**Goal**: Run daily outbound engagement for EN, evaluate Claude Code's new scheduled tasks feature for pipeline scheduling.

**Outbound run (Round 3)**: Used strategy from `data/strategy/strategy_20260309.json` with 4 targets: @tanarainw (191K), @iiCoraMaay (17.8K), @baharaykin (12.6K), @NotjustRen00 (16.7K).

Before planning, verified @meruru_tcbn's actual following list via bearer token API (`get_users_following`) — found 3 of 4 targets already followed (likely manually by operator), only @baharaykin not followed. This programmatic check prevented wasting 3 follow attempts.

| Action | Result |
|---|---|
| Likes | 12/12 succeeded |
| Follows | 1/1 succeeded (@baharaykin) |
| Replies | 0/4 (all 403 — reply restriction still active on new account) |

Failed replies escalated to operator with tweet URLs and reply text per the escalation pattern established in Session 32.

**Files created** (2):
- `data/outbound/outbound_plan_20260310_EN.json` — Outbound plan with safety checks (API-verified follow status)
- `data/outbound/outbound_log_20260310.json` — Execution log with 4 `failed_replies` entries

**Scheduling architecture decision**: Evaluated Claude Code's new scheduled tasks feature (`/loop` CLI and Desktop Scheduled Tasks) against system cron for our pipeline scheduling needs.

- **CLI `/loop`**: Session-scoped (dies on exit), 3-day auto-expiry. Not viable for unattended operation.
- **Desktop Scheduled Tasks**: Persistent, catches up missed runs, but requires Desktop GUI app open + computer awake. Agent teams explicitly not available in Desktop.
- **System cron**: Fully headless, survives restarts, proven reliability.

**Decision**: System cron remains the right choice. Claude Code's scheduling features are designed for developer-in-the-loop workflows (build polling, PR monitoring), not unattended agent pipelines. Our Telegram bot daemon + cron (or Python APScheduler inside the bot) provides the reliability our system needs.

**Model assignment per agent**: Previously all agents ran on Opus (inherited from parent). Implemented per-agent model selection — Strategist elevated to Opus because strategy is the foundation all downstream agents depend on:

| Agent | Model | Rationale |
|---|---|---|
| Marc (team leader + conversation) | **Opus** | Complex coordination, judgment, multi-step reasoning |
| Strategist | **Opus** | Core strategy — everything downstream depends on it |
| Scout | **Sonnet** | Structured data analysis and pattern detection |
| Creator | **Sonnet** | Creative writing + structured JSON output |
| Outbound | **Sonnet** | Safety reasoning + contextual reply crafting |
| Analyst | **Sonnet** | Metrics analysis + daily report generation |
| Publisher | — | Script only, no LLM |

**Cron scheduling implemented**: 3 daily cron jobs for autonomous pipeline operation.

| Time (JST) | Task | Script |
|---|---|---|
| 06:00 | Pipeline (Scout → Strategist → Creator → Preview) | `cron_wrapper.sh pipeline` |
| 14:00 | Outbound (likes, replies, follows) | `cron_wrapper.sh outbound` |
| 22:00 | Metrics (collection + daily report) | `cron_wrapper.sh metrics` |

Publishing remains manual (requires human approval via Telegram).

**Files created** (4):
- `scripts/cron_wrapper.sh` — Cron entry point (environment setup, logging, Telegram error notification)
- `scripts/run_outbound.sh` — Daily outbound engagement for active accounts
- `scripts/run_metrics.sh` — Metrics collection + daily report
- `scripts/install_cron.sh` — Install/remove/show cron schedule

**Files modified** (6):
- `agents/marc.md` — Agent team table with model column + rationale
- `agents/marc_pipeline.md` — Scout (sonnet), Strategist (opus), Creator (sonnet) spawn prompts
- `agents/marc_publishing.md` — Outbound (sonnet), Analyst (sonnet) spawn prompts
- `agents/marc_conversation.md` — Team table with model column
- `CLAUDE.md` — Agent definitions with model annotations
- `docs/context.md` — Session 33 updates

---

### Session 34 — PDCA War Rooms: Morning/Evening Briefings with Feedback Loop (March 12, 2026)

**Goal**: Close the PDCA loop. The system did Plan (strategy/content) and Do (publish/outbound) but the Check→Act transition was broken — Analyst collected metrics but insights never fed back to Strategist. A/B tests ran indefinitely without auto-concluding. Category performance never adjusted content mix.

**Solution**: Two autonomous War Room sessions per day:
- **Morning War Room (05:30 JST)** — Marc reviews yesterday's results, sends operator briefing via Telegram before the pipeline runs
- **Evening War Room (22:00 JST)** — Marc collects metrics, generates daily report, produces `strategy_feedback_{date}.json` for tomorrow's Strategist

The key new artifact is `data/strategy/strategy_feedback_{YYYYMMDD}.json` — the missing bridge from Check to Act. It contains category performance rankings, A/B test evaluations (with auto-conclusion at high confidence), posting time effectiveness, outbound effectiveness, and recommended adjustments with confidence levels.

**Strategist PDCA integration** (new Step 1.5): Strategist now reads yesterday's strategy feedback before generating today's strategy. Confidence-based rules control how aggressively adjustments are applied:
- `high` confidence → apply directly (shift content_mix 5-10%, swap time slots, conclude A/B test)
- `medium` confidence → apply conservatively (shift 2-5%)
- `low` confidence → note in key_insights only, no changes
- Core strategy constraints (grok_interactive minimums, zero EN hashtags) are inviolable

**Cron schedule updated**: 4 daily jobs (was 3). Standalone `metrics` job removed (absorbed into evening war room).

| Time (JST) | Task | Script |
|---|---|---|
| 05:30 | Morning War Room | `cron_wrapper.sh morning_warroom` |
| 06:00 | Pipeline (Strategist reads feedback) | `cron_wrapper.sh pipeline` |
| 14:00 | Outbound (likes, replies, follows) | `cron_wrapper.sh outbound` |
| 22:00 | Evening War Room (metrics + feedback) | `cron_wrapper.sh evening_warroom` |

**Publishing workflow trimmed**: Steps 5-8 (metrics, summaries, daily report, alerts) moved from `marc_publishing.md` to `marc_warroom.md`. Publishing is now steps 1-4 only (post → validate → outbound → publish report).

**Files created** (2):
- `agents/marc_warroom.md` — War room playbook (morning briefing + evening metrics/feedback workflow)
- `scripts/run_warroom.sh` — War room entry point (accepts `morning` or `evening` arg)

**Files modified** (7):
- `agents/strategist.md` — Added Step 1.5 (read strategy_feedback, confidence-based adjustment rules)
- `agents/marc.md` — Added War Rooms workflow reference
- `agents/marc_publishing.md` — Removed steps 5-8 (moved to evening war room)
- `scripts/cron_wrapper.sh` — Added `morning_warroom` and `evening_warroom` cases
- `scripts/install_cron.sh` — New 4-job schedule, updated `show_schedule()`
- `scripts/validate.py` — Added `validate_strategy_feedback()` (8 checks) and `validate_morning_briefing()` (5 checks)
- `scripts/run_metrics.sh` — Added deprecation header (kept functional for manual re-runs)

**Session 34 continued — Telegram bot performance fix, cron execution, content plan HTML fix**:

**Telegram bot timeout fix** (4 iterations):
- Problem: `claude -p` in conversational layer took >120s, causing "Sorry, I took too long to respond" errors
- Root cause: Running `claude -p` from the project directory loaded all CLAUDE.md files (massive context), making even simple responses take 120s+
- Fix: Changed `cwd` to `$HOME` to avoid loading project context files. Added `--allowedTools ""` and `--no-session-persistence` flags. Response time dropped from 120s → 37s.
- Also: truncated history (500 chars/msg, max 10 messages), added `--model sonnet` for faster responses

**Cron execution**: All 4 daily jobs installed and executed successfully (morning war room, pipeline, outbound, evening war room).

**Content plan HTML rendering fix**:
- Problem: `content_plan_20260312_EN.html` showed truncated image prompts — operator couldn't verify character lock compliance
- Root cause: Marc used `generic` report type which dumps JSON as flat tables, truncating image_prompt. A dedicated `content_plan` report type already existed with full structured rendering (meta, subject, outfit, pose, scene, camera, lighting, mood + Copy JSON buttons)
- Fix: Updated `marc.md` and `marc_conversation.md` "Reporting to Operator" sections to list correct report types. Added warning: "Never use `generic` for content plans"

**Creator + Meruru concept integration**:
- Problem: `agents/creator.md` didn't reference `config/meruru_concept.md` — Creator relied only on `image_prompt_guide.md` for character info, missing voice rules, NG list, and content pillar definitions
- Fix: Added `config/meruru_concept.md` as required input in Creator Step 5. Creator now reads character lock (physical traits), voice rules (casual lowercase, never starts with "I"), content pillars, and NG list (no body comparisons, no political opinions, etc.)

**Files modified** (4):
- `agents/marc.md` — Updated "Reporting to Operator" with correct report types (content_plan, daily_report, content_preview, generic)
- `agents/marc_conversation.md` — Updated "Delivery Format" with correct report types
- `agents/creator.md` — Added `config/meruru_concept.md` as required input (Step 5 + metadata)
- `scripts/telegram_bot.py` — Performance fix: cwd=$HOME, --allowedTools "", --no-session-persistence, history truncation

### Session 35 — War Room Multi-Agent Discussion: Cross-Examination Protocol (March 12, 2026)

**Goal**: Convert war rooms from solo-Marc operations (reads data alone, composes briefings) into real-time multi-agent discussions. The previous output was just facts — follower counts, posts published — with no strategic debate. The operator wanted agents to actively discuss, challenge each other, and surface disagreements.

**Solution**: Both morning and evening war rooms now spawn a 3-agent discussion team:
- **Marc (Opus)** — Moderator. Sets agenda, asks probing questions, synthesizes conclusions.
- **Analyst (Sonnet)** — Data advocate. Presents numbers, challenges unsupported claims with data.
- **Strategist (Opus)** — Strategy advocate. Proposes changes, defends decisions, admits failures.

**3-Round Discussion Protocol**:
1. **Round 1 — Independent Briefings** (parallel): Analyst prepares KPI report; Strategist prepares strategy assessment. Both work simultaneously.
2. **Round 2 — Cross-Examination**: Marc sends each agent's findings to the other for challenge. Analyst asks "where's the data?" Strategist asks "is this noise or signal?"
3. **Round 3 — Recommendations**: Both agents propose top 3 actionable recommendations. Marc merges them.

**Early termination**: If Round 2 shows clear consensus, Marc skips Round 3 to save cost.

**Fallback**: If a teammate fails to respond within 2 minutes, Marc falls back to solo briefing. Output still passes validation (`discussion` is a soft check).

**Output schema enhanced**: Both `morning_briefing_{date}.json` and `strategy_feedback_{date}.json` now include an optional `discussion` section with:
- `participants` — who was in the discussion
- `rounds` — summary of each round's contributions/exchanges
- `key_debates` — topics where agents disagreed, with positions and resolutions
- `consensus_points` — what both agents agreed on
- `unresolved` — disagreements flagged for operator

**Telegram messages enhanced**: Now include "Discussion Highlights" section showing key agent quotes, debates, and consensus points.

**Cost controls**: Max 3 rounds, each agent message < 1000 words, morning target < 10 min, evening < 15 min.

**Files modified** (5):
- `agents/marc_warroom.md` — Full rewrite: solo-Marc → 3-round discussion protocol with spawn prompts, cross-examination templates, and synthesis workflow
- `agents/analyst.md` — Added "War Room Discussion Mode" section: DATA ADVOCATE role, behavior rules, prep checklists, cross-examination guidelines
- `agents/strategist.md` — Added "War Room Discussion Mode" section: STRATEGY ADVOCATE role, signal vs noise rules, pivot willingness, prep checklists
- `scripts/run_warroom.sh` — Updated both morning/evening `claude -p` prompts to explicitly require multi-agent discussion ("You MUST spawn Analyst and Strategist as teammates")
- `scripts/validate.py` — Added soft-check `discussion` validation to both `validate_morning_briefing()` and `validate_strategy_feedback()` (warns but doesn't fail — backward compatible with solo-Marc fallback)

### Session 36 — War Room Subagent Redesign + API Replies Disabled (March 13, 2026)

**Problem**: Session 35's Agent Teams implementation failed in practice. Both war room runs got stuck — teammates completed work and called SendMessage successfully, but Marc never received the messages. Root cause: Agent Teams async messaging doesn't reliably work in `claude -p` non-interactive mode. Marc's turn ended after spawning teammates, and the async message delivery never woke him up.

**Investigation**: Traced through session transcripts. Both Analyst and Strategist completed their tasks and sent messages with `success: true`, but Marc's transcript ended at "Waiting for their briefings..." with no further entries. Consulted Agent Teams docs at https://code.claude.com/docs/en/agent-teams — confirmed that subagents (blocking Agent tool calls) are the correct pattern for this use case, not Agent Teams (designed for inter-agent peer communication).

**Solution**: Replaced Agent Teams with **subagents** (Agent tool without `team_name`):
- Each subagent call **blocks** until the agent completes and **returns results directly** to Marc
- No async messaging, no `TeamCreate`, no `SendMessage`, no `shutdown_request`
- Round 1: Spawn Analyst + Strategist as **parallel subagents** (`run_in_background: true`)
- Rounds 2-3: Same pattern — parallel blocking subagent calls with cross-examination context
- Marc has all results directly from return values — no message coordination needed

**Result**: Evening war room ran successfully. Produced both `daily_report_20260313.json` and `strategy_feedback_20260313.json` with full 3-round discussion (3 participants, 3 rounds, 7 consensus points, 3 key debates). Both files passed validation.

**Discussion quality highlights**:
- Strategist self-graded D — strategy irrelevant for 4 consecutive days
- Analyst challenged Strategist's proposed content mix change as "no data basis" — Strategist walked it back
- Both converged on #1 priority: fix measurement gap before optimizing
- Consensus: stop API replies (100% failure for 5 days), max likes to 30/day, retire A/B test

**Operator decisions from war room output**:
- **API replies disabled**: Set `max_replies_per_day: 0` for both EN and JP in `config/outbound_rules.json`. All API reply attempts have failed with 403 for 5 consecutive days (X spam prevention for new/low-follower accounts). Outbound now likes-only. Updated `config/global_rules.md`.

**Key architectural lesson**: Agent Teams vs Subagents:
- **Agent Teams** = peer-to-peer async messaging between teammates. Best for long-running collaborative work where agents need to talk to each other.
- **Subagents** = blocking calls that return results to the caller. Best for focused tasks where agents report back to a coordinator (our war room pattern).
- In `claude -p` mode, subagents are more reliable because they block and return — no dependency on async message delivery.

**Files modified** (3):
- `agents/marc_warroom.md` — Rewrite: Agent Teams → subagents. Added "How Subagents Work" section. All spawn prompts changed from teammate messaging to blocking Agent tool calls with `run_in_background: true` for parallelism.
- `scripts/run_warroom.sh` — Removed `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Updated prompts: "spawn as SUBAGENTS using the Agent tool" instead of "spawn as teammates". Explicit instructions to use blocking calls.
- `config/outbound_rules.json` — `max_replies_per_day: 0` for both EN and JP
- `config/global_rules.md` — Updated outbound limits: "0 replies" with reason (403 blocked for new accounts)

### Session 37 — Cron Auth Failure Fix: Long-Lived Token for Headless Auth (March 14, 2026)

**Problem**: All cron-scheduled jobs (morning warroom, evening warroom, pipeline, outbound) failed starting March 13 with `Not logged in · Please run /login`. The error appeared in every cron log:
- `cron_morning_warroom_20260313.log`: Failed at 05:31
- `cron_pipeline_20260313.log`: Failed at 06:00
- `cron_evening_warroom_20260313.log`: Failed at 22:00

Meanwhile, the same commands worked fine in interactive terminals.

**Initial hypothesis (wrong)**: The plan proposed that `env -u CLAUDECODE` in shell scripts was stripping auth context. Testing proved this **incorrect** — `env -u CLAUDECODE` is required to allow nested `claude -p` invocations (prevents "Nested sessions share runtime resources" error). Removing it breaks all invocations from within Claude Code. From cron, `CLAUDECODE` is never set, so `env -u CLAUDECODE` is a no-op. All proposed changes were reverted.

**Root cause (actual)**: Claude Code authenticates via OAuth tokens from `claude.ai`, stored in the macOS Keychain under `"Claude Code-credentials"`. These tokens have a limited lifetime (~12-24h). Cron processes can read the Keychain but cannot refresh expired tokens interactively. The token was last refreshed on March 12 21:06 JST (via interactive session) — by the next morning's cron run at 05:31 JST, it had expired.

**Evidence**:
- Keychain entry `"Claude Code-credentials"` created `2026-03-12 12:06:29 UTC`, last modified `2026-03-13 18:58:54 UTC`
- March 12 warroom runs at 12:43 JST succeeded (fresh token from interactive session)
- March 13 runs starting at 05:31 JST all failed (token expired, no interactive session to refresh)
- `claude auth status` showed `loggedIn: true` only after an interactive session refreshed the token

**Solution**: Ran `claude setup-token` to create a **long-lived authentication token** (valid ~1 year, prefix `sk-ant-oat01-`). This token is stored in the Keychain and used by all `claude -p` invocations without requiring interactive refresh. Verified auth works in a minimal cron-like environment (`env -i HOME=$HOME PATH=... claude auth status` → `loggedIn: true`).

**No code changes required** — the shell scripts and telegram bot were correct all along. The fix was purely an auth credential setup.

**Key lesson**: `claude -p` in cron requires `claude setup-token` for long-lived auth. The default OAuth flow (`claude auth login`) produces tokens that expire and need interactive refresh — unsuitable for headless/cron use. This is documented in Claude Code's headless mode docs.

### Session 38 — Auto-Schedule Slot Publishing on Approval (March 14, 2026)

**Problem**: When the operator approved all posts via `/approve EN`, then called `/publish EN`, all approved posts were published simultaneously because all `scheduled_time` values had already passed. The operator wanted each slot to publish automatically at its designated time — triggered by approval itself, not a separate `/publish` call.

Previously, per-slot cron entries were manually added (March 13) to work around this:
```
0 6 13 3 * cd /path && python3 scripts/publisher.py post --account EN --slot 3 # X-AGENTS-PUBLISH-SLOT3
```

**Solution**: Automated per-slot cron scheduling triggered by `/approve`.

**New file — `scripts/schedule_slots.py`**:
- Accepts `--account EN [--date YYYYMMDD]`
- Loads the content plan, finds approved posts with future `scheduled_time`
- Removes all existing `# X-AGENTS-PUBLISH-SLOT` cron entries (clean slate)
- Adds date-specific cron entries (`{min} {hour} {day} {month} *`) that fire once at each slot's UTC time
- Handles both UTC and JST time formats (converts JST → UTC for cron)
- Skips past times with a warning; prints summary for Telegram

**Modified — `scripts/telegram_bot.py` (`cmd_approve`)**:
- After saving approved content plan, calls `schedule_slots.py`
- Operator sees both "3 post(s) approved" AND scheduled times in the Telegram response
- Re-approval automatically clears old entries (clean slate logic)

**Also in this session**:
- Rescheduled March 13 slots 02-04 to March 14 (slot 01 was already posted, 02-04 were deleted after the simultaneous publish issue)
- Created `content_plan_20260314_EN.json` with slots 02-04 as approved
- Copied images from `media/posted/` back to `media/pending/` with updated `EN_20260314_*` IDs
- Morning warroom cron at 05:30 failed again with "Not logged in" — confirmed this was a timing issue (the `setup-token` from Session 37 was applied around the same time; manual `run_warroom.sh morning` succeeded afterward)

**Artifacts**:
- `scripts/schedule_slots.py` — new helper
- `scripts/telegram_bot.py` — modified `cmd_approve` (~line 452)
- `data/content/content_plan_20260314_EN.json` — rescheduled slots 02-04

### Session 39 — Following-Aware Target Selection (March 15, 2026)

**Problem**: The Outbound agent wasted follow budget because no upstream agent knew which accounts were already followed. On March 14, 0 of 3 follow slots executed — all 4 strategy targets were already followed. The Strategist picks targets from scout data and outbound logs but has no visibility into real follow status. The Outbound agent uses `outbound_history.py` (log-based, known to miss 22/34 actual follows per Session 35 analysis). Only `publisher.py`'s `_fetch_real_following()` knows the truth — but it runs at execution time, too late to find replacements.

**Solution**: Persist the real following list to a shared file. Strategist and Outbound agent both read it to make informed decisions. One API call, shared by all agents.

**Changes (5 files)**:

1. **`scripts/publisher.py`** — Added `run_sync_following()` function + `sync-following` CLI subcommand. Fetches real following list via X API and saves to `data/outbound/following_{account}.json`. Also auto-refreshes after `run_smart_outbound()` completes.

2. **`agents/strategist.md`** — Added Step 1.6 (read following list before analysis). Updated Target Rotation Rules to prioritize unfollowed targets — must include at least `daily_follows` unfollowed accounts. Added `target_follow_status` field to `outbound_strategy` output schema + validation rule 13.

3. **`agents/outbound.md`** — Added input #5 (read `following_{account}.json` as source of truth for follow status). Updated Step 2 Safety Reasoning to use the file instead of `outbound_history.py` for follow decisions.

4. **`agents/marc_pipeline.md`** — Added Step 3.6 (sync following before Strategist spawn).

5. **`agents/marc_publishing.md`** — Added Step 2.5 (refresh following before Outbound spawn).

**Data flow**:
```
Pipeline:  sync-following → Scout → Strategist (reads following list) → Creator → Preview
Publishing: Publisher → sync-following → Outbound (reads following list) → smart-outbound → auto-sync
```

**Output format** (`data/outbound/following_EN.json`):
```json
{"account": "EN", "fetched_at": "...", "count": 41, "following": ["account1", "account2", ...]}
```

**Artifacts**:
- `scripts/publisher.py` — added `run_sync_following()`, `sync-following` subcommand, auto-refresh after smart-outbound
- `agents/strategist.md` — Step 1.6, updated Target Rotation Rules, `target_follow_status` in schema
- `agents/outbound.md` — updated Steps 1 & 2 for following list as source of truth
- `agents/marc_pipeline.md` — Step 3.6
- `agents/marc_publishing.md` — Step 2.5

### Session 39b — Cron→launchd Migration: Permanent Auth Fix (March 15, 2026)

**Problem**: Every cron-scheduled job failed with "Not logged in" since Session 37. The `setup-token` fix (Session 37) stored a long-lived OAuth token in macOS Keychain, but cron runs in a separate security session that **cannot access Keychain items** — even after `security unlock-keychain` succeeds.

**Investigation** (systematic elimination of approaches):

1. **Keychain unlock (`security unlock-keychain`)**: Unlock succeeds (exit 0), but `security find-generic-password` returns "SecKeychainSearchCopyNext: The specified item could not be found in the keychain." The login keychain wasn't even in cron's search list. Adding it via `security list-keychains -d user -s` didn't help — the security session still blocks item-level access.

2. **ANTHROPIC_API_KEY env var**: The OAuth token (`sk-ant-oat01-*`) is not a valid API key. `claude auth status` reports `loggedIn: true` but `claude -p` fails with "Invalid API key". The OAuth token only works through Keychain's OAuth flow.

3. **`apiKeyHelper` setting**: Setting was reverted — incompatible with Claude.ai OAuth authentication method.

**Root cause**: macOS security sessions are strictly isolated. Cron's security session fundamentally cannot access Keychain items created in the user's login session. This is a deliberate macOS security design, not a configuration issue.

**Solution**: Replaced all crontab entries with macOS LaunchAgents (`~/Library/LaunchAgents/com.xagents.*.plist`). LaunchAgents run in the user's login session with full Keychain access.

**Changes**:

| Old (cron) | New (LaunchAgent) | Schedule |
|---|---|---|
| `30 5 * * *` morning_warroom | `com.xagents.morning-warroom.plist` | 05:30 daily |
| `0 6 * * *` pipeline | `com.xagents.pipeline.plist` | 06:00 daily |
| `0 14 * * *` outbound | `com.xagents.outbound.plist` | 14:00 daily |
| `0 22 * * *` evening_warroom | `com.xagents.evening-warroom.plist` | 22:00 daily |

Also updated:
- **`scripts/cron_wrapper.sh`** — Removed Keychain unlock hack. Added note that this script is now invoked by launchd, not cron.
- **`scripts/schedule_slots.py`** — Rewritten to create per-slot LaunchAgent plists (`com.xagents.publish-slot.{date}-{account}-{slot}.plist`) instead of crontab entries. Uses `plistlib` for proper plist generation and `launchctl load/unload` for agent management.

**Verified**: `claude -p "Reply with exactly one word: AUTH_OK"` returned `AUTH_OK` from a LaunchAgent at 06:38 JST. Full Keychain access, Max subscription authenticated.

**Prerequisite**: User must be logged in to macOS (screen-locked is fine; logged out is not).

**Management commands**:
```bash
# List active agents
launchctl list | grep xagents

# Reload an agent after plist change
launchctl unload ~/Library/LaunchAgents/com.xagents.pipeline.plist
launchctl load ~/Library/LaunchAgents/com.xagents.pipeline.plist
```

**Artifacts**:
- `~/Library/LaunchAgents/com.xagents.{morning-warroom,pipeline,outbound,evening-warroom}.plist` — 4 persistent scheduled agents
- `scripts/cron_wrapper.sh` — updated (auth note, Keychain hack removed)
- `scripts/schedule_slots.py` — rewritten for launchd

### Session 40 — Growth Acceleration: Outbound Limits, Tweet Tracking, PDCA Loop Fix, Schedule Resilience (March 16, 2026)

**Context**: @meruru_tcbn had 9 followers after 10 days of operation with 50 total posts. Growth was too slow. Root cause analysis identified four systemic issues: conservative outbound limits, untracked manual posts, a broken morning war room feedback loop, and past-slot scheduling failures.

**Problem 1 — Outbound too conservative**: `config/outbound_rules.json` capped EN likes at 20/day and follows at 3/day, well below the global rules ceiling (30 likes, 5 follows). Actual daily usage was only 9 likes and 0-1 follows — leaving significant growth value unused.

**Fix**: Increased EN limits to max — `max_likes_per_day: 30`, `max_follows_per_day: 5`, `max_targets_per_day: 5`. These match the global rules in `config/global_rules.md`.

**Problem 2 — Manual posts invisible**: Operator was posting reposts and quote tweets manually (14+ untracked posts vs 1 pipeline post in 2 days). These posts had no metrics collection, no category tracking, and no performance feedback — a major blind spot for the war room and strategy optimization.

**Fix**: Created `scripts/fetch_account_tweets.py` — fetches the account timeline via X API, cross-references against all content plans, and identifies untracked tweets. Classifies each as original/retweet/quote/reply using the new `referenced_tweets` field. Outputs to `data/metrics/untracked_tweets_{YYYYMMDD}_{account}.json`. With `--collect-metrics` flag, stores metrics in SQLite via `db_manager.insert_post_metrics()` with `source: "timeline_scan"`.

Supporting change: Added `referenced_tweets` to `TWEET_FIELDS` in `scripts/x_api.py` and updated `_normalize_tweet()` to include tweet type data. All API callers (Scout, Analyst, Outbound) now receive tweet type information.

**Problem 3 — Morning War Room feedback loop broken**: Morning war room (05:30 JST) produced recommendations via multi-agent discussion, but the pipeline (06:00 JST) never read them. The Strategist only consumed `strategy_feedback_{yesterday}.json` from the evening war room — morning briefing recommendations went to Telegram only and were completely ignored by the system.

**Fix**: Added **Step 1.55** to `agents/strategist.md` — "Read today's morning briefing if available (same-day PDCA)". The Strategist now reads `data/metrics/morning_briefing_{YYYYMMDD}.json` and applies its recommendations using the same confidence-based rules as the evening feedback. Morning briefing takes priority over evening feedback when they conflict (it's more recent and incorporates the latest data). Updated `agents/marc_pipeline.md` Step 4 to pass the morning briefing path to the Strategist spawn prompt.

**PDCA loop now complete**:
```
Evening War Room (22:00) → strategy_feedback_{yesterday}.json → Strategist Step 1.5
Morning War Room (05:30) → morning_briefing_{today}.json → Strategist Step 1.55  ← NEW
Pipeline (06:00) → Strategist applies BOTH → strategy → Creator → Outbound
```

**Problem 4 — Past-slot scheduling silently drops posts**: `schedule_slots.py` skipped any slot whose `scheduled_time` had already passed (line 134: `if utc_dt <= now_utc: skipped`). If the operator approved after a slot time, that post was permanently lost. This contributed to the low 1 post/day cadence vs the 4/day target.

**Fix**: Rewrote the scheduling logic. Past slots are now **rescheduled** instead of skipped — starting at now + 5 minutes with 30-minute staggered gaps between posts (to avoid ghost tweets on new accounts). The script also avoids collision with any future scheduled slots. Example: if 2 of 4 slots have passed, they get rescheduled to 15:05 and 15:35, while the other 2 keep their original future times.

**Decision 17**: Outbound limits should match global rules ceiling — conservative margins below the global max leave growth value unused with no safety benefit.

**Decision 18**: Morning war room output must feed into the same-day pipeline. Any PDCA discussion that doesn't reach the agents it's meant to influence is wasted compute.

**Files created** (1):
- `scripts/fetch_account_tweets.py` — Timeline scanner for untracked tweet discovery and metrics collection (~200 lines)

**Files modified** (5):
- `config/outbound_rules.json` — EN likes 20→30, follows 3→5, targets 4→5
- `scripts/x_api.py` — Added `referenced_tweets` to `TWEET_FIELDS`, updated `_normalize_tweet()` with tweet type extraction
- `agents/strategist.md` — Added Step 1.55 (read morning briefing for same-day PDCA feedback)
- `agents/marc_pipeline.md` — Updated Strategist spawn prompt to include morning briefing path
- `scripts/schedule_slots.py` — Past slots rescheduled with 30-min stagger instead of silently skipped

### Session 41 — Fix EN Posting Slot Time Alignment: UTC Wrap Bug (March 16, 2026)

**Context**: EN content plan for March 16 had Slot 4 scheduled at `00:30 UTC`. `schedule_slots.py` uses the content plan date (March 16) for all slots, converting `00:30 UTC` → `09:30 JST March 16`. This fired **before** Slot 1 (`13:00 UTC` → `22:00 JST March 16`), breaking the intended posting order. The post was published out of sequence.

**Root cause**: The Strategist's EN optimal time window included `00:00-01:00 UTC`, which wraps to the previous JST day. `schedule_slots.py` correctly converts UTC to JST using the content plan date, so any UTC time before ~13:00 converts to a JST time earlier than the pipeline's 06:00 JST start — meaning it fires before the operator can prepare images.

**Fix approach**: Constraint-based — no code changes to `schedule_slots.py`. Instead, constrained the Strategist to only pick EN times within `13:00-23:59 UTC`, which converts to `22:00 JST → 08:59 JST+1` — all safely after the pipeline runs. The `00:00-01:00 UTC` window (7-8 PM ET) shifted to `23:00-23:59 UTC` (6-7 PM ET), still capturing US evening audience.

**Changes**:
1. `agents/strategist.md` — Updated Posting Cadence section: EN optimal times now `13:00-14:00, 17:00-18:00, 20:00-22:00, 23:00-23:59 UTC`. Added scheduling constraint note explaining the 13:00-23:59 UTC requirement.
2. `agents/strategist.md` — Added Validation Rule 14: EN posting times must be ascending UTC within 13:00-23:59 range.
3. `data/strategy/core_strategy.json` — Updated `posting_cadence.EN.optimal_times_utc` last entry from `00:00-01:00 UTC` to `23:00-23:59 UTC`. Added `scheduling_constraint` field.

**Decision 19**: Fix scheduling bugs through agent constraints (Strategist rules) rather than code complexity (schedule_slots.py date arithmetic). The Strategist has full freedom to pick times within the safe range based on daily scout data — only the unsafe wrap zone is excluded.

**Files modified** (2):
- `agents/strategist.md` — Posting Cadence update + Validation Rule 14
- `data/strategy/core_strategy.json` — optimal_times_utc + scheduling_constraint

### Session 42 — Self-Improving Outbound Agent: Learning Loop, Cross-Agent Intelligence, Adaptive Targeting (March 17, 2026)

**Context**: Marc briefed the Outbound agent on a "beauty-first" targeting strategy shift (target beauty fans/followers of competitors, not competitors themselves). The briefing was saved to `data/outbound/outbound_briefing_beauty_first_20260317.json`, but Outbound's instructions had no step to read briefing files — it would have ignored the strategy shift entirely. More fundamentally, Outbound was a static executor: it read the strategy, executed likes/follows, and stopped. No review of past performance, no cross-agent intelligence, no adaptation.

**Problem**: Outbound agent had no capability to:
1. Read operator briefings or strategy shifts
2. Review its own past performance (follow-back rates, engagement reciprocity)
3. Learn from other agents' outputs (Scout discoveries, Analyst metrics, Strategist feedback)
4. Adapt its targeting criteria based on accumulated learnings
5. Propose strategic changes to Marc based on data patterns

**Fix — Redesigned Outbound as a learning agent with 3 new capabilities:**

1. **Step 0: Daily Intelligence & Adaptation** (runs before execution):
   - **Self-review** (0.1): Reads past outbound logs, evaluates follow-back rates, engagement reciprocity, skip rates, wasted budget
   - **Cross-agent intelligence** (0.2): Reads Scout reports (new accounts), strategy feedback (effective/ineffective targets), morning briefings, daily reports, operator briefings, and its own journal
   - **Adaptive reasoning** (0.3): Decides what to change today — target sources, scoring thresholds, engagement style, new filters
   - **Proposals to Marc** (0.4): Flags strategic changes that need Marc's or Strategist's attention (e.g., "follow-back rate dropped — recommend shifting targets")

2. **Step 8: Outbound Journal** (persistent learning):
   - Writes `data/outbound/outbound_journal_{account}.json` — cumulative learnings across runs
   - Tracks: effective/ineffective target traits, follow-back rate history, scoring adjustments, active hypotheses with evidence
   - Read at start of each run, appended after — institutional knowledge that compounds

3. **Target priority system** (replaces static strategy targets):
   - Priority order: briefing targets > journal-informed targets > strategy targets > scout discoveries
   - Scoring thresholds and engagement styles adapt based on journal data

**Design principle**: Agents should be learning systems, not static executors. The Outbound agent now has its own PDCA loop: review yesterday's results → adapt today's plan → execute → record learnings → feed tomorrow's review. This mirrors the war room PDCA loop for content strategy but operates at the individual agent level.

**Decision 20**: Agents that interact with external systems (outbound, publisher) should maintain persistent journals tracking what works and what doesn't. The journal is the agent's institutional memory — it compounds over time and prevents repeating the same mistakes.

**Files modified** (1):
- `agents/outbound.md` — Added Step 0 (Daily Intelligence & Adaptation), Step 8 (Outbound Journal), target priority system, daily_adaptation field in plan schema

### Session 42b — X Analytics CSV Import: Daily Impressions & Engagement Data (March 17, 2026)

**Context**: The X API Basic plan does not provide impression data. The Analyst's `post_metrics` table had `impressions: NULL` for all 36 tracked posts. Meanwhile, X's data export and Analytics dashboard provide daily account-level impressions, profile visits, bookmarks, new follows/unfollows — metrics unavailable via API.

**Solution**: Built a CSV import pipeline for X Analytics dashboard exports:

1. **New `daily_analytics` table** in SQLite — stores daily account-level metrics: impressions, likes, engagements, bookmarks, shares, new_follows, unfollows, replies, reposts, profile_visits, posts_created, video_views, media_views. Primary key: `(account, date)`.

2. **`scripts/import_analytics_csv.py`** — Parses the X Analytics CSV format (`Date,Impressions,Likes,...`), converts dates, and writes to `daily_analytics` via `db_manager`. Supports `--dry-run` and `--account` flags. Uses `INSERT OR REPLACE` for safe re-imports.

3. **`db_manager.py` updates** — Added `insert_daily_analytics()`, `get_daily_analytics()`, and `get_daily_analytics_range()` functions.

**Initial import**: 7 days of EN data (Mar 11-17). Key finding: Mar 14 had 3,163 impressions (2.6x the 7-day average of 1,209) — worth investigating what drove the spike.

**Operator workflow**: Periodically download CSV from X Analytics dashboard → run `python3 scripts/import_analytics_csv.py <csv_path> --account EN`. The Analyst and war room agents can now query `daily_analytics` for impression-based engagement rates and profile visit trends.

**Files created** (1):
- `scripts/import_analytics_csv.py` — CSV import script for X Analytics data

**Files modified** (1):
- `scripts/db_manager.py` — Added `daily_analytics` table schema, insert and query functions

### Session 42c — Per-Post Impression Import + Analytics-Aware Agents + Never-Skip Pipeline (March 17-18, 2026)

**Context**: Operator imported 2 weeks of X Analytics CSV data including **per-post impressions** — the missing metric. Analysis revealed critical insights: replies to large accounts generate 2-70x more impressions than original posts (@katekarsyn reply = 2,823 impressions, 24% of all account impressions from 1 reply). Original image posts outperform Grok posts (5.4% vs 3.6% ER). Mar 16 raw iPhone aesthetic posts hit 7-10% ER (3-4x previous average).

**Per-post analytics import**: Extended `import_analytics_csv.py` to auto-detect CSV type (daily overview vs per-post content). Added `post_analytics` table to SQLite storing per-tweet: impressions, likes, engagements, bookmarks, profile_visits, detail_expands, url_clicks. Imported 66 posts (Mar 4-17).

**Analytics-aware agents** — All four execution agents now read and learn from analytics data:

1. **Strategist** (Steps 1.6, 1.65): Reads `post_analytics` and `daily_analytics` tables for impression-based content mix decisions, caption style optimization, reply target ROI analysis. Reads strategy meeting reports as high-confidence directives.

2. **Creator** (Step 7): Reads past post performance to inform creative decisions — which captions drove highest ER, which categories got most impressions, which posts got bookmarked (save-worthy patterns), which drove profile visits (follower conversion content).

3. **Analyst** (Step 1.7, enhanced Step 2.2, new Step 2.6): Reads X Analytics tables for impression-based ER, profile visit rates, bookmark rates. Category breakdown now includes impression-weighted metrics. New Reply Performance Analysis ranks reply targets by impression ROI for the Outbound agent.

4. **Outbound** (already updated in Session 42): Step 0 learning loop already reads reports and adapts targeting.

**Strategy meeting**: Marc + Strategist analyzed the full 2-week dataset. Key decisions: engagement_questions 30%→40%, image_showcase 35%→25%, manual replies elevated to #1 growth lever (4/day to Tier 1 targets), raw iPhone aesthetic locked as permanent default, new A/B test: questions vs statements.

**Never-skip pipeline**: The regular 06:00 JST pipeline was skipping when it found existing pipeline state from ad-hoc runs. Fix: `marc_pipeline.md` Step 1 now explicitly instructs Marc to rename existing state to `_prev` and run fresh. `run_pipeline.sh` prompt reinforces "CRITICAL: NEVER skip."

**Decision 21**: Per-post impression data from X Analytics CSV is the most valuable metric the system has. It enables impression-based engagement rates (more accurate than follower-based), reply target ROI analysis, and profile visit attribution. Periodic CSV import should be part of the operator's routine.

**Decision 22**: Agents should never skip scheduled runs based on existing state. Ad-hoc runs create artifacts that confuse scheduled runs. Solution: archive existing state and run fresh.

**Files created** (0 new — extended existing)

**Files modified** (6):
- `agents/strategist.md` — Steps 1.6 (analytics data), 1.65 (meeting reports)
- `agents/creator.md` — Step 7 (performance data for content learning)
- `agents/analyst.md` — Step 1.7 (X Analytics tables), Step 2.2 enhanced, Step 2.6 (reply performance)
- `scripts/db_manager.py` — Added `post_analytics` table, `insert_post_analytics()`, `get_post_analytics()`
- `scripts/import_analytics_csv.py` — Extended to auto-detect and import per-post content CSV
- `agents/marc_pipeline.md` — Step 1: never skip, rename existing state to `_prev`
- `scripts/run_pipeline.sh` — Added never-skip instruction to Marc's prompt

### Session 43 — Data-Driven Content Variety System (March 18, 2026)

**Context**: Creator agent was producing repetitive content — same captions ("not even trying 🤍"), same scenes (minimalist bedroom every plan), same outfits (sports bra 3x), all standing poses. A prior fix had arbitrarily expanded the scene list to 16 unproven scenes (kitchen, car selfie, staircase, etc.), which contradicted the data: only 5 scene types are proven high-engagement from competitor analysis. The fix: variety comes from **within** the 5 proven scenes (sub-variants) and from the Strategist making daily visual direction decisions, not arbitrary expansion.

**Strategist `visual_guidance`**: Added Step 3.7 (Visual Variety Planning) to `agents/strategist.md`. Strategist now reads last 3 content plans, reads operator reference images from `media/reference/`, and outputs a `visual_guidance` block per account with: `scene_rotation` (slot-by-slot scene type + sub-variant assignment with rotation reasoning), `outfit_suggestions` (type + color per slot, no repeats), `pose_mix` (at least 2 different positions), and `recently_used` (scenes/outfits/captions from last 3 days for dedup). Added validation rule 15. This makes the Strategist the single source of truth for visual direction.

**Creator reverted & refactored**: Reverted the arbitrary 16-scene expansion in `agents/creator.md` back to the 5 proven scene types (bedroom mirror, bathroom, beach/pool, gym, cozy casual). Creator now consumes `visual_guidance` from the strategy (Step 8) instead of self-managing dedup. Added Step 9: read operator reference images from `media/reference/` — Creator analyzes full visual composition (scene, outfit, pose, lighting, mood, framing) and uses as primary inspiration, distributed across slots. Fallback preserved for older strategy format without `visual_guidance`.

**Scene sub-variants**: Added `#### Sub-variants` sections to each of the 5 main scene templates in `config/image_prompt_guide.md`. Bedroom mirror: 4 sub-variants (clean minimalist, cozy messy bed, hotel room, getting-ready vanity). Bathroom: 3 (home, hotel luxury marble, steamy minimal). Beach/pool: 4 (shoreline, poolside, sitting on sand, shallow water). Bedroom casual: 3 (sitting on bed, couch lounging, floor sitting). Gym: 3 (mirror by weights, locker room, yoga mat). This creates 17 distinct scene variations from 5 data-backed scene types.

**Caption pattern library**: Added to `config/meruru_concept.md` under Voice section. Six pattern types derived from competitor data: rating ask, binary choice, casual flex, confidence statement, direct address, reaction bait. Rule: 3+ different patterns per 4-post plan, never reuse exact caption from last 5 plans.

**`media/reference/` directory**: New directory for operator reference images. Flat folder — operator drops inspiration images (any format). Both Strategist and Creator read all images (Claude is multimodal) and analyze complete visual composition for scene/outfit/pose/lighting/mood guidance.

**Decision 23**: Content variety should come from sub-variants within data-proven scene types and Strategist-driven visual guidance, not from arbitrary scene expansion. The Strategist owns visual direction; Creator executes it.

**Files modified** (4):
- `agents/strategist.md` — Step 3.7 (visual variety planning), `visual_guidance` in output schema, validation rule 15
- `agents/creator.md` — Reverted 16-scene expansion, Step 8 (consume visual_guidance), Step 9 (reference images), updated validation rules 17-20
- `config/image_prompt_guide.md` — Sub-variant sections for all 5 scene templates
- `config/meruru_concept.md` — Caption pattern library (6 pattern types + rotation rules)

**Files created** (1):
- `media/reference/.gitkeep` — Operator reference image directory

### Session 43b — Cross-Midnight Publish Fix + Manual Reply Dedup (March 19, 2026)

**Context**: Two bugs discovered during live operation.

**Bug 1 — Cross-midnight publish failure**: When posts are approved late (after 22:00 JST), `schedule_slots.py` creates LaunchAgent plists for slots whose UTC times fall after midnight JST (e.g., 17:30 UTC = 02:30 JST next day). When launchd fires these plists, `publisher.py` calls `today_str()` which returns the NEW day's date, so it looks for `content_plan_20260319_EN.json` instead of `content_plan_20260318_EN.json`. Result: "No content plan found" error, posts never published.

**Fix**: Added `--date {date_str}` to the publisher command in `schedule_slots.py` line 85. Publisher already supports the `--date` flag (top-level arg before subcommand). Now the LaunchAgent plist always passes the correct content plan date regardless of when launchd actually fires the job.

**Bug 2 — Manual reply dedup missing**: Outbound agent recommended the same tweet URLs for manual replies across consecutive days. 6 of 13 reply recommendations were duplicates from yesterday. Root cause: likes have dedup (via `outbound_history.py`), follows have dedup (via `following_{account}.json`), but manual replies had zero dedup — no mechanism to check previous `manual_replies` arrays.

**Fix**: Three changes to `agents/outbound.md`:
1. Step 0.1: Added manual reply dedup — reads last 3 days of outbound plans + manual reply files, builds `previously_recommended_reply_urls` set
2. Step 4.3: Added dedup check as FIRST criterion before other filtering — tweet_url must NOT be in `previously_recommended_reply_urls`
3. Added validation rule 8: No `tweet_url` in `manual_replies` may repeat from the last 3 days

**Decision 24**: Publisher commands in LaunchAgent plists must always include explicit `--date` to prevent cross-midnight date drift. Never rely on `today_str()` for scheduled jobs that may fire on a different calendar day than intended.

**Files modified** (3):
- `scripts/schedule_slots.py` — Added `--date {date_str}` to publisher command in LaunchAgent plist
- `agents/outbound.md` — Manual reply dedup in Steps 0.1, 4.3, and validation rule 8
- `docs/context.md` — Session 43b entry

### Session 43c — Require Image for Publish + Image Compression Workflow (March 19-20, 2026)

**Context**: Slot 1 of Mar 19 content plan posted text-only ("deadly 😮‍💨") without any image. The operator hadn't yet placed the image in `media/pending/`. Publisher silently posted text-only because `find_media()` returning `None` simply meant `media_ids=None` in the `create_post()` call — no warning, no skip. For a beauty account, text-only posts are essentially broken.

**Fix — Require image**: Added a guard in `scripts/publisher.py` after `find_media()`: if no image is found and `--force` is not set, the post is SKIPPED with a warning log and status stays `"approved"` so it retries when the image is added. The `--force` flag overrides this for intentional text-only posts (e.g., grok posts where Grok generates the image).

**Image compression workflow**: Multiple images were over the 2MB X API upload limit (3.3-5.0MB PNGs). Used macOS `sips -s format jpeg -s formatOptions 80` to compress to JPEG (typically 450-690KB). Original PNGs renamed to `.oversized`. This should be automated in the publisher in a future session.

**Decision 25**: Publisher must never silently post text-only for beauty accounts. Missing image = skip and keep approved for retry. Text-only posting requires explicit `--force` flag.

**Files modified** (2):
- `scripts/publisher.py` — Image-required guard after `find_media()`, skip if no image unless `--force`
- `docs/context.md` — Session 43c entry

### Session 44 — Fix Approval-Bypasses-Scheduling Bug (March 21, 2026)

**Problem**: When the operator sent a free-form message like "approve slot 1" to conversational Marc (instead of using the `/approve` Telegram command), Marc treated it as a publishing task. Marc approved the post by editing the content plan JSON directly and then called `publisher.py post` — publishing the post immediately instead of scheduling it at the Strategist-recommended time via LaunchAgent.

**Evidence**: Slot 1 of the Mar 20 content plan was scheduled for 13:00 UTC (22:00 JST) but was published at 12:53 UTC (21:53 JST) — 7 minutes early — because Marc called `publisher.py post` directly instead of going through `schedule_slots.py`.

**Root cause**: The `/approve` Telegram command performs two atomic steps: (1) set `status: "approved"`, (2) call `schedule_slots.py` to create LaunchAgents at each slot's designated time. When Marc handled approval via the execution layer, he did step 1 (approve) but skipped step 2 (schedule) and went straight to `publisher.py post` (immediate publish).

**Fix**: Enforced approve+schedule atomicity across all agent instruction files. Marc may approve posts (set status in JSON), but MUST immediately follow with `schedule_slots.py`. Direct `publisher.py post` calls are banned — only LaunchAgents (created by `schedule_slots.py`) may call `publisher.py post --slot {N}` at the designated time.

**Decision 26**: Approval and scheduling are atomic — never approve without scheduling. Never call `publisher.py post` directly. Always go through `schedule_slots.py`, which creates LaunchAgents that fire at each slot's Strategist-recommended time.

**Files modified** (4):
- `agents/marc.md` — Added "Approval & Publishing Boundary" section: approve+schedule atomicity, never call publisher.py directly
- `agents/marc_conversation.md` — Updated publishing rule: approve then schedule, never publish directly
- `agents/marc_publishing.md` — Added guard: approval requires immediate schedule_slots.py call
- `config/global_rules.md` — Added rule: approval and scheduling are atomic (learned 2026-03-21)

### Session 44b — Claude Code Channels Evaluation (March 21, 2026)

**Context**: Anthropic officially launched Claude Code Channels (research preview, v2.1.80+), which allows controlling a Claude Code session through MCP server plugins for Telegram and Discord. Since our system already has a custom Telegram integration (`telegram_bot.py`, 910+ lines), evaluated whether Channels could replace it.

**What Channels Are**: MCP server plugins that push messages into a running Claude Code session. Claude reads the message and replies back through the same channel — a chat bridge between Telegram/Discord and a Claude Code terminal. Setup: install plugin via `/plugin install telegram@claude-plugins-official`, configure bot token, restart with `claude --channels plugin:telegram@claude-plugins-official`, pair via code.

**Comparison**:

| Aspect | Our System (`telegram_bot.py`) | Claude Code Channels |
|---|---|---|
| Architecture | Custom Python daemon with 2-layer design: conversational `claude -p` (Sonnet) + Agent Teams execution (Opus) | MCP plugin pushing messages into a running `claude` session |
| Always-on | Bot runs as standalone daemon (independent process) | Requires Claude Code session to be open — session dies = bridge dies |
| Custom commands | 13 commands (`/approve`, `/publish`, `/pipeline`, `/status`, etc.) with Python logic | No custom commands — everything through Claude's reasoning |
| Atomic operations | `/approve` does approve + schedule in Python (guaranteed together) | Claude must reason about atomicity every time (proven unreliable — Session 44) |
| Cost control | Conversational layer uses Sonnet (cheap, fast ~37s); execution uses Opus only when needed | Single model for everything — no per-layer model selection |
| Image handling | Custom `handle_photo` with vision routing | Not documented for Channels |
| URL enrichment | Custom `fetch_url.py` integration | Claude has native WebFetch |
| Auth | Custom `AUTHORIZED_CHAT_ID` check | Pairing code + allowlist (built-in) |

**Why our system is better (for now)**:
1. **Atomic operations**: `/approve` does approve + schedule in Python code — guaranteed to happen together. With Channels, Claude would need to reason about this every time, and Session 44 proved Claude gets this wrong.
2. **Always-on without a terminal**: Our bot runs as a daemon. Channels require a Claude Code session to be running.
3. **Custom command logic**: 13 commands with specific Python implementations. Channels have zero custom commands — everything goes through Claude's reasoning, which is slower and less reliable for mechanical operations.
4. **Cost efficiency**: Conversational layer uses Sonnet; execution layer uses Opus only when needed. Channels use whatever model the session is configured for.
5. **Separation of concerns**: Mechanical operations (approve, schedule, rate limit tracking) stay in Python. Only reasoning tasks go to Claude.

**Where Channels could be better**: Simpler setup (no 910-line custom bot), native Claude Code context (full access to project files without spawning processes), no conversation management code, and future Anthropic improvements.

**Decision 27**: Keep our current custom Telegram bot system. Claude Code Channels are designed for a different use case — pushing events into a developer's active session (CI alerts, monitoring). Our system is an autonomous agent pipeline that needs always-on operation, atomic mechanical operations, custom command routing, per-layer model selection, and LaunchAgent scheduling integration. Worth re-evaluating when Channels exit research preview and add custom command hooks or persistent daemon mode.

**Files modified** (1):
- `docs/context.md` — Session 44b entry + Decision 27

### Session 44c — Self-Improving Agents: Standing Directives System (March 21-22, 2026)

**Problem**: War rooms produced insights daily (consensus points, recommendations, performance gates, target rotation rules), but those insights were trapped in per-day JSON files. Only the Strategist read yesterday's `strategy_feedback`. Scout, Outbound, Creator, and Analyst never saw accumulated learnings. Recommendations that required multi-day action (like "expand target pool") were repeated in 4 consecutive war rooms (Mar 18-21) but never executed — because no agent was instructed to read them.

**Root cause**: The PDCA loop had a gap between "Check" (war room produces insights) and "Act" (agents apply insights). The `strategy_feedback_{date}.json` bridge only reached the Strategist, and only for typed recommendations (content_mix, ab_test, posting_time, outbound_target). New directive types (target pool expansion, performance-gated allocation, follow ratio thresholds, budget deployment floors, engagement rotation schedules) had no delivery mechanism to the agents that needed to act on them.

**Solution — Standing Directives System**: A persistent `data/strategy/standing_directives.json` file that accumulates directives across days. War rooms write; all agents read.

**Architecture**:
```
War Room (morning/evening)
  → Discussion produces consensus + recommendations
  → Marc writes standing_directives.json (new Step 8)
  → Next day's agents read directives at startup
  → Agents execute: Scout samples followers, Outbound deploys full budget, Strategist gates grok
  → Results feed back into next war room
  → War room resolves completed directives, adds new ones
  → Cycle continues — agents self-improve
```

**Directive schema**: Each directive has `id`, `created`, `type`, `status` (active/resolved/expired), `priority`, `directive`, `rationale`, `assigned_to` (specific agent), `expires` (optional deadline), `resolved_date`, `resolution`.

**Types**: `content_mix`, `target_pool`, `outbound`, `reply_strategy`, `engagement`, `posting_time`, `ab_test`.

**Lifecycle**:
- **Created** by Marc after war room consensus/recommendation
- **Read** by assigned agent at startup of every daily run
- **Resolved** by Marc when the required action is confirmed complete
- **Expired** when deadline passes — Marc applies fallback action and creates a new directive
- **Escalated** to operator via Telegram when active 3+ days without resolution

**Agent integration**:
- **Scout** (Step 0): Reads directives before data collection. Executes `target_pool` directives via new Follower Sampling Mode — samples followers of Tier 1 accounts, filters by beauty relevance, outputs to `data/scout/follower_targets_*.json`.
- **Strategist** (Step 1.7): Reads directives. Applies `content_mix` gates (performance-based allocation with deadlines), `follow_ratio` threshold (pause/resume follows based on following/followers ratio from `outbound_rules.json`), `target_pool` flags for key_insights.
- **Creator** (Step 0): Reads directives. Applies `posting_time` workflow changes (e.g., prioritize slot 1 for evening prep).
- **Outbound** (Step 0.2.7): Reads directives. Applies `outbound` budget floors (80% minimum deployment), `reply_strategy` Tier 1 prioritization, `engagement` specific targets, rotation schedules. Step 2b: follow ratio check. Step 5: expand to secondary targets when primary pool exhausted.
- **Marc War Room** (Step 8, both morning + evening): Writes new directives from consensus, resolves completed ones, expires overdue ones with fallback actions, escalates stale blockers.

**Additional improvements from morning briefing feedback**:
- `config/outbound_rules.json`: `follow_cooldown_days` 7→5, added `follow_ratio.pause_threshold: 1.2`
- Scout: New Follower Sampling Mode for discovering fresh outbound targets from competitor follower audiences
- Strategist: Performance-gated allocation rule — categories with <3 data points after 7+ days can be cut below core strategy minimum per deadline directives
- Outbound: Budget expansion to secondary targets when primary pool is cooldown-blocked (never leave likes unused)
- Pipeline: Image supply check (Step 8.5) — reports missing images to operator via Telegram after content plan validation

**Decision 28**: Agents must be self-improving systems, not static executors. War room insights must persist across days via standing directives and reach ALL agents — not just the Strategist. The standing directives file is the mechanism for autonomous improvement: war rooms write, agents read, results feed back, and the cycle compounds.

**Files created** (1):
- `data/strategy/standing_directives.json` — 5 initial directives (later updated to 7 by evening war room)

**Files modified** (9):
- `agents/marc.md` — Added "Standing Directives" section
- `agents/marc_warroom.md` — Added Step 8 to both morning + evening war rooms (write/update/resolve/expire directives)
- `agents/scout.md` — Added Follower Sampling Mode + Step 0 reads directives
- `agents/strategist.md` — Added Step 1.7 reads directives, performance-gated allocation, follow ratio gate
- `agents/creator.md` — Added Step 0 reads directives
- `agents/outbound.md` — Step 0.2.7 reads directives, Step 2b follow ratio check, Step 5 budget expansion
- `agents/marc_pipeline.md` — Added Step 8.5 image supply check
- `config/outbound_rules.json` — `follow_cooldown_days` 7→5, added `follow_ratio` section
- `CLAUDE.md` — Added standing directives reference

---

### Session 45 — v4 Architecture Redesign: Python Orchestrator + Strategic Manager (March 23, 2026)

**Problem**: Marc spent 73% of runtime on mechanical coordination (spawning agents, passing files, validating). 4 critical issues documented in `docs/meruru_agent_issues_v1.md`: no autonomy, formulaic prompts, repetitive captions, low-value outbound.

**Root cause**: Marc's role conflated two things — Coordinator (spawn, validate, sequence — mechanical, deterministic) and Project Manager (review quality, evaluate progress, propose improvements — requires judgment).

**Solution**: Separate coordination (Python `orchestrator.py`) from management (Marc as Strategic Manager reviewing at end of every flow).

**Architecture change**: v1-v3 (7 agents, Marc as coordinator, ~12 LLM calls, 73% coordination overhead) → v4 (orchestrator.py + 5 LLM agents, ~5-6 calls, 0% coordination overhead)

**Pipeline flow** (3 LLM calls, zero API):
```
orchestrator.py pipeline
  1. claude -p Strategist (opus)        # LLM 1
  2. validate.py strategist             # Python
  3. claude -p Creator (sonnet)         # LLM 2
  4. validate.py creator                # Python
  5. claude -p Marc Review (opus)       # LLM 3
```

**War Room flow** (2 LLM calls, zero API):
```
orchestrator.py warroom {morning|evening}
  1. claude -p War Room (opus)          # LLM 1
  2. validate.py warroom                # Python
  3. claude -p Marc Review (opus)       # LLM 2
  4. execute_ready_directives()         # Python
```

**Content quality architecture**:
- 3-tier constraint hierarchy: Tier 1 (hard validation — character lock, iPhone, negative prompt), Tier 2 (strong defaults — scene types, outfits), Tier 3 (creative freedom — pose, mood, lighting, color)
- Creative briefs replace prescriptive assignments: Strategist gives mood/intent, Creator has full visual autonomy
- Caption patterns expanded from 6 to 12+, structural dedup enforced
- Scene types expanded from 5 to 10+, each with sub-variants

**New files**: `scripts/orchestrator.py`, `prompts/strategist.md`, `prompts/creator.md`, `prompts/warroom.md`, `prompts/marc_review.md`, `prompts/outbound.md`, `scripts/outbound_context.py`

**Modified files**: `scripts/telegram_bot.py`, `scripts/cron_wrapper.sh`, `config/meruru_concept.md`, `config/image_prompt_guide.md`, `scripts/validate.py`, `agents/marc_conversation.md`, `CLAUDE.md`

**Decisions**:
- D29: Separate coordination (Python) from management (Marc LLM) — Marc spent 73% on mechanical tasks a script does better
- D30: 3-tier constraint hierarchy — 40+ equally-enforced constraints killed creativity; only Tier 1 enforced by validation
- D31: Creative briefs replace prescriptive assignments — Strategist gives mood/intent, Creator has full visual autonomy

**Reference**: Full architecture in `docs/x-agent-redesign-architecture.md`

---

### Session 46 — Content Quality Fixes: Reference Adoption, Expression, Grok Removal (March 24-25, 2026)

**Problem**: Content plan EN 0324 scored 98/100 structurally but failed visual review — scenes unrelated to references (art gallery, greenhouse, arcade vs intimate/body-focused), teeth-showing expression from "bright smile" keyword, "tool: higgsfield" in Copy JSON, grok_interactive still in EN despite testing showing zero impact.

**Root cause (references)**: Creator read composition technique only (pose, angle) but ignored content type. Strategist moment_seeds were independent of reference direction.

**Root cause (expression)**: "bright" keyword overrides "closed-mouth" in image generators. No teeth exclusions in negative prompt.

**Root cause (tool)**: Legacy field in old plans context + HTML report hardcoded it in copy_obj.

**Root cause (grok)**: Previous strategy context had grok; LLM copied it despite updated prompt.

**Solution**:
- orchestrator.py analyzes reference catalog for dominant visual direction, injects summary into Creator prompt
- Creator prompt rewritten: references = content direction, not just composition
- Strategist prompt: moment_seeds must match reference visual direction
- Expression whitelist enforced (6 approved terms only, "bright smile" banned)
- Negative prompt: teeth exclusions added to standard block + all 6 templates
- Tool field: stripped from Creator output + removed from HTML copy_obj
- Grok removed from EN: core_strategy.json, meruru_concept.md, strategist.md, creator.md
- validate.py: hard rejection for EN grok_interactive in strategy

**Verification**: 2 pipeline runs. Run 1: all 3 bugs fixed but grok leaked at 10%. Run 2 (after validation enforcement): all clean — 0 grok, approved expressions, teeth in neg, no tool field, reference-aligned scenes.

**Decision D32**: Content quality requires validation enforcement, not just prompt instructions. When an LLM ignores a prohibition, add a hard check in validate.py.

**Files modified** (10): `prompts/creator.md`, `prompts/strategist.md`, `config/image_prompt_guide.md`, `config/meruru_concept.md`, `data/strategy/core_strategy.json`, `scripts/generate_html_report.py`, `scripts/orchestrator.py`, `scripts/validate.py`, `data/strategy/strategy_current.json`, `data/strategy/strategy_20260324.json`

---

### Session 48 — Purpose-Driven Posts + Visual Diversity Matrix (March 26, 2026)

**Problem**: The content pipeline created 4 daily posts as a "story arc" — imagining moments across Meruru's day. But on X, users see posts individually in their feed, never as a connected set. The narrative arc provided zero value. Additionally, all 4 posts often ended up visually similar (same framing, similar poses, same body emphasis), making the profile grid monotonous.

**Solution**:
- Replaced `moment_seed` with `post_purpose` + `visual_focus` in Strategist creative briefs
- 5 post purposes: `body_showcase`, `face_beauty`, `lifestyle_vibe`, `engagement_hook`, `style_flex` — at least 3 different per day
- `visual_focus` is a lightweight 2-field object: `emphasis` (bust/hips/silhouette/face/back/legs) + `framing` (close-up/medium/full-body)
- Visual diversity matrix validated on Creator OUTPUT: framings≥2, angles≥2, poses≥3, outfit coverage≥2
- Creator declares `visual_diversity` field in output for transparency

**Design principle preserved**: D31 (Strategist sets intent, Creator has autonomy) — Strategist assigns purpose and focal dimension, Creator has full autonomy on scene, outfit, pose, lighting execution.

**Additional improvements** (same session):

1. **Auto reference analysis**: Pipeline Step 0 now runs `analyze_references.py` before Strategist, so new images added to `media/reference/` are automatically picked up. Non-fatal — pipeline continues with existing catalog if analysis fails.

2. **3-day visual dedup**: Orchestrator extracts visual fingerprints (scene, pose, framing, angle, outfit top) from last 3 content plans (~12 posts) and injects as `{{recent_visual_history}}` blocklist into Creator prompt. Rules: no same scene location 3 days, no same pose+framing combo, no same outfit top 2 days, no same angle+framing combo 1 day.

3. **No text/letters in images**: New Tier 1 rule — NEVER include words, letters, numbers, logos, brand names, or typography in image prompts, even if reference images have text. Negative prompt base block updated with `text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text`. Validation enforces both prompt content and negative_prompt inclusion.

**Verification**: Full pipeline run for EN on 2026-03-28 — Strategist produced 4 unique purposes with 4 unique emphases and 3 unique framings. Creator output: 4 posts with personality captions (e.g., "i started walking slower once i realized people were watching" — 61 chars). All validations passed except 1 caption at 20 chars (correctly caught by new 30-char minimum).

**Additional improvements** (Mar 27-28, same session):

4. **Personality captions**: Replaced 3-word fragments ("look back", "say less") with personality sentences showing Meruru's character. EN caption limit changed from <30 to 30-100 chars (aim 40-80). Validation enforces minimum. `meruru_concept.md` rewritten with personality-driven voice and examples.

5. **False "pipeline drought" fix**: Agents claimed "zero posts published for 10 days" while operator was posting 3-5/day via X web UI. Root cause: agents looked at content plan `status: "draft"` instead of analytics `posts_created` data. Fixed: resolved 4 false-premise directives (DIR-025/034/036/037), added global rule forbidding drought claims when analytics shows posting, strengthened "operator posts manually" notes in Strategist + Marc prompts.

6. **Pipeline reliability fixes**:
   - `analyze_references.py` self-terminating `--timeout` (prevents pipeline crash from slow vision analysis)
   - Reference catalog text compacted 302KB → 8KB (prevented Sonnet context overflow causing empty/fragment outputs)
   - `_reconstruct_plan()` — when Creator outputs individual posts instead of wrapper JSON, orchestrator collects all post objects and reconstructs the full plan
   - `run_claude_p()` retry logic (max 2 retries) for transient Bun/AVX crashes
   - `extract_json()` detects post fragments and prefers full plan objects
   - Creator timeout increased to 900s for large prompts

7. **Creator prompt optimization** (Mar 30): Creator prompt grew to 166K chars causing Sonnet to produce only 1 of 4 posts. Root cause: standing_directives (50K — included 34 resolved), strategy (25K — included both EN+JP), image_prompt_guide (32K — all 6 templates). Fix: inject only active creator-relevant directives (50K→10K), only current account's strategy section (25K→14K), cap image guide at 15K (32K→15K). **Result: 166K→98K prompt, all 4 posts generated reliably.** This is structurally bounded — directives will accumulate but only active ones reach Creator.

**Decision D38**: Creator prompt must stay under ~120K chars. Orchestrator filters standing_directives to active+creator-relevant only, extracts single-account strategy, and caps large reference files. Prompt bloat is the #1 cause of incomplete Creator output.

**Decision D34**: Validate visual diversity on Creator OUTPUT (actual image_prompt fields), not on Strategist input. Strategist provides intent; enforcement belongs at the output layer.

**Decision D35**: Auto-analyze reference images at pipeline start so operator can simply drop new images into `media/reference/` daily without running a separate script.

**Decision D36**: Automate image generation via Browser Use CLI controlling the Higgsfield web UI (using existing Pro plan credits), not via the separate Higgsfield Cloud API (which requires additional pay-as-you-go credits).

**Decision D37**: Never claim "pipeline drought" when analytics `posts_created` shows active posting. Content plan `status: "draft"` is expected — operator posts manually via X web UI, not through publisher.py.

**Auto image generation plan** (`docs/plan-auto-image-generation.md`): Browser Use CLI automates the Higgsfield web UI using existing Pro plan ($29/mo). No extra API credits. ~15-17 hours effort. Plan only — not yet implemented.

**Files modified** (9): `prompts/strategist.md`, `prompts/creator.md`, `prompts/marc_review.md`, `scripts/validate.py`, `scripts/orchestrator.py`, `scripts/analyze_references.py`, `config/image_prompt_guide.md`, `config/meruru_concept.md`, `config/global_rules.md`

**Files created** (1): `docs/plan-auto-image-generation.md`

---

### Session 47 — Metrics Visibility Fix: Real Data for Marc + Directive Dedup Enforcement (March 25, 2026)

**Problem**: Marc's pipeline review reported "Day 7 of zero posts published" and "EN followers: 104" — both wrong. The operator had been posting daily (29 posts in 7 days, 499K impressions, +207 follows) and had 214 followers. Marc also generated 47 unnumbered duplicate directives over Mar 23-25 (8 "cleanup" directives that were themselves duplicated).

**Root cause (metrics blindness)**: Orchestrator fed Marc only today's strategy JSON + content plan + standing directives. It never fed him SQLite analytics data (from CSV imports) or archive follower counts. Marc had zero visibility into actual posting activity or real follower counts.

**Root cause (directive duplication)**: `_apply_directive_updates()` blindly appended new directives without checking for DIR-NNN IDs or duplicate detection. War rooms kept generating new directives for the same problems without checking if active directives already existed.

**Solution**:
- Added `get_account_metrics_summary()` to orchestrator.py — queries SQLite for daily analytics (impressions, posts created, follows), follower/following counts from Twitter archive, and top 5 posts by impressions
- Injected real metrics into both Marc Review and Strategist contexts
- `_apply_directive_updates()` now enforces DIR-NNN ID format (regex validation) and rejects duplicate IDs
- Cleaned standing directives: 58 → 15 entries (removed 47 unnumbered duplicates, consolidated unique unnumbered content into DIR-012 through DIR-015)
- Created `scripts/import_twitter_archive.py` for extracting follower/following lists from Twitter data archives
- Imported analytics CSVs (7 daily rows Mar 19-25, 161 per-post rows Mar 12-25) and Twitter archive (214 followers, 64 following)

**Verification**: Evening war room correctly reported "Followers: 214", "Week total: 499K impressions, +195 net followers", "Mar 24 Grok post: 204K impressions, +78 follows". Directive updates added DIR-016 through DIR-020 — all properly numbered, zero duplicates.

**Decision D33**: Agent review context must include real operational data (from analytics imports and archives), not just pipeline-generated plans. Without metrics visibility, agents operate on assumptions that diverge from reality within days.

**Files created** (1): `scripts/import_twitter_archive.py`

**Files modified** (4): `scripts/orchestrator.py` (metrics summary + directive dedup), `prompts/strategist.md` (account_metrics placeholder), `prompts/marc_review.md` (metrics source guidance), `data/strategy/standing_directives.json` (cleanup 58→15)

---

### Session 49 — v5 Architecture Redesign: Meruru as Unified Creative Agent (April 6-7, 2026)

**Problem**: After 6 weeks of v4 operation, the operator assessed the entire system as **non-functional**. The 3-agent split (Strategist → Creator → Marc Review) preserved an architectural flaw: **no single entity "is" Meruru**. Strategist doesn't know what Meruru looks like or how she talks. Creator follows strategy briefs rather than thinking "what would Meruru post?" Marc reviews quality metrics but doesn't embody the character.

**Operator's specific complaints**:
1. **System adds overhead, not value** — operator spends 3hrs/day on content; only 30min is mechanics, the rest is creative decisions the system doesn't help with
2. **Content has no soul** — image prompts repetitive (5 of 6 Slot 1 posts were luxury interiors), captions sound like AI strategy artifacts
3. **Captions are backwards** — system creates captions from strategy+image; operator creates captions from character personality (image is secondary). "gm" is a valid Meruru caption regardless of image — system can't produce this
4. **Reference images template-matched, not adopted** — operator stores 247 references for specific costume/pose adoption, but system only uses generic patterns
5. **Feed balance not addressed** — operator manually checks close-ups/full-body, sexy/cute, poses, colors, clothing, lighting; system offers no help
6. **War rooms are noise** — operator barely reviews them; same 2 action items flagged for 8+ consecutive days with zero execution
7. **X API cost prohibitive** — pay-as-you-go, project not profitable, every API call is direct loss

**Operator's vision**: Meruru should function like a **human influencer** — she knows her personality, looks at her recent feed, and suggests both image direction AND captions as one coherent creative vision. Like a real person who posts what feels right because they know who they are.

**Solution (v5 architecture)**: Collapse Strategist + Creator + Marc Review into a single **Meruru agent** (Opus). She holds personality, visual sense, feed awareness, and voice in one prompt. Strategy/balance constraints are inputs TO her, not drivers above her.

**Architecture changes**:
- **3 LLM calls → 1 LLM call** per pipeline run (5-6/day → 1-2/day total)
- **Strategist REMOVED** — feed balance analysis (Python) replaces content_mix percentages; creative briefs replaced by Meruru's own judgment
- **Creator REPLACED** by Meruru agent (Opus instead of Sonnet)
- **War Room REMOVED** — operator doesn't use it
- **Marc Review (LLM) REMOVED** — replaced with Python-only Tier 1 validation
- **Standing Directives REMOVED** — coordination mechanism for multi-agent system; single agent embeds rules in identity
- **Marc Conversation KEPT** — still the Telegram interface, routes `/create` and `/balance` commands

**New components**:
- `config/meruru_identity.md` — first-person identity document (expanded from `meruru_concept.md`)
- `scripts/feed_balance.py` — Python feed balance + unused reference pool + usage tracking
- `data/content/reference_usage.json` — tracks which reference images have been used (single-use enforcement)
- `prompts/meruru.md` — unified Meruru creative prompt
- `prompts/meruru_balance.md` — balance analysis prompt for `/balance` command

**Key design decisions**:
- **6 candidates per day, operator picks 4** — 3 reference-based + 3 creative posts. Provides variety and natural training signal (which type does operator pick more?). As Meruru's creative quality improves, ratio may shift toward more creative, fewer reference-based.
- **Caption-first / unified creation** — character personality drives both caption AND image direction. "gm" is valid regardless of image. Some posts are caption-driven, others image-driven.
- **Reference adoption: keep costume + pose, change background** — Meruru adopts a specific unused reference's costume and pose, keeps her character lock, and chooses a fresh background based on feed needs. References are single-use (tracked in `reference_usage.json`).
- **Visual style derived from posted images** — operator selected 12 high-performance posts + their actual Higgsfield prompts; analyzed into a first-person "My Visual Style" section saved at `docs/meruru_visual_style.md`. NOT computed from reference catalog (Aesthetic DNA was explicitly rejected as the wrong abstraction).
- **Cron automation preserved** — LaunchAgent runs `/create` daily at 06:00 JST, operator wakes up with content plan ready.

**Feed balance approach**:
- Python `compute_feed_balance()` counts dimensions across last 14 days: framings, poses, scene types, outfit coverage, color palettes, moods, lighting, camera angles
- Returns structured dict + human-readable summary of what's over/under-represented
- Approximate (only counts system-generated plans, not operator's manual posts) — operator can supplement with free-text context via `/create EN "context"`

**Cost & performance**:
| Metric | v4 | v5 |
|---|---|---|
| LLM calls/day | 5-6 | 1-2 |
| Pipeline runtime | 8-15 min | 3-5 min |
| Prompt size | ~100K+ chars | ~13-19K chars |
| Posts per plan | 4 | 6 candidates → operator picks 4 |
| Operator overhead | ~3 hrs/day | Target 2-2.5 hrs/day |

**Phase 0 (✅ Complete Apr 7)**:
- Operator selected 12 high-performance posted images from `media/posted/`
- Operator provided actual Higgsfield prompts (some images differed from content plan JSONs because operator generated independently)
- Analyzed patterns: scenes, lighting, mood, framing, expression, outfits, color palette
- Identified two distinct visual moods with no middle ground:
  1. **Warm intimate glow** — soft ambient lighting, ivory/marble tones, hotel bathroom evenings, bedroom comfort, kitchen mornings
  2. **Hard isolating light** — single dramatic source, deep shadows, plain wall corners, after-hours intensity
- Universal traits: vertical orientation, restrained expression (never teeth), body-conscious styling, dewy skin sheen, high contrast color palette (dark + skin + bold accent, often red), "caught in private moment" energy
- Notably absent: outdoor/public spaces, beach/pool/gym, daylight street, smiling poses
- Result saved at `docs/meruru_visual_style.md` (approved by operator)

**Decisions D39-D44**:
- **D39**: Single creative agent over multi-agent split — Strategist + Creator + Marc Review collapsed into one Meruru agent because no single agent in v4 embodied the character (Session 49)
- **D40**: Caption-first / unified creation — character personality drives both caption and image direction together. Images are context, not the driver. Operator confirmed: "gm" is a valid caption regardless of image (Session 49)
- **D41**: 6 candidates per day with operator picking 4 — provides variety, natural training signal (creative vs reference-based selection rates), and gradual transition path as Meruru's creative independence improves (Session 49)
- **D42**: References for costume/pose adoption only, single-use — operator stores 247 references specifically to adopt their costumes and poses while keeping character lock and changing background. Tracked in `reference_usage.json` to prevent reuse (Session 49)
- **D43**: Visual style derived from posted images, not reference catalog — Aesthetic DNA (computed from reference catalog) was rejected as wrong abstraction. Real visual identity comes from what Meruru has actually posted and what the operator considers high-performance (Session 49)
- **D44**: Remove War Room and Standing Directives — coordination mechanisms for multi-agent system. Single agent doesn't need cross-agent communication or persistent rule CRUD. Persistent rules embedded in identity document (Session 49)

**Architecture document**: `docs/x-agent-redesign-v5-architecture.md` (~600 lines, fully reviewed in 4 rounds of third-party critique)

**Implementation phases**:
- **Phase 0**: ✅ Complete (Apr 7) — Visual style foundation
- **Phase 1**: ✅ Complete (Apr 7) — Foundation
- **Phase 2**: ✅ Complete (Apr 7) — Telegram integration
- **Phase 3**: ✅ Complete (Apr 7) — Cleanup
- **Phase 4**: Ongoing — Polish (observational; iterate on real-world output quality)

**Phase 1 — Foundation (5 files)**:
- `config/meruru_identity.md` — first-person identity expanded from `meruru_concept.md`, integrates `docs/meruru_visual_style.md` as Section 4
- `scripts/feed_balance.py` — pure-Python module with `compute_feed_balance()`, `get_unused_references()`, `mark_references_used()` + CLI
- `data/content/reference_usage.json` — initialized empty `{"EN": [], "JP": []}`
- `prompts/meruru.md` — unified Meruru creative prompt (~5K template, ~30K when expanded with all placeholders)
- `scripts/orchestrator.py` — added `run_create()`, `_format_unused_references_for_prompt()`, `_build_tier1_constraints()`, `_build_image_prompt_format()`, `create` CLI subcommand

**Phase 1 first run results** (`/create EN`):
- Runtime 312s (~5 min), 6 candidates generated (3 ref-based + 3 creative)
- Captions character-driven and unique: `"stood here too long pretending this wasn't on purpose"`, `"shh i'm not telling you what i'm thinking"`, `"made coffee i'm not even gonna drink"`, etc.
- 6 unique scenes across candidates (powder room, charcoal wall, living room, kitchen, hallway, bedroom)
- Reference usage tracking working (3 references marked used)
- Issue: prompt size 37K (vs 13-19K target) — reference descriptions were too verbose
- Fix: trimmed `_format_unused_references_for_prompt()` to one_line + outfit + pose only, dropping scene/lighting/mood (per design intent — references are for COSTUME + POSE adoption only)
- Re-run: prompt down to 30,919 chars; produced "gm from the only person awake in this room" — exactly the character-first "gm" caption the operator described

**Phase 2 — Telegram integration (4 files)**:
- `prompts/meruru_balance.md` — lightweight balance-check prompt (output is plain-text Telegram message, not JSON)
- `scripts/orchestrator.py` — added `run_balance()` + `balance` CLI subcommand
- `scripts/telegram_bot.py` — added `cmd_create()` and `cmd_balance()` handlers, registered, updated `/help` text grouping v5 commands as primary and v4 as legacy
- `agents/marc_conversation.md` — fully rewritten for v5: knows about `/create` and `/balance`, marks v4 commands as legacy fallback

**Phase 2 verification — `/balance` test**:
- Runtime 11s (target ≤2 min ✅), prompt size 12,246 chars
- Meruru's actual recommendation correctly identified gaps: "72% of my lighting is one mood. zero bright-airy, zero hard shadow drama, and i haven't been in a car or a cafe in two weeks"
- Post ideas with character-first captions: "skipped class for an oat latte. worth it.", "parked for 20 mins just to finish this song", "the lighting in here is doing half the work"

**Phase 2 bonus fix**: `send_telegram()` had a long-standing v4 bug — it built shell commands via f-string, breaking on apostrophes in messages. Fixed by switching to `subprocess.run` with argument list (no shell). This affects ALL callers of send_telegram, not just v5.

**Phase 3 — Cleanup (7 changes)**:
- Archived 5 v4 prompts to `prompts/archive/`: `strategist.md`, `creator.md`, `marc_review.md`, `warroom.md`, `outbound.md`
- `scripts/validate.py` — removed `reply_templates` requirement (v4 leftover), relaxed outfit dedup to a warning (since 6-candidate pool allows some overlap when operator picks 4)
- `scripts/orchestrator.py` — removed `run_warroom()` entirely; marked `run_pipeline()` as legacy fallback; updated CLI choices `{create, balance, pipeline}`; updated module docstring; added `build_prompt()` archive-fallback so legacy v4 templates load from `prompts/archive/`
- `scripts/cron_wrapper.sh` — added `create` and `balance` task handlers; war room handlers removed with explanatory error
- LaunchAgents: created `~/Library/LaunchAgents/com.xagents.create.plist` (06:00 JST daily, loaded), unloaded v4 plists (`com.xagents.morning-warroom`, `evening-warroom`, `pipeline`, `outbound`) but preserved .plist files for fallback re-enabling
- `scripts/generate_html_report.py` — `generate_content_plan()` now groups posts by `type` (📎 reference-based / ✨ creative), shows `reference_filename`, drops `reply_templates` section. `render_post_card()` adds type badge and reference filename row. Falls back gracefully for legacy v4 plans without `type` field.
- `CLAUDE.md` — fully rewritten for v5 architecture, removed Strategist/Creator/War Room references, added Meruru / feed_balance / 6-candidate documentation
- `validate.py` re-test: **PASS — All 14 checks passed** on the v5 content plan

**Telegram bot restarted Apr 7** to pick up new `/create` and `/balance` commands. PID 45356, "Application started" confirmed.

**Files modified/created across all phases (~15)**:
- Created: `config/meruru_identity.md`, `scripts/feed_balance.py`, `data/content/reference_usage.json`, `prompts/meruru.md`, `prompts/meruru_balance.md`, `~/Library/LaunchAgents/com.xagents.create.plist`, `docs/meruru_visual_style.md`, `docs/x-agent-redesign-v5-architecture.md`
- Modified: `scripts/orchestrator.py`, `scripts/telegram_bot.py`, `scripts/validate.py`, `scripts/generate_html_report.py`, `scripts/cron_wrapper.sh`, `agents/marc_conversation.md`, `CLAUDE.md`, `docs/context.md`
- Archived: `prompts/strategist.md`, `prompts/creator.md`, `prompts/marc_review.md`, `prompts/warroom.md`, `prompts/outbound.md` (moved to `prompts/archive/`)

---

### Session 50 — All Daily Automation Halted (May 20, 2026)

**Context**: Operator decided to stop every daily auto-task. The audit revealed that even though Session 49's notes said v4 LaunchAgents were unloaded, `launchctl list` showed them still loaded and erroring out daily (exit status 1) — only `com.xagents.create` was healthy.

**Inventory before shutdown**:

| Loaded LaunchAgent | Schedule (JST) | Wrapper task | State |
|---|---|---|---|
| `com.xagents.create` | daily 06:00 | `cron_wrapper.sh create` | exit 0 — was the only working job (v5 Meruru) |
| `com.xagents.pipeline` | daily 06:00 | `cron_wrapper.sh pipeline` | exit 1 — legacy v4 |
| `com.xagents.morning-warroom` | daily 05:30 | `cron_wrapper.sh morning_warroom` | exit 1 — removed in v5, wrapper errors out |
| `com.xagents.evening-warroom` | daily 22:00 | `cron_wrapper.sh evening_warroom` | exit 1 — removed in v5, wrapper errors out |
| `com.xagents.outbound` | daily 14:00 | `cron_wrapper.sh outbound` | exit 1 — legacy v4, no `outbound` case in wrapper |
| `com.xagents.publish-slot.20260322-en-02` | one-shot, Mar 23 02:30 | `publisher.py post --slot 2` | expired (date in past) |
| `com.xagents.publish-slot.20260322-en-03` | one-shot, Mar 23 06:00 | `publisher.py post --slot 3` | expired |
| `com.xagents.publish-slot.20260322-en-04` | one-shot, Mar 23 08:30 | `publisher.py post --slot 4` | expired |

No cron entries. No background daemons (telegram_bot.py not running).

**Action taken**:
- `launchctl unload` on all 5 daily plists (`create`, `pipeline`, `morning-warroom`, `evening-warroom`, `outbound`)
- `.plist` files preserved in `~/Library/LaunchAgents/` — can be re-enabled later with `launchctl load`
- 3 expired `publish-slot.20260322-*` plists left in place (already past their `StartCalendarInterval` date, will not fire)

**Effect on Telegram messages**: The daily content plan Telegram message was the end of the `create` task (orchestrator.py sends the HTML report via `send_telegram` after generation). With `create` unloaded, **Marc sends no scheduled daily messages**. Telegram bot remains available for `/create`, `/balance`, and free-form conversation if the operator manually starts the daemon — those are operator-triggered, not scheduled.

**Discrepancy resolved**: CLAUDE.md and Session 49 notes claimed the v4 plists were unloaded. They were not (or were reloaded since). After Session 50, all 5 are confirmed unloaded.

**To resume any single task**:
```
launchctl load ~/Library/LaunchAgents/com.xagents.create.plist
```

**To clean up the 3 expired publish-slot plists** (optional, not done this session):
```
rm ~/Library/LaunchAgents/com.xagents.publish-slot.20260322-en-*.plist
```

---

### Session 51 — Daily Automation Actually Halted (June 8, 2026)

**Context**: Operator noticed daily Telegram messages from Marc were still arriving despite Session 50 documenting that all daily LaunchAgents had been halted. Investigation showed Session 50's halt was not effective in practice.

**Root cause**: `launchctl unload` only removes a service from the *current* launchd session. macOS automatically (re-)loads every `.plist` it finds in `~/Library/LaunchAgents/` at the next user login. Session 50 deliberately left the `.plist` files in that directory "for future re-enable" — which meant the next reboot/login silently restored all 5 daily jobs. From that point on (~May 20 onward) they kept firing every day.

**Evidence at investigation time (today, June 8)**:

| Job | Last fire | Source |
|---|---|---|
| `com.xagents.create` | 06:02 → 08:15 (sent Telegram message + HTML doc) | `logs/cron_create_20260608.log` Step 10: `Sending Telegram document` |
| `com.xagents.pipeline` | 10:12 | `logs/cron_pipeline_20260608.log` |
| `com.xagents.morning-warroom` | 05:46 | `logs/cron_morning_warroom_20260608.log` |
| `com.xagents.evening-warroom` | yesterday 22:00 | `logs/cron_evening_warroom_20260607.log` |
| `com.xagents.outbound` | yesterday 14:00 | `logs/cron_outbound_20260607.log` |

`launchctl list | grep xagent` confirmed all 5 daily agents loaded alongside the 3 expired publish-slot agents.

**Action taken** ("Option B" — move plists out of auto-load path so re-load is structurally impossible):
```
mkdir -p ~/Library/LaunchAgents/xagents-disabled
mv ~/Library/LaunchAgents/com.xagents.{create,pipeline,morning-warroom,evening-warroom,outbound}.plist \
   ~/Library/LaunchAgents/xagents-disabled/
for j in create pipeline morning-warroom evening-warroom outbound; do
  launchctl bootout gui/$(id -u)/com.xagents.$j
done
```

**Verification after halt**:
- `launchctl list | grep xagent` → only the 3 expired `publish-slot.20260322-en-*` remain (one-shot dates in March 2026, will never fire)
- `~/Library/LaunchAgents/` → no daily plists (moved to `xagents-disabled/`)
- No running `orchestrator.py` / `cron_wrapper.sh` / `telegram_bot.py` processes
- No lockfiles, no crontab entries

**Why Option B over `launchctl disable`**: Option A (`disable` + `bootout`) is also persistent, but the disabled state lives inside launchctl's database — invisible if you only look at the LaunchAgents folder. Session 50 was already burned by an invisible "the agents are off, trust me" state. Moving the files makes the off-state self-evident — `ls ~/Library/LaunchAgents/` shows no daily jobs.

**What's still off-by-default (not changed this session)**:
- `telegram_bot.py` — the conversational Marc layer is not running. The daily Telegram messages were sent by `orchestrator.py → telegram_send.py` directly, not via the bot. Halting the LaunchAgents alone is sufficient to stop scheduled messages regardless of bot state.

**To resume any single task** (now requires both move-back and bootstrap):
```
mv ~/Library/LaunchAgents/xagents-disabled/com.xagents.create.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.xagents.create.plist
```

---

## 4. Decision Summary

### Framework-Level Decisions (Apply to All Future Projects)

| # | Decision | Rationale |
|---|---|---|
| D1 | Claude Code + launchd as the agent execution framework | Handles 80% natively; launchd fills scheduling gap (replaced cron in Session 39b — cron cannot access macOS Keychain) |
| D2 | VPS for always-on compute (Phase 6 deployment) | Cheaper than hardware ($12/mo Vultr Tokyo); only needed for autonomous operation |
| D3 | Telegram Bot for human-agent communication | Simple (~50 lines Python), free, feature-rich; universal across any project |
| D8 | CLAUDE.md for persistent behavioral memory | Native auto-loading; rules persist across sessions; no custom code needed |
| D16 | ~~Agent Teams for pipeline coordination~~ **Superseded by D29** | Originally Agent Teams for pipeline, subagents for war rooms (Session 36). Replaced by Python orchestrator + `claude -p` in v4 (Session 45) |

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
| D17 | Outbound limits match global rules ceiling | Conservative margins below global max leave growth value unused with no safety benefit |
| D18 | Morning war room output feeds into same-day pipeline | Any PDCA discussion that doesn't reach the agents it influences is wasted compute |
| D26 | Approval and scheduling are atomic — always approve then schedule_slots.py | Marc bypassing schedule_slots.py caused immediate publish instead of slot-timed publish (Session 44) |
| D27 | Keep custom Telegram bot over Claude Code Channels | Channels lack always-on daemon, atomic operations, custom commands, per-layer model selection (Session 44b) |
| D28 | Standing directives for self-improving agents | War room insights must persist across days and reach all agents — not just the Strategist. Directives accumulate, expire, and escalate autonomously (Session 44c) |
| D29 | Separate coordination (Python) from management (Marc LLM) | Marc spent 73% on mechanical tasks a script does better — orchestrator.py handles sequencing, Marc focuses on strategic review (Session 45) |
| D30 | 3-tier constraint hierarchy | 40+ equally-enforced constraints killed creativity; only Tier 1 enforced by validation, Tier 2 as defaults, Tier 3 creative freedom (Session 45) |
| D31 | Creative briefs replace prescriptive assignments | Strategist gives mood/intent, Creator has full visual autonomy — prescriptive scene/outfit/pose assignments killed variety (Session 45) |
| D32 | Validation enforcement over prompt-only instructions | LLMs ignore prohibitions ~10% of the time; validate.py must enforce critical rules with hard rejection (Session 46) |
| D33 | Agent review context must include real operational data | Without metrics from CSV imports and archives, agents operate on assumptions that diverge from reality within days — Marc thought 0 posts published when 29 were (Session 47) |
| D34 | Validate visual diversity on Creator output, not Strategist input | Strategist provides intent (purpose + focus); enforcement belongs at the output layer where actual image_prompt fields can be checked (Session 48) |
| D35 | Auto-analyze reference images at pipeline start | Operator drops images into `media/reference/` daily — pipeline picks them up automatically (Session 48) |
| D36 | Automate image gen via Browser Use on web UI, not Higgsfield API | Higgsfield Cloud API requires separate pay-as-you-go credits ($23-68/mo extra). Browser Use controls the web UI using existing Pro plan — no extra cost (Session 48) |
| D37 | Never claim "pipeline drought" when analytics shows posting | Content plan `status: "draft"` is expected — operator posts manually. Trust `posts_created` from analytics over content plan statuses (Session 48) |
| D38 | Creator prompt must stay under ~120K chars | Orchestrator filters directives (active only), extracts single-account strategy, caps large files. Prompt bloat is #1 cause of incomplete Creator output — 166K produced 1/4 posts, 98K produces 4/4 (Session 48) |

---

## 5. The Framework Architecture (Reusable Pattern)

This is the general-purpose architecture that emerged from the research and is being validated through the X Beauty demo. **Updated in Session 45** to replace Agent Teams with Python orchestrator + LLM agents.

```
┌──────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENT FRAMEWORK (v4)                 │
│                                                                   │
│  ┌──────────┐                                                     │
│  │ launchd  │──┐                                                  │
│  └──────────┘  │                                                  │
│                │     ┌─────────────────────────────────────────┐  │
│  ┌──────────┐  ├────▶│  CONVERSATIONAL LAYER                   │  │
│  │ Telegram │──┘     │  Lightweight `claude -p` (Marc)          │  │
│  │   Bot    │◀───────│  - Receives messages / launchd triggers  │  │
│  │ (daemon) │        │  - Reasons about tasks                   │  │
│  └────┬─────┘        │  - Asks clarifying questions             │  │
│       │              │  - Routes commands to orchestrator        │  │
│       │              └──────────────┬──────────────────────────┘  │
│       │                             │ /pipeline, /warroom, etc.   │
│       │                             ▼                              │
│       │              ┌─────────────────────────────────────────┐  │
│       │              │  ORCHESTRATOR (Python, zero LLM cost)    │  │
│       │              │  orchestrator.py                          │  │
│       │              │  - Sequences pipeline steps               │  │
│       │              │  - Invokes `claude -p` for LLM reasoning  │  │
│       │              │  - Validates outputs (validate.py)        │  │
│       │              │  - Executes standing directives           │  │
│       │              └────────┬────────────────────────────────┘  │
│       │                       │                                    │
│       │        ┌──────────────┼──────────────┐                    │
│       │        ▼              ▼              ▼                     │
│       │   ┌─────────┐   ┌─────────┐   ┌─────────┐               │
│       │   │claude -p │   │claude -p │   │claude -p │              │
│  [HUMAN]  │Strategist│   │ Creator │   │Marc Revw │              │
│       │   │ (Opus)  │   │(Sonnet) │   │ (Opus)  │               │
│       │   └────┬────┘   └────┬────┘   └────┬────┘               │
│       │        │              │              │                     │
│       │        ▼              ▼              ▼                     │
│       │   ┌─────────────────────────────────────────────────┐     │
│       │   │              Shared State Layer                   │    │
│       │   │  CLAUDE.md (behavioral rules, auto-loaded)       │    │
│       │   │  JSON files (agent-to-agent data exchange)       │    │
│       │   │  SQLite (structured metrics & history)           │    │
│       │   │  Standing directives (cross-day persistence)     │    │
│       │   └─────────────────────────────────────────────────┘     │
│       │                                                           │
│       │   Tech stack: Claude Code CLI + Python orchestrator +     │
│       │               launchd + Telegram Bot + CLAUDE.md +        │
│       │               SQLite + JSON                               │
│       │                                                           │
└───────┴───────────────────────────────────────────────────────────┘
```

**Key principles** (from the original article, validated and refined):

1. **Single-responsibility agents** — each agent does one thing well
2. **Separate coordination from management** — Python orchestrator handles mechanical sequencing (zero LLM cost); Marc as Strategic Manager handles judgment calls (Session 45, D29)
3. **launchd-triggered batch pipelines** — overnight execution, no always-listening daemon needed (replaced cron in Session 39b)
4. **Persistent memory via CLAUDE.md** — behavioral rules auto-loaded; learned knowledge persists
5. **Filesystem-based shared state** — agents communicate via JSON/SQLite, not in-memory
6. **Human-in-the-loop at decision points** — approval gates before irreversible actions
7. **Error handling with classification** — auto-retry vs. escalate vs. halt based on error type
8. **Telegram as the single communication channel** — reports, alerts, commands, all unified
9. **Hybrid agents ("Claude Brain, Python Hands")** — Python handles deterministic execution (API calls, rate limits, data storage); Claude handles intelligence (analysis, filtering, composition). Failures degrade gracefully to Python-only behavior.
10. **Validation enforcement** — critical rules enforced by Python validation, not just prompt instructions. LLMs ignore prohibitions ~10% of the time; validate.py catches violations (Session 46, D32).

---

## 6. Demo Project: X Beauty System

### 6.1 Agent Architecture (v4 — Session 45)

```
Human (Shimpei)
└── Telegram (unified communication)
    └── Conversational Marc (claude -p, chat + command routing)
         ↓ (commands route to)
    orchestrator.py (Python, zero LLM cost)
    ├── Strategist ──── Growth strategy from metrics + directives          [claude -p Opus]
    ├── validate.py ─── Output validation (Tier 1 enforcement)            [Python]
    ├── Creator ─────── Content plans with creative freedom                [claude -p Sonnet]
    ├── validate.py ─── Output validation (Tier 1 enforcement)            [Python]
    ├── Marc Review ─── Strategic review + directive updates               [claude -p Opus]
    ├── War Room ────── Multi-perspective analysis (morning/evening)       [claude -p Opus]
    └── Outbound ────── Engagement planning + reply drafting               [claude -p Sonnet]

Supporting scripts (no LLM):
    ├── scout.py ────── Data collection only (Python)
    ├── publisher.py ── Posting approved content to X (Python)
    ├── analyst.py ──── Metrics collection + summary (Python)
    └── outbound_context.py ── Pre-computed engagement context (Python)
```

#### 6.1.1 v4 Architecture Pattern (Session 45)

The v4 architecture separates coordination from management. Python `orchestrator.py` handles all mechanical coordination (sequencing, file passing, validation) at zero LLM cost. LLM agents are invoked via `claude -p` with focused prompts from `prompts/`. Marc's role changed from Coordinator to Strategic Manager — he reviews outputs at the end of every flow, evaluates 10K follower goal progress, and updates standing directives. Content quality uses a 3-tier constraint hierarchy: Tier 1 (hard validation by validate.py), Tier 2 (strong defaults in prompts), Tier 3 (full creative freedom for the Creator LLM).

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
│   ├── global_rules.md                     ← BEHAVIORAL RULES
│   └── outbound_rules.json                ← OUTBOUND SAFETY PARAMETERS (Session 30: margins, cooldowns, rotation)
│
├── agents/                                 ← AGENT SKILL FILES
│   ├── marc.md                            ← COO / Team Leader (Session 24: Agent Teams)
│   ├── marc_conversation.md               ← Conversational Marc system prompt (Session 24: identity, team reference, decision rules)
│   ├── marc_pipeline.md                   ← Goal-oriented Pipeline Playbook (Session 24: teammate spawning)
│   ├── marc_publishing.md                 ← Goal-oriented Publishing Playbook (Session 24: teammate spawning)
│   ├── marc_schemas.md                    ← Schemas & report formats (loaded on demand)
│   ├── scout.md                           ← Competitor Research (Phase 5: Daily Intelligence Mode, Session 24: Teammate Mode added)
│   ├── strategist.md                      ← Growth Strategy (Session 24: Teammate Mode added)
│   ├── creator.md                         ← Content Planning & Image Prompts (Phase 2, Session 24: Teammate Mode added)
│   ├── publisher.md                       ← X API Posting (Session 30: Smart Outbound Mode moved to outbound.md)
│   ├── outbound.md                        ← Community Engagement & Growth (Session 30: extracted from publisher.md with safety reasoning)
│   └── analyst.md                         ← Metrics Collection & Data Storage (Phase 5: Intelligence Mode, Session 24: Teammate Mode added)
│
├── scripts/                                ← PIPELINE & UTILITY SCRIPTS
│   ├── run_pipeline.sh                    ← Pipeline entry point (Agent Teams enabled, Session 24: Team Leader prompt)
│   ├── run_task.sh                        ← Operator task entry point (Agent Teams enabled, Session 24: Team Leader prompt)
│   ├── validate.py                        ← Deterministic validation (Phase 5: analyst_report, scout_analysis, outbound_plan)
│   ├── x_api.py                           ← X API v2 wrapper library (read + write + batch)
│   ├── db_manager.py                      ← SQLite database layer (WAL mode, insert/query)
│   ├── scout.py                           ← Scout agent script (Phase 5: --raw/--compact + pre-analysis)
│   ├── publisher.py                       ← Publisher agent script (Phase 5: smart-outbound subcommand)
│   ├── publisher_outbound_data.py         ← Outbound data fetcher for Claude analysis (Phase 5)
│   ├── outbound_history.py               ← Outbound history query tool (Session 30: SQLite + JSON, 3 CLI modes)
│   ├── analyst.py                         ← Analyst agent script (collect + summary + import) (Phase 4)
│   ├── fetch_url.py                       ← URL fetcher — extracts readable text from web pages (Session 28)
│   ├── telegram_send.py                   ← Telegram send helper (Phase 2)
│   ├── telegram_bot.py                    ← Telegram bot daemon (conversational Marc + Agent Teams execution + commands + URL enrichment + image vision) (Session 24, 28, 32)
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

**Latest**: Session 48 — Purpose-Driven Posts + Personality Captions + Pipeline Fixes (March 26-30, 2026). Major content quality overhaul: purpose-driven posts, visual diversity matrix, personality captions (30-100 chars), 3-day visual dedup, no-text-in-images. Pipeline reliability: self-terminating ref analysis, compact reference text (302KB→8KB), plan reconstruction, claude -p retry logic. Fixed false "pipeline drought" caused by agents reading content plan statuses instead of analytics data. Creator prompt optimized from 166K→98K to prevent incomplete output (50K resolved directives removed, single-account strategy, capped image guide).

Session 48 files modified (9 files):
- `prompts/strategist.md` — Creative briefs rewrite: `moment_seed` → `post_purpose` + `visual_focus`. Diversity rules. Updated schema + validation checklist. Strengthened "operator posts manually" note.
- `prompts/creator.md` — Purpose-first process. Visual diversity check. `{{recent_visual_history}}` 3-day dedup. No-text-in-images Tier 1 rule. Personality captions (30-100 chars, aim 40-80). Emphasis→image and purpose→caption mapping tables.
- `prompts/marc_review.md` — EN caption limit updated to 30-100 (minimum, not maximum).
- `scripts/validate.py` — Visual diversity matrix, strategist brief checks, text-in-image checks, EN caption length 30-100 enforcement.
- `scripts/orchestrator.py` — Step 0 auto ref analysis with `--timeout`. `_extract_recent_visual_history()`. `_reconstruct_plan()` for fragmented Creator output. `run_claude_p()` retry logic for Bun crashes. Compact reference text (20 most recent, 302KB→8KB). Creator timeout 900s. Creator prompt optimization: active-only directives (50K→10K), single-account strategy (25K→14K), capped image guide (32K→15K). Total: 166K→98K.
- `scripts/analyze_references.py` — Self-terminating `--timeout` flag. Saves partial progress before budget expires.
- `config/image_prompt_guide.md` — Negative prompt text/letter/typography exclusions in base + combined + all 6 templates.
- `config/meruru_concept.md` — Caption voice rewrite: personality sentences replacing fragments. New examples showing mood, humor, confessions.
- `config/global_rules.md` — New rule: never claim drought when analytics shows `posts_created > 0`.

Session 47 files created (1 file):
- `scripts/import_twitter_archive.py` — Extract follower/following from Twitter data archive

Session 47 files modified (4 files):
- `scripts/orchestrator.py` — Added `get_account_metrics_summary()` (SQLite query + archive data), injected into Strategist + Marc Review contexts. `_apply_directive_updates()` enforces DIR-NNN ID format, rejects duplicates.
- `prompts/strategist.md` — Added `{{account_metrics_EN}}` placeholder for real analytics
- `prompts/marc_review.md` — Updated to reference `account_metrics_*` for real follower/posting data
- `data/strategy/standing_directives.json` — Cleaned 58→15 entries (47 unnumbered duplicates removed)

Session 46 files modified (10 files):
- `prompts/creator.md` — References = content direction, expression whitelist (further updated Session 48: purpose-first process)
- `prompts/strategist.md` — moment_seeds must match reference visual direction (further updated Session 48: moment_seed → post_purpose + visual_focus)
- `config/image_prompt_guide.md` — Expression whitelist, teeth exclusions in negative prompt + all 6 templates (further updated Session 48: text/letter exclusions)
- `config/meruru_concept.md` — Grok removed from EN engagement tools
- `data/strategy/core_strategy.json` — Grok removed from EN engagement_tools
- `scripts/generate_html_report.py` — Tool field removed from HTML copy_obj
- `scripts/orchestrator.py` — Reference catalog analysis + visual direction injection
- `scripts/validate.py` — Hard rejection for EN grok_interactive in strategy
- `data/strategy/strategy_current.json` — Grok removed
- `data/strategy/strategy_20260324.json` — Clean strategy after fixes

Session 45 files created (7 files):
- `scripts/orchestrator.py` — Python coordinator (~430 lines)
- `scripts/outbound_context.py` — Pre-computed outbound context (~220 lines)
- `prompts/strategist.md` — Merged Scout analysis + Strategy prompt
- `prompts/creator.md` — Simplified Creator with creative freedom
- `prompts/warroom.md` — Single-call war room (3 perspectives)
- `prompts/marc_review.md` — Marc's strategic review template
- `prompts/outbound.md` — Focused outbound planning

Session 45 files modified (7 files):
- `scripts/telegram_bot.py` — Commands route to orchestrator, directive scheduler
- `scripts/cron_wrapper.sh` — All tasks call orchestrator.py
- `config/meruru_concept.md` — Caption patterns 6→12+
- `config/image_prompt_guide.md` — 3-tier constraint hierarchy, +5 scene types
- `scripts/validate.py` — Creator validation enforces Tier 1 only; added warroom mode
- `agents/marc_conversation.md` — Slimmed to conversational rules, references orchestrator
- `CLAUDE.md` — Updated architecture to v4

Session 36 files modified (4 files):
- `agents/marc_warroom.md` — Rewrite: Agent Teams → subagents (blocking Agent tool calls)
- `scripts/run_warroom.sh` — Removed Agent Teams env var, updated prompts for subagent pattern
- `config/outbound_rules.json` — `max_replies_per_day: 0` for both EN and JP
- `config/global_rules.md` — Updated outbound limits to reflect 0 replies

Session 35 files modified (5 files):
- `agents/marc_warroom.md` — Full rewrite: solo-Marc → 3-round discussion protocol
- `agents/analyst.md` — Added War Room Discussion Mode (DATA ADVOCATE role)
- `agents/strategist.md` — Added War Room Discussion Mode (STRATEGY ADVOCATE role)
- `scripts/run_warroom.sh` — Updated prompts to require multi-agent discussion
- `scripts/validate.py` — Added soft-check discussion validation to morning_briefing and strategy_feedback

Session 34 files created (2 files):
- `agents/marc_warroom.md` — War room playbook (morning briefing + evening metrics/feedback)
- `scripts/run_warroom.sh` — War room entry point (`morning` or `evening` arg)

Session 34 files modified (11 files):
- `agents/strategist.md` — Step 1.5: read strategy_feedback with confidence-based rules
- `agents/marc.md` — War Rooms workflow reference + correct report types for content plans
- `agents/marc_publishing.md` — Steps 5-8 moved to evening war room
- `agents/marc_conversation.md` — Updated delivery format with correct report types
- `agents/creator.md` — Added meruru_concept.md as required input (character lock, voice, NG list)
- `scripts/cron_wrapper.sh` — Added morning_warroom, evening_warroom cases
- `scripts/install_cron.sh` — 4-job schedule (morning 05:30, pipeline 06:00, outbound 14:00, evening 22:00)
- `scripts/validate.py` — Added strategy_feedback (8 checks) and morning_briefing (5 checks) validators
- `scripts/run_metrics.sh` — Deprecation header (kept for manual re-runs)
- `scripts/telegram_bot.py` — Performance fix: cwd=$HOME, --allowedTools "", history truncation

Session 33 files created (2 files):
- `data/outbound/outbound_plan_20260310_EN.json` — Outbound plan with API-verified follow status
- `data/outbound/outbound_log_20260310.json` — Execution log with `failed_replies` for human escalation

Session 32 files modified (4 files):
- `config/accounts.json` — EN and EN-subaccount tokens updated to @meruru_tcbn's OAuth tokens
- `scripts/publisher.py` — Smart-outbound tracks `failed_replies` in outbound log for human escalation
- `agents/outbound.md` — Added Step 7 (failed action escalation to Marc)
- `agents/marc_publishing.md` — Check outbound log for `failed_replies`, send manual reply instructions via Telegram

Session 32 rules added (1 file):
- `config/global_rules.md` — Agent escalation rule: when API fails, find alternative path instead of stopping

Session 31 files created/modified (8 files):
- `config/account_status.json` — **New** Account active/suspended status (EN active, JP suspended)
- `config/accounts.json` — Added `"EN"` key pointing to @meruru_tcbn sub-account, renamed `EN-shadowbanne` → `EN-shadowbanned`
- `scripts/x_api.py` — Added `get_active_accounts()` helper (reads account_status.json, fallback to ["EN", "JP"])
- `scripts/telegram_bot.py` — Imported `get_active_accounts()`, replaced hardcoded `["EN", "JP"]` in cmd_approve, cmd_details, _show_metrics_summary
- `agents/marc_pipeline.md` — Added Step 0 (check account status), gated Steps 6-9 on active accounts only
- `agents/marc_publishing.md` — Added account status check in prerequisites, gated Steps 1-6 on active accounts
- `agents/marc_conversation.md` — Added Account Status section, updated Known Limitations with shadowban/JP status
- `CLAUDE.md` — Added account status tracking to Project Context

Session 30 files created/modified (10 files):
- `agents/outbound.md` — **New** Outbound agent definition (6-step workflow: read → safety reasoning → fetch → plan → write → execute)
- `scripts/outbound_history.py` — **New** History query tool (SQLite + JSON, 3 CLI modes: --days, --target, --check-tweets)
- `config/outbound_rules.json` — **New** Safety parameters (per-account margins, cooldown periods, rotation rules)
- `agents/publisher.md` — Removed Smart Outbound Mode, added execution-only note
- `agents/strategist.md` — Added Target Rotation Rules (full pool, recent log check, market match, size mix)
- `agents/marc_publishing.md` — Step 3 spawns Outbound agent instead of Publisher
- `agents/marc.md` — Updated team table, flow, logging, dependencies
- `agents/marc_conversation.md` — Updated team table, task types
- `agents/creator.md` — Reply templates reference Outbound agent
- `CLAUDE.md` — Added Outbound to agent definitions and tool assignments

Session 29 files created/modified (7 files):
- `scripts/image_analyzer.py` — **New** Image analysis via Anthropic Vision API (--top N, --dry-run)
- `agents/creator.md` — Added image references input + "Using Image References" section (2 modes)
- `agents/marc_pipeline.md` — Added Step 3.5 (Image Analysis, optional), updated Creator spawn prompts
- `scripts/validate.py` — Added `image_references` validation mode (6 checks)
- `scripts/generate_html_report.py` — Image prompt section now renders all structured Higgsfield fields (meta, subject, outfit, pose, scene, camera, lighting, mood) as syntax-highlighted JSON with "Copy JSON" button for one-click copy of entire prompt
- `data/content/content_plan_20260308_EN.json` — Rewrote image prompts from old midjourney format to full Higgsfield schema (150+ word prompts, structured fields, standard negative prompts, fixed character profiles with curvaceous body type)
- `data/content/content_plan_20260308_JP.json` — Rewrote image prompts from old stable_diffusion format to full Higgsfield schema (150+ word prompts, structured fields, locked JP character profile with specific body measurements)

Session 28 files created/modified (3 files):
- `scripts/fetch_url.py` — **New** URL fetcher (requests + stdlib html.parser, CLI-compatible)
- `scripts/telegram_bot.py` — URL detection + async content fetching in `handle_message`
- `agents/marc_conversation.md` — Added "URL Reading" section

Session 27 files removed (11 files):
- `data/*20260306*` (9 files) — All Mar 6 pipeline test outputs (scout, strategy, content plans, HTML reports, pipeline state, image analysis)
- `data/strategy/strategy_current.json` — Copy of Mar 6 strategy (regenerates on next pipeline run)

Session 26 files created/modified (3 files):
- `scripts/generate_html_report.py` — **New** HTML report generator (3 report types, dark theme, responsive)
- `agents/marc_pipeline.md` — Step 9: added HTML generation + `--document` send for content preview
- `agents/marc_publishing.md` — Steps 4 and 8: added HTML generation + `--document` send for publish/daily reports

Session 25 files modified (6 files):
- `scripts/telegram_bot.py` — Added non-interactive override to `_execute_task()` prompt
- `CLAUDE.md` — Scoped preferences: interactive (ask user) vs non-interactive (execute directly)
- `scripts/x_api.py` — Added `MEDIA_FIELDS`, `expansions=["attachments.media_keys"]` to `get_user_timeline()`, media lookup from response includes
- `scripts/scout.py` — Added `profile_image_url` to `fetch_competitor()` return dict
- `agents/creator.md` — Added `status: "draft"` reminder at Step 2 (prevents auto-approval bypass)
- `agents/marc_pipeline.md` — Added `status: "draft"` instruction to both Creator spawn prompts

Session 24 files added/modified (10 files):
- `agents/marc.md` — Rewritten as Team Leader (Agent tool teammate spawning replaces nested `claude -p`)
- `agents/marc_conversation.md` — **New** System prompt for conversational Marc (identity, team reference, decision rules, START_TASK)
- `agents/marc_pipeline.md` — Rewritten as goal-oriented Pipeline Playbook (parallel teammate spawning)
- `agents/marc_publishing.md` — Rewritten as goal-oriented Publishing Playbook (teammate spawning)
- `agents/scout.md`, `strategist.md`, `creator.md`, `publisher.md`, `analyst.md` — Added "Teammate Mode" section
- `scripts/telegram_bot.py` — Major rewrite: conversational layer via `claude -p`, `_execute_task()` Agent Teams spawner, `/pipeline`, `/running` commands
- `scripts/run_task.sh`, `run_pipeline.sh` — Added `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, Team Leader prompts
- `CLAUDE.md` — Added Architecture section (two-layer design)

Phase 5 files added/modified (10 files):
- `agents/analyst.md` — Added "Intelligence Mode" section (anomaly detection, category breakdown, A/B test evaluation, trend comparison, report composition)
- `agents/scout.md` — Added "Daily Intelligence Mode" section + updated CLI usage with `--raw`/`--compact` flags
- `agents/publisher.md` — Added "Smart Outbound Mode" section (later moved to `agents/outbound.md` in Session 30)
- `agents/marc_pipeline.md` — Step 2 replaced with Claude Scout subagent invocation + fallback
- `agents/marc_publishing.md` — Step P4 replaced with smart outbound flow (later replaced with Outbound agent in Session 30), Step P8 replaced with analyst intelligence flow (P8a-P8c)
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
| Session 24 | Agent Teams Migration (Conversational Marc + Teammates) | Local machine | **✅ Complete** — 10 files modified/created, Marc responds conversationally via Telegram, spawns Agent Teams for execution |
| Session 25 | Production Testing (Real tasks via Telegram) | Local machine | **✅ Complete** — 5 tasks executed (3 ad-hoc + 1 image analysis + 1 daily pipeline), non-interactive bug fixed, media collection added, agent philosophy established |
| Session 26 | HTML Report Generation for Telegram Review | Local machine | **✅ Complete** — `generate_html_report.py` with 3 report types, pipeline + publishing playbooks updated |
| Session 32 | First Production Outbound + OAuth Fix + Agent Escalation | Local machine | **✅ Complete** — OAuth tokens fixed, 20 likes + 5 follows via API, 5 replies escalated to human. Agent escalation pattern established. |
| Session 45 | v4 Architecture Redesign (Python Orchestrator + Strategic Manager) | Local machine | **✅ Complete** — orchestrator.py replaces Marc coordination, 3-tier constraints, creative briefs, 5 LLM agents, ~50% cost reduction |
| Session 46 | Content Quality Fixes (Reference adoption, expression, grok removal) | Local machine | **✅ Complete** — reference adoption overhaul, expression whitelist, tool removal, grok removal, validation enforcement. 2 pipeline runs verified. |
| Session 47 | Metrics Visibility Fix (Real data for Marc + directive dedup) | Local machine | **✅ Complete** — orchestrator feeds SQLite analytics + archive data to all agents. Directive dedup enforcement. Standing directives cleaned 58→15. |
| Session 48 | Purpose-Driven Posts + Personality Captions + Pipeline Fixes | Local machine | **✅ Complete** — `moment_seed` → `post_purpose` + `visual_focus`. Visual diversity matrix. Personality captions (30-100 chars). 3-day visual dedup. No-text rule. Plan reconstruction. Retry logic. False drought fix. 9 files modified. |
| Session 48b | Auto Image Generation Plan | Local machine | **📋 Planned** — Browser Use CLI to automate Higgsfield web UI using existing Pro plan. Plan at `docs/plan-auto-image-generation.md`. |
| Session 49 | v5 Architecture Redesign (Meruru as Unified Creative Agent) | Local machine | **✅ Complete (Phases 0-3)** — Phase 0: visual style derived from 12 posted images. Phase 1: `meruru_identity.md`, `feed_balance.py`, `meruru.md`, `run_create()` — first run produced 6 character-driven candidates including "gm from the only person awake in this room". Phase 2: `/create` and `/balance` Telegram commands wired up; `meruru_balance.md` prompt; bonus fix to `send_telegram` apostrophe bug. Phase 3: cleanup — archived 5 v4 prompts, simplified `validate.py` (14/14 PASS), removed `run_warroom()`, updated `cron_wrapper.sh`, replaced LaunchAgent (`com.xagents.create.plist`), updated HTML report for 6-candidate split, rewrote `CLAUDE.md`. Bot restarted. Phase 4 (polish/iteration) ongoing. |
| Session 50 | All Daily Automation Halted (attempt) | Local machine | **⚠️ Halt not persistent (May 20, 2026)** — `launchctl unload` was effective only until the next login; macOS auto-reloaded all 5 plists from `~/Library/LaunchAgents/`. Jobs continued firing daily until Session 51. |
| Session 51 | Daily Automation Actually Halted | Local machine | **🛑 Stopped (June 8, 2026)** — Moved 5 daily plists to `~/Library/LaunchAgents/xagents-disabled/` and `launchctl bootout`'d each. Structurally impossible to auto-reload. Verified `launchctl list` shows only the 3 expired publish-slot agents. No daily Telegram messages from Marc going forward. |
| Phase 6 | VPS Deployment (provision, copy project, install cron) | VPS | Not started |
| Phase 7 | Autonomous Operation (cron runs agents overnight) | VPS | Not started |

---

## 10. Key Technical Decisions Explained

### Why Claude Code + cron instead of OpenClaw?

OpenClaw is a daemon-based framework with native messaging and always-listening capabilities. Claude Code is a session-based CLI tool. Despite this, Claude Code was chosen because: (a) it handles ~80% of requirements natively, (b) cron fills the scheduling gap reliably, (c) a 50-line Telegram bot fills the messaging gap, (d) staying within Anthropic's ecosystem avoids the security risks of OpenClaw's broad permissions and community skill vulnerabilities, (e) it avoids learning a second framework. The key insight was that the project needs a batch pipeline (run overnight, review in morning), not a real-time conversational daemon.

### Why a COO agent (Marc) instead of a simple orchestrator script?

**Updated in Session 45**: The original rationale proved partially wrong. Investigation showed Marc spent 73% of runtime on mechanical coordination (spawning agents, passing files, validating) — work a Python script does better and cheaper. The v4 redesign separated coordination (Python `orchestrator.py`) from management (Marc as Strategic Manager). Marc no longer orchestrates — he reviews every flow's output, evaluates 10K goal progress, updates standing directives, and proposes improvements. The judgment calls are real and valuable; they just don't need to happen at every step.

### Why X API + Playwright hybrid for the demo?

Pure X API (Basic, $200/month) cannot provide impression counts — that requires Pro at $5,000/month. Pure Playwright risks account bans. The hybrid uses official API for everything except impression scraping from own post pages — minimal risk, full functionality, $200/month. **Note**: Compliance review (Session 10) found that Playwright scraping — even on own pages — may violate X's ban on non-API automation of the website. This will be re-evaluated at Phase 4; Playwright may be removed entirely.

### Why CLAUDE.md instead of a database for agent memory?

CLAUDE.md files are automatically loaded by Claude Code at session start with zero custom code. For behavioral instructions ("never use more than 3 hashtags"), this is ideal. Structured data (metrics, rate limits, credentials) stays in JSON/SQLite because Python scripts need machine-parseable formats. This split — CLAUDE.md for behavior, JSON/SQLite for data — is a reusable pattern for any project using this framework.

### Why 6 agents for the demo instead of fewer or more?

Each agent maps to a distinct skill domain. Combining any two would bloat context windows. Splitting further would add coordination overhead without benefit. The COO-over-specialists pattern matches the original article's architecture and scales well — adding a new capability means adding one agent, not restructuring the whole system.

### Why Agent Teams instead of isolated subagents?

**Superseded in Session 45**: Agent Teams were replaced by the Python orchestrator + `claude -p` pattern. Agent Teams had reliability issues in `claude -p` non-interactive mode (Session 36: async messaging didn't reliably deliver). The v4 architecture uses `orchestrator.py` to invoke each LLM agent as an isolated `claude -p` call with focused prompts — simpler, cheaper, and more reliable. Agents communicate via JSON files on the shared filesystem, not in-memory messaging.

### Why `claude -p` for the conversational layer instead of Anthropic API?

The operator subscribes to Claude Max ($100/mo) which includes unlimited `claude` CLI usage. Using the Anthropic API would require a separate API key and billing. Since the conversational layer only needs text-in/text-out (no streaming, no complex tool use), `claude -p` provides the same capability at zero additional cost. The conversation uses a `START_TASK:` JSON marker pattern to signal when Marc decides to execute, replacing the Anthropic API's native tool_use mechanism.

---

## 11. Glossary

| Term | Definition |
|---|---|
| **Autonomous Agent Framework** | The general-purpose architecture for multi-agent systems being developed — the main project |
| **X Beauty Demo** | The first demonstration project validating the framework: growing an AI beauty X account |
| **Marc (Strategic Manager)** | Formerly COO/coordinator; as of v4 (Session 45), Marc is the Strategic Manager who reviews outputs at the end of every flow, evaluates 10K goal progress, updates standing directives, and proposes improvements. Also handles ad-hoc Telegram conversation. |
| **Scout** | Demo agent: scrapes competitor data and identifies trends using X API |
| **Strategist** | Demo agent: formulates growth strategy based on Scout and Analyst data |
| **Creator** | Demo agent: drafts post content and image prompts |
| **Publisher** | Demo agent: executes posting and outbound engagement via X API |
| **Analyst** | Demo agent: collects post metrics via X API batch lookup, account snapshots, stores in SQLite, generates JSON summaries. Manual impression input via Telegram /metrics, screenshot parsing (Claude Vision), or CSV/JSON import. |
| **War Room** | Multi-perspective analysis session (Analyst, Strategist, Moderator perspectives in a single LLM call) — produces recommendations and directive updates |
| **Pipeline** | The agent execution sequence — orchestrator.py runs Strategist → validate → Creator → validate → Marc Review |
| **CLAUDE.md** | Claude Code's native memory system — markdown files auto-loaded at session start |
| **Orchestrator** | `scripts/orchestrator.py` — Python script that sequences all pipeline steps, invokes `claude -p` for LLM reasoning, validates outputs, executes directives. Zero LLM cost for coordination. (Session 45) |
| **Shared State** | The filesystem layer (JSON + SQLite) through which agents exchange data between sessions |
| **OpenClaw** | Open-source agent framework evaluated and rejected in favor of Claude Code + cron |
| **Compliance Review** | Living document tracking 7 X Developer Terms issues to resolve during implementation |
| **Amarry Technologies** | Shimpei's company — the broader corporate context |
| **UniModel** | Amarry's primary product — an AI model marketplace (separate from this project) |
| **Agent Teams** | Claude Code experimental feature — used in v1-v3, replaced by Python orchestrator in v4 (Session 45) due to reliability issues in non-interactive mode |
| **Conversational Layer** | The lightweight `claude -p` layer that handles Telegram message intake, reasoning, and command routing to the orchestrator |
| **Visual Direction Summary** | Orchestrator-computed analysis of reference catalog's dominant scenes/outfits/content types, injected into Creator prompt to ensure generated content matches brand image (Session 46) |
| **Standing Directives** | `data/strategy/standing_directives.json` — persistent cross-day directives written by Marc after war rooms, read by all agents at startup. The mechanism for autonomous improvement (Session 44c). DIR-NNN ID format enforced since Session 47 to prevent duplication. |
| **Account Metrics Summary** | Orchestrator-computed SQLite query combining daily analytics (from CSV imports), follower/following counts (from Twitter archive), and top posts. Injected into Strategist and Marc Review contexts to ensure agents see real operational data (Session 47) |
| **3-Tier Constraint Hierarchy** | Content quality system: Tier 1 (hard validation by validate.py), Tier 2 (strong defaults in prompts), Tier 3 (full creative freedom). Replaced 40+ equally-enforced constraints (Session 45) |
| **Post Purpose** | One of 5 strategic intents assigned per slot: `body_showcase`, `face_beauty`, `lifestyle_vibe`, `engagement_hook`, `style_flex`. Replaced `moment_seed` narrative arcs (Session 48) |
| **Visual Focus** | Lightweight 2-field Strategist directive: `emphasis` (where the viewer's eye goes) + `framing` (how tight the shot is). Creator has full autonomy on everything else (Session 48) |
| **Visual Diversity Matrix** | Validation check on Creator output ensuring variety across 4-post sets: framings≥2, angles≥2, poses≥3, outfit coverage levels≥2. Prevents monotonous profile grids (Session 48) |
| **Personality Captions** | EN captions must be 30-100 chars showing Meruru's character (mood, humor, confessions, inner monologue) — not 3-word fragments. Aim 40-80 chars. Validated by validate.py (Session 48) |
| **Plan Reconstruction** | `_reconstruct_plan()` in orchestrator.py — when Creator (Sonnet) outputs individual post JSON objects instead of the wrapper, orchestrator collects all posts and rebuilds the full plan structure (Session 48) |
| **Recent Visual History** | Orchestrator-extracted fingerprints (scene, pose, framing, angle, outfit) from last 3 content plans (~12 posts), injected as `{{recent_visual_history}}` blocklist to prevent Creator from repeating similar images (Session 48) |
