# Project Context Document
# Autonomous AI Agent System

**Purpose of this document**: Enable any third party to fully understand the project vision, decision history, current state, and deliverables without needing to read the full conversation transcript.

**Last updated**: March 3, 2026 (Session 15: Phase 1 Testing Complete)

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

**Decision 10**: Local-first development. Phases 0-4 run on your own machine (CLI). VPS provisioning moves to Phase 5. Autonomous cron operation is Phase 6.

**Phase 0 Runbook rewritten**: Completely replaced VPS-centric 12-step guide with local development setup (9 steps). No server provisioning, hardening, or cron setup.

**Implementation phases restructured**: 5 phases → 7 phases:
- Phases 0-4: Your machine (build, test, iterate)
- Phase 5: VPS deployment (provision, copy project, install cron)
- Phase 6: Autonomous operation (cron triggers agents overnight)

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
- Parent spec (`x-ai-beauty-spec-v2.3.md`): project structure updated, Section 11.2 annotated as Phase 5+, locking recommendation extended, Phase 5 checklist annotated
- Parent PRD (`x-ai-beauty-prd-v1.md`): F7 note updated to link Phase 1 spec
- Review doc (`review.md`): Issues 3.15 and 3.16 annotated with Phase 1 resolution status

**Self-review found and fixed 10 issues** (2 HIGH, 2 MEDIUM, 6 LOW):
- **HIGH**: `strategy_current.json` write conflict (Strategist vs Marc) — resolved: Marc is sole writer after validation
- **HIGH**: Strategist invocation mechanism ambiguous (`$(cat)` vs progressive disclosure) — resolved: standardized on progressive disclosure
- **MEDIUM**: `run_pipeline.sh` missing `.pipeline.lock` implementation — added
- **MEDIUM**: `competitors.json` schema missing — added cross-reference to parent spec Section 10.2
- **LOW**: Date format conversion undocumented, hardcoded competitor counts, `--dry-run` undefined, Scout output path convention, Phase 0 prerequisite missing from PRD, `--dangerously-skip-permissions` security note missing — all fixed

**Deliverables**: `specs/phase-1-spec.md` (v1.0) + `specs/phase-1-prd.md` (v1.0)

---

## 4. Decision Summary

### Framework-Level Decisions (Apply to All Future Projects)

| # | Decision | Rationale |
|---|---|---|
| D1 | Claude Code + cron as the agent execution framework | Handles 80% natively; cron fills scheduling gap; avoids dependency on OpenClaw |
| D2 | VPS for always-on compute (Phase 5 deployment) | Cheaper than hardware ($12/mo Vultr Tokyo); only needed for autonomous operation |
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
| D10 | Local-first development; VPS deferred to Phase 5 | VPS only needed for autonomous operation; development uses your own machine + CLI |
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

---

## 6. Demo Project: X Beauty System

### 6.1 Agent Architecture

```
Human (Shimpei)
└── Telegram (unified communication)
    └── 🎖️ Marc (COO / Orchestrator / Reporter)
        ├── 🔍 Scout ──────── Competitor research & trend analysis      [X API v2]
        ├── 📊 Strategist ─── Data-driven growth strategy               [Claude Code]
        ├── ✍️ Creator ─────── Content drafting & image prompts          [Claude Code]
        ├── 📢 Publisher ──── Posting & outbound engagement             [X API v2 ⚠️]
        └── 📈 Analyst ────── Metrics collection & data storage         [X API + Playwright ⚠️]
```

⚠️ = X Developer Terms compliance concerns logged. See `specs/x-developer-terms-compliance-review.md`.

### 6.2 Key Details

- **Goal**: 0 → 10,000 followers on at least one account (EN or JP)
- **Tech stack**: Claude Code CLI + cron + X API v2 (Basic $200/mo) + Playwright (under compliance review) + python-telegram-bot + SQLite + CLAUDE.md
- **Monthly cost**: $300 during development (X API $200 + Claude Max $100). Vultr VPS ($12/mo) added at Phase 5 deployment.
- **Daily pipeline**: 0:30 AM pipeline start → 7:00 AM morning brief → 7-9 AM human approval → 9 AM-9 PM posting & engagement → 11 PM metrics → 11:30 PM daily report → 11:45 PM retrospective
- **Estimated timeline**: ~19 days from Phase 0 start to autonomous operation (Phases 0-4 local development, Phase 5 VPS deployment, Phase 6 autonomous)

### 6.3 Open Questions (Unresolved)

| # | Question | Impact | Status |
|---|---|---|---|
| OQ-1 | Which AI image generation tool (Midjourney, SD, Flux)? | Affects Creator's prompt format | Open |
| OQ-2 | Initial competitor list (10+ accounts)? | Blocks Phase 1 testing | **Resolved: 41 unique accounts (26 EN + 17 JP, 2 overlap)** |
| OQ-3 | Fresh X accounts or existing ones? | Affects Phase 0 setup | **Resolved: Use existing accounts** |
| OQ-4 | Monthly budget ceiling above $350? | Determines scope constraints | Open |
| OQ-5 | Operate on weekends/holidays? | Affects scheduling | Open |
| OQ-6 | VPS provider preference? | Affects Phase 5 deployment | **Resolved: Vultr Tokyo ($12/mo)** |
| OQ-7 | Claude subscription tier (Pro $20 vs Max $100)? | Affects cost and capability | **Resolved: Claude Max ($100/mo)** |
| OQ-8 | Backup destination (S3, Google Drive, local)? | Affects Phase 4 implementation | Open |

**Updated monthly cost**: $300 during development (X API $200 + Claude Max $100). Vultr VPS ($12/mo) added at Phase 5.

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
│   ├── marc.md, scout.md, strategist.md,
│   │   creator.md, publisher.md, analyst.md
│   └── (placeholders — built during Phases 1-4)
│
├── scripts/                                ← PIPELINE & UTILITY SCRIPTS
│   ├── run_pipeline.sh                    ← Phase 1 entry point (thin wrapper → Marc)
│   ├── validate.py                        ← Deterministic validation (scout/strategist/cross)
│   ├── x_api.py                           ← X API v2 wrapper library
│   └── scout.py                           ← Scout agent script
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
    └──▶ procedures/add-competitor.md
            │
            │  "Add/remove competitor accounts"
            │  "Keeps competitor-accounts.md + competitors.json in sync"
            │
            └──▶ Operates on ──▶ competitor-accounts.md + competitors.json
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
| `context.md` | Meta | This document — full project context for third-party understanding |

---

## 9. Implementation Status

### Development Approach

All development happens on your own machine. A VPS is only needed when the system is ready to run autonomously. Phases 0-4 are local CLI development. Phase 5 is VPS deployment. Phase 6 is autonomous operation.

**Latest**: Phase 1 complete — all 12 tests passed (March 3, 2026).

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
| Phase 2 | Creator + Telegram Command Processing | Local machine | Not started |
| Phase 3 | Publisher + X API Posting | Local machine | Not started |
| Phase 4 | Analyst + Full Integration (2-3 day manual test) | Local machine | Not started |
| Phase 5 | VPS Deployment (provision, copy project, install cron) | VPS | Not started |
| Phase 6 | Autonomous Operation (cron runs agents overnight) | VPS | Not started |

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
| **Analyst** | Demo agent: collects performance metrics via X API (Playwright impression scraping under compliance review) |
| **War Room** | Marc's daily review session where all agent outputs are cross-checked for consistency |
| **Pipeline** | The agent execution sequence — during development, triggered manually via CLI; in production, triggered by cron overnight |
| **CLAUDE.md** | Claude Code's native memory system — markdown files auto-loaded at session start |
| **Orchestrator Script** | Shell script that cron triggers; launches Marc who then invokes agents in sequence |
| **Shared State** | The filesystem layer (JSON + SQLite) through which agents exchange data between sessions |
| **OpenClaw** | Open-source agent framework evaluated and rejected in favor of Claude Code + cron |
| **Compliance Review** | Living document tracking 7 X Developer Terms issues to resolve during implementation |
| **Amarry Technologies** | Shimpei's company — the broader corporate context |
| **UniModel** | Amarry's primary product — an AI model marketplace (separate from this project) |
