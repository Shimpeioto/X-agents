# Document Review: X AI Beauty Autonomous Agent System

**Reviewer**: Claude (AI) | **Date**: March 2, 2026 | **Status**: Pre-Implementation Review

## Documents Reviewed

| # | Document | Filename | Version |
|---|---|---|---|
| 1 | Technical Specification | `x-ai-beauty-spec-v2.3.md` | v2.3, March 1 2026 |
| 2 | Product Requirements Document | `x-ai-beauty-prd-v1.md` | v1.0, March 1 2026 |
| 3 | X Developer Terms Compliance Review | `x-developer-terms-compliance-review.md` | Unversioned, March 2 2026 |
| 4 | Phase 0 Runbook | `phase-0-runbook.md` | v2.0, ~March 2 2026 |
| 5 | Context & Decision Log | `context.md` | Unversioned, March 1 2026 |
| 6 | Framework Analysis | `autonomous-agent-system-analysis.md` | Unversioned, Feb 28 2026 |

---

## 1. Executive Summary

The six documents are approximately **80% solid** and demonstrate thorough thinking about architecture, agent design, and operational flow. However, the review uncovered **critical gaps that must be resolved before Phase 0 implementation begins**.

### Issue Counts by Severity

| Severity | Count | Description |
|---|---|---|
| **Critical** | 12 | Must fix before Phase 0 starts. Blocks implementation or creates compliance/security risk. |
| **High** | 18 | Must fix before Phase 1. Missing technical details that will cause implementation failures. |
| **Medium** | 30+ | Fix during implementation. Gaps that affect quality but don't block progress. |
| **Low** | 8 | Fix when convenient. Minor inconsistencies, naming issues, optimizations. |

### Top 5 Most Urgent Issues

1. **Compliance violations designed into spec/PRD** — 4 features prohibited by X Terms are still presented as core functionality (§3.1, §3.2)
2. **PRD references non-existent spec v2.1** — anyone following PRD hits dead links (§2.1)
3. **Duplicate Risk Management section in spec** — Sections 8 and 17 are word-for-word identical (§3.1)
4. **Human time commitment contradicts across 3 sections** — <30 min vs <1 hour vs 30-60 min vs 2-hour window (§4.2)
5. **Telegram Bot daemon completely unspecified** — critical always-running component with zero design documentation (§3.8)

---

## 2. Cross-Document Issues

### 2.1 PRD References Non-Existent Spec v2.1 [CRITICAL]

- **Location**: `x-ai-beauty-prd-v1.md` lines 8, 400
- **Quote**: `[Technical Specification v2.1](./x-ai-beauty-agent-config-v2.1-en.md)`
- **Problem**: This file does not exist. The current spec is `x-ai-beauty-spec-v2.3.md`. PRD line 192 correctly references v2.3, showing the update was partially done but inconsistent.
- **Also**: PRD line 359 references "Technical Specification v2.1, Section 8 (Risk Management)" — the section mapping changed between v2.1 and v2.3.
- **Fix**: Replace all v2.1 references with v2.3 and correct filename to `x-ai-beauty-spec-v2.3.md`.

### 2.2 Open Questions Resolved in context.md but Still "Open" in PRD [HIGH]

- **Location**: `context.md` lines 399-407 vs `x-ai-beauty-prd-v1.md` lines 382-386
- **Details**:
  - OQ-3: Resolved in context.md — "Use existing accounts." Still listed as "Open" in PRD.
  - OQ-6: Resolved in context.md — "Vultr Tokyo ($12/mo)." Still listed as "Open" in PRD.
  - OQ-7: Resolved in context.md — "Claude Max ($100/mo)." Still listed as "Open" in PRD.
- **Impact**: PRD is outdated. These were resolved in Session 9 (per context.md line 242) but PRD was never updated.
- **Fix**: Update PRD Section 14 to mark OQ-3, OQ-6, OQ-7 as resolved with their decisions.

### 2.3 Compliance Violations Designed into Spec/PRD Without Acknowledgment [CRITICAL]

- **Location**: All documents
- **Problem**: The compliance review identifies 4 critical X Terms violations (automated likes, follows, cold replies, Playwright scraping). The spec still includes all of these as core features with monthly volume projections. The PRD doesn't reference the compliance review at all.
- **Root cause**: Decision 11 (`context.md` line 274) was to "record compliance concerns without making spec changes." This created a situation where the spec prescribes features that X explicitly prohibits.
- **Cross-document status**:

| Issue | context.md | compliance-review | spec | PRD | runbook |
|---|---|---|---|---|---|
| Automated likes banned | "resolve Phase 3" | Full section | Still in design as "Safe" | No mention | No mention |
| Automated follows BAN risk | "resolve Phase 3" | Full section | Still in design as "Safe" | No mention | No mention |
| Cold replies banned | "resolve Phase 3" | Full section | Vague | Vague | No mention |
| Playwright scraping banned | "may be removed" | Full section | Still in design | No mention | Step 7 setup |

- **Fix**: Add compliance warnings inline in spec and PRD wherever prohibited features appear. Reference the compliance review document.

### 2.4 Phase Count Mismatch: PRD Says 5 Phases, Spec/Context Say 7 [HIGH]

- **Location**: PRD Section 13 vs spec Section 7 vs context.md Section 6.2
- **Details**: PRD describes a 5-phase, 17-day timeline (Phases 0-5). Spec and context describe a 7-phase timeline (Phases 0-6, ~19 days). The local-first development decision (Session 10) added the Phase 5/6 split but PRD was never updated.
- **Fix**: Update PRD Section 13 to reflect the 7-phase timeline.

### 2.5 `global_rules` Format Inconsistency (JSON vs Markdown) [HIGH]

- **Location**: Spec Section 10.3 vs Spec Section 13.4 vs Phase 0 Runbook Step 5
- **Details**:
  - Spec Section 10.3 defines `config/global_rules.json` as a JSON file with structured rule objects
  - Spec Section 13.4 says this was migrated to Markdown (`config/global_rules.md`) for native CLAUDE.md loading
  - Marc's agent description (Spec Section 3, line 229) says Marc updates `config/global_rules.json` (JSON)
  - Runbook Step 5 (line 219) creates it as `global_rules.md` (Markdown)
  - Health check script (Runbook line 476) checks for `config/global_rules.md`
- **Fix**: Reconcile to one format. The Markdown format appears to be the final decision per Section 13.4. Update all JSON references in Sections 3 and 10.3.

### 2.6 Agent Count Discrepancy: 5 vs 6 Agents Listed [HIGH]

- **Location**: Spec Section 1 vs context.md vs PRD
- **Details**:
  - `context.md` line 32: "6-agent system" — lists Scout, Strategist, Creator, Publisher, Analyst, Commander/Marc
  - Spec Section 1 agent list (line 35): Lists only 5 agents (Scout, Strategist, Creator, Publisher, Analyst) — Marc missing from numbered list
  - Spec diagram (line 31): Shows Marc at top (6 total)
  - Spec Section 3 header: "Agent Roster (6 Agents)" — correct
  - PRD line 14: "A COO agent (Marc) orchestrates five specialist agents" — correct
- **Fix**: Add Marc explicitly to the Section 1 agent list.

### 2.7 PRD Does Not Reference Compliance Review Document [HIGH]

- **Location**: PRD — no cross-reference exists
- **Problem**: A reader of the PRD would have no idea that 7 X compliance issues exist. PRD should either reference the compliance doc or incorporate issue summaries.
- **Fix**: Add a subsection to PRD Section 12 referencing `x-developer-terms-compliance-review.md`.

### 2.8 VPS Setup Labeled "Phase 0" in Spec But Is Actually Phase 5 [MEDIUM]

- **Location**: Spec Section 16.1 title: "Initial VPS Setup (Phase 0)"
- **Problem**: The entire document philosophy (Section 7) and Phase 0 Runbook both say Phase 0 is local development. VPS is Phase 5.
- **Fix**: Change Section 16.1 title to reference Phase 5.

### 2.9 OAuth Version Confusion: 1.0a and 2.0 Mixed [HIGH]

- **Location**: Spec Section 9.1 and Section 10.1
- **Details**: Section 9.1 says the system uses "OAuth 2.0 User Context" but the `accounts.json` schema includes both `access_token_secret` (OAuth 1.0a concept) and `refresh_token` (OAuth 2.0 with PKCE). The spec never clarifies which method is used.
- **Fix**: Clarify which OAuth method is primary and remove fields from the unused method, OR document the dual-auth strategy explicitly.

### 2.10 Missing Cross-References Between Documents [MEDIUM]

- Spec has no link to compliance review document
- PRD has no link to compliance review document
- Runbook has no "Related Documents" section linking to PRD
- Compliance review references phases by number but not document filenames

### 2.11 Cost Breakdown Missing from PRD [MEDIUM]

- **Location**: PRD Section 3.2 vs context.md Section 6.3
- **Details**: context.md clearly states: Development $300/month (X API $200 + Claude Max $100), Production $312/month (+VPS $12/mo). PRD only says "<$350/month" with no breakdown.
- **Fix**: Add cost breakdown to PRD Section 3.2 or 6.1.

### 2.12 Context Document Has Stale Directory Path [LOW]

- **Location**: `context.md` Section 7, line 417
- **Quote**: `/mnt/user-data/outputs/`
- **Problem**: This is the path from the AI conversation environment where documents were originally generated, not the actual path on disk (`/Users/shimpeioto/Amarry/X-agents/`).
- **Fix**: Update to actual project path.

### 2.13 Compliance Review Phase-0 Catch-22 [CRITICAL]

- **Location**: Compliance review Issue 7 vs Phase 0 Runbook Step 3
- **Details**: The use case description sample in the Runbook (lines 106-108) explicitly mentions "likes, replies" — the very operations flagged as prohibited in Issues 1 and 3. Since Issue 7 says the use case description is binding, submitting this description and then removing likes/replies would itself be a compliance issue (material change).
- **Fix**: Resolve whether likes/replies will be included BEFORE writing the use case description in Step 3.

---

## 3. Spec v2.3 Issues

### 3.1 Duplicate Risk Management Sections [CRITICAL]

- **Location**: Section 8 (lines 826-839) and Section 17 (lines 1641-1660)
- **Problem**: Word-for-word identical content. Both titled "Risk Management" with the same 8-row table. The document header claims "Renumbered Sections 14-16 to 15-17" but the old Section 8 was never removed.
- **Fix**: Delete Section 17 (the duplicate), or consolidate unique content from both into one section.

### 3.2 Post Frequency Contradiction [CRITICAL]

- **Location**: Header (line 10) vs Section 2.2 (line 83) vs Section 3 (line 192) vs Section 5 (lines 659-663)
- **Details**:
  - Header: "Post frequency: 3-5 posts/day per account"
  - Section 2.2 API calculation: Uses 5 posts × 2 accounts × 30 days = 300 posts/month
  - Section 3 Marc's brief: Lists exactly 4 post times for both EN and JP
  - Section 5 Pipeline Schedule: Lists only 4 scheduled post times
- **Fix**: Decide on the actual frequency (4 is the implementation reality) and make all references consistent. Update API usage calculations accordingly.

### 3.3 Missing Telegram Bot Daemon Design [CRITICAL]

- **Location**: Spec Section 4 lists `scripts/telegram_bot.py` in project structure (line 637) but never defines it
- **Problem**: The Telegram Bot is the always-running process that receives human commands (`/approve`, `/edit`, `/pause`, etc.). Its architecture — polling vs webhook, how it invokes Claude, how it authenticates, how it processes concurrent commands — is completely unspecified. When Shimpei sends `/approve` via Telegram at 7:15 AM, *something* must receive that message, process it, and invoke Marc. The bot daemon is that something, but its design is absent from all documents.
- **Fix**: Add a dedicated section specifying the Telegram Bot daemon architecture.

### 3.4 Missing OAuth Refresh Implementation Details [HIGH]

- **Location**: Section 9.1 (lines 870-876)
- **Quote**: "Access tokens expire after 2 hours. The `x_api.py` wrapper must implement automatic refresh using the refresh token."
- **Missing**: When to check token expiry (proactively vs reactively), what to do if refresh fails mid-operation, token storage/rotation security, how Marc "escalates to human" when Marc is an AI agent with no direct way to halt X API operations mid-execution.
- **Fix**: Specify the token refresh flow including error recovery.

### 3.5 Missing Playwright Technical Details [HIGH]

- **Location**: Section 2.5 (lines 139-142)
- **Quote**: "Impression counts are scraped via Playwright from our own account's post detail pages only."
- **Missing**: CSS selectors, handling for page layout changes, backup plan if impressions are unavailable, page load wait times, how image descriptions are extracted (vision AI? alt-text? URL analysis?).
- **Fix**: Add selector specifications or at minimum a discovery procedure.

### 3.6 SQLite Schema Missing Constraints [HIGH]

- **Location**: Section 5 (lines ~547-570)
- **Problem**: `post_metrics` table has no PRIMARY KEY or UNIQUE constraint. Nothing prevents duplicate (tweet_id, measured_at) entries. The `engagement_rate` column divides by `impressions` but `impressions` can be NULL (from Playwright failures), which would cause division errors.
- **Fix**: Add constraints and specify NULL handling for engagement calculations.

### 3.7 Missing Rate Limit Enforcement Mechanism [HIGH]

- **Location**: Section 2.4 (lines 117-122) and Section 10.5 (lines ~1002-1015)
- **Problem**: Rate limit counters are defined in JSON but HOW Publisher enforces them is unspecified. No grace period, no recovery specification (midnight reset vs 24h rolling window).
- **Fix**: Specify the enforcement mechanism in Publisher's agent definition.

### 3.8 Missing Post Status Transition Validation [HIGH]

- **Location**: Section 4 (lines 650-656)
- **Details**: Lifecycle shows `draft -> approved -> media_ready -> scheduled -> posted -> measured` but: who can perform each transition? What happens if a post skips a state? Is there a rollback mechanism if human withdraws approval?
- **Fix**: Add a transition table with actors and validation rules.

### 3.9 Missing Telegram Command Validation [HIGH]

- **Location**: Section 3.0 (lines 213-223)
- **Problem**: Commands like `/approve`, `/edit`, `/pause`, `/strategy` are listed but: no validation rules for invalid input, no error response format, no timeout behavior, no concurrency handling (what if two `/approve` commands sent simultaneously?).
- **Fix**: Add validation schemas and error response specifications.

### 3.10 Credential Storage Security Insufficient [HIGH]

- **Location**: Section 9.3 (line 876)
- **Details**: `chmod 600` for `config/accounts.json` (gitignored). No backup encryption. If VPS compromised, credentials are plaintext. Refresh tokens are long-lived — attacker with `accounts.json` can refresh tokens indefinitely.
- **Fix**: Add encrypted storage or secret management specification. Add VPS hardening steps.

### 3.11 VPS Root Access Not Secured [HIGH]

- **Location**: Section 16.1 (lines 1523-1533)
- **Quote**: `ssh root@<vps-ip>`
- **Missing**: No mention of disabling root SSH login (`PermitRootLogin no`), SSH key permissions, disabling password auth.
- **Fix**: Add VPS hardening checklist.

### 3.12 Telegram Bot Has No Rate Limiting [HIGH]

- **Location**: Section 3.0 (lines 213-223)
- **Problem**: No rate limiting on Telegram commands. User could spam `/pause /resume /pause /resume`. No audit logging of commands.
- **Fix**: Add command rate limiting and audit log specification.

### 3.13 Playwright Browser Profiles Store Session Cookies in Plaintext [HIGH]

- **Location**: Section 7.1 / 16.1 (lines 760-761, 1550)
- **Problem**: Browser profiles store X session cookies unencrypted on disk. No profile file encryption or secure storage specified.
- **Fix**: Acknowledge risk or add encryption specification.

### 3.14 Missing `aiosqlite` in Spec Deployment Dependencies [HIGH]

- **Location**: Spec Section 16.1 (line 1561) vs Runbook Step 2
- **Details**: Spec deployment pip install lists `tweepy python-telegram-bot anthropic playwright aiohttp` but omits `aiosqlite`. Runbook correctly includes it.
- **Fix**: Add `aiosqlite` to spec deployment dependencies.

### 3.15 Missing `telegram_alert.py` Script [HIGH]

- **Location**: Spec line 1094 (`orchestrator.sh` references it)
- **Problem**: The orchestrator.sh script calls `telegram_alert.py` for error notifications but this script is never defined anywhere.
- **Fix**: Define the script or remove the reference.
- **Phase 1 resolution note**: This remains a Phase 2+ concern. Phase 1 uses `run_pipeline.sh` (not `orchestrator.sh`), so `telegram_alert.py` is not needed until the full orchestrator is deployed in Phase 5.

### 3.16 No Claude Model Selection Per Agent [MEDIUM]

- **Location**: Spec Section 12, line 1153
- **Quote**: `CLAUDE_MODEL=claude-sonnet-4-20250514  # or opus for Marc`
- **Problem**: There is no mechanism for dynamically selecting different models for different agents. Each cron invocation is a separate `claude -p` call. Marc can't use Opus while Scout uses Sonnet unless the orchestrator sets different environment variables per invocation. This is never addressed.
- **Fix**: Add model selection logic to orchestrator.sh or agent invocation.
- **Phase 1 resolution note**: Phase 1's `run_pipeline.sh` supports setting `CLAUDE_MODEL` before invoking Marc. Marc can also set `CLAUDE_MODEL` per subagent invocation via `claude -p` calls. See [Phase 1 Spec](./docs/specs/phase-1-spec.md) Section 4.2.

### 3.17 Cron Job Timing Assumes Zero Latency [MEDIUM]

- **Location**: Section 11.1 crontab
- **Problem**: No locking/queuing mechanism to prevent concurrent X API operations. Two Claude Code sessions running simultaneously could cause SQLite write conflicts. If Marc's 6:00 War Room review is still running at 7:00, the next scheduled task starts anyway.
- **Fix**: Add flock-based locking or queue mechanism to orchestrator.

### 3.18 Human Approval Window Too Tight [MEDIUM]

- **Location**: Section 5 (line 671)
- **Quote**: "7:00-9:00 HUMAN: Approve posts & prepare images"
- **Problem**: 2-hour window for human to approve 8 posts (4 EN + 4 JP) AND prepare 8 images. If timezone mismatch or busy, 9:00 post deadline missed. No specification of what happens if approval is late.
- **Fix**: Specify late-approval behavior (skip slot, queue for next, etc.).

### 3.19 API Budget Underestimated [MEDIUM]

- **Location**: Section 2.2 Read operations (lines 93-97)
- **Details**: Claims ~10,700 reads/month but:
  1. Analyst runs twice/day (line 668: 15:00 and 23:00) but math counts only once. Actual: 2 × 1,200 = 2,400/month (not 1,200). Revised: ~11,900.
  2. Token refresh calls unbudgeted (~150/month).
  3. Realistic total: **~12,500-13,200 reads/month** (still within 15,000 budget but with only ~10-15% buffer, not the claimed 30%).
- **Fix**: Recalculate with correct Analyst frequency and token refresh overhead.

### 3.20 Marc Dual-Role Coupling [MEDIUM]

- **Location**: Section 3.0 (lines 145-165)
- **Problem**: Marc is both orchestrator AND reporter. If Marc's execution is interrupted mid-pipeline, Telegram reporting is incomplete. These should be separate concerns.
- **Fix**: Consider separating orchestration and reporting responsibilities, or document the coupling risk.

### 3.21 Analyst NULL Handling for Impressions [MEDIUM]

- **Location**: Section 5 (lines ~526-570)
- **Details**: `impressions INTEGER, -- From Playwright (may be NULL)` but `engagement_rate` calculation divides by impressions. No specification of what `engagement_rate` is when impressions are NULL.
- **Fix**: Add NULL handling specification (e.g., separate `engagement_rate_api_only` metric).

### 3.22 Publisher Concurrency Not Specified [MEDIUM]

- **Location**: Section 3.4 (lines 472-499)
- **Problem**: No locking mechanism for concurrent operations. No specification of operation order (post first then outbound? interleaved?). No retry specification.
- **Fix**: Add concurrency and retry specifications.

### 3.23 Outbound Engagement Timing Conflicts with Posting [MEDIUM]

- **Location**: Section 5 crontab (lines 1057-1059)
- **Problem**: Outbound batch at 10:30 may run before Post #2 is scheduled. No specification of dependencies between posting and outbound timing.
- **Fix**: Add dependency ordering.

### 3.24 Configuration Schema Missing Fields [MEDIUM]

- **Location**: Sections 10.1-10.5
- **Missing fields**:
  - `accounts.json`: `token_expiry`, `token_refresh_at`, `account_status`, `api_version`
  - `competitors.json`: `last_scraped`, `api_error_count`, `status` (active/private/suspended), `follow_reason`
  - `rate_limits_{date}.json`: `timestamp`, `warning_sent`, `reset_time`
- **Fix**: Add the missing fields.

### 3.25 Scout Error Handling for Private Accounts [MEDIUM]

- **Location**: Section 3.1 (line 276)
- **Problem**: No spec for how Scout handles competitors going private mid-day. Does Scout add private accounts to `new_accounts_discovered` or silently skip?
- **Fix**: Specify error handling behavior.

### 3.26 Runbook Bash Compatibility Issue (macOS) [MEDIUM]

- **Location**: Phase 0 Runbook Step 8 (lines 424-429)
- **Problem**: Uses `${agent^}` (capitalize first letter) which is a Bash 4+ parameter expansion. macOS default shell is zsh where this syntax doesn't work. The runbook targets macOS/Linux.
- **Fix**: Replace with POSIX-compatible capitalization or note Bash requirement.

### 3.27 Playwright VPS Resource Concern [LOW]

- **Problem**: Running Playwright browser automation on a 2 vCPU / 4 GB RAM VPS while Chromium competes with Claude Code execution may cause resource exhaustion.
- **Fix**: Add resource monitoring or specify minimum requirements more conservatively.

### 3.28 Posting Time Precision [LOW]

- **Location**: Section 5 crontab
- **Problem**: Cron only guarantees execution "at some point during that minute." For engagement optimization this is fine, but the spec doesn't acknowledge this.

---

## 4. PRD v1.0 Issues

### 4.1 10K Follower Target Unrealistic for Timeline [CRITICAL]

- **Location**: Section 3.1, Section 1
- **Quote**: "Reach 10,000 followers on at least one account (EN or JP) as fast as possible"
- **Problem**: Success metric says ">100 followers/day sustained after Week 2." At 100/day, 10K followers requires ~100 days. The project timeline is 17-19 days. Section 3.4 explicitly excludes monetization and real-time trend-jacking — two major growth mechanisms.
- **Fix**: Either adjust the target to be timeline-realistic or frame 10K as a long-term north-star goal.

### 4.2 Human Time Commitment Contradicts Across 3 Sections [CRITICAL]

- **Location**: Section 4.1 vs Section 3.2 vs Section 11.2
- **Details**:
  - Section 4.1: "Available for 30-60 minutes in the morning (7-9 AM JST)" — implies 2-hour availability window
  - Section 3.2: "<1 hour/day" success metric
  - Section 11.2: "Human can complete daily workflow in <30 minutes"
- **Reality check**: Morning workflow includes: receive brief (5 min) + review 4+ posts per account (10 min/post = 40+ min) + generate images with Midjourney/Stable Diffusion (15-20 min/image × 8 images = 60-80 min). Total: ~2 hours minimum.
- **Fix**: Reconcile the three numbers. Image generation time must be factored in since Section 3.4 says "AI image generation (human prepares images using external tools)" — it is NOT automated.

### 4.3 F7 (Marc Orchestration) Severely Under-Specified [CRITICAL]

- **Location**: Section 5.1, F7
- **Quote**: "Marc manages the full pipeline: agent sequencing, dependency management, error handling, War Room reviews."
- **Problems**: "War Room review" is undefined. No decision criteria for skipping/rescheduling agents. No handling for partial pipeline failures. No output validation criteria.
- **Estimated effort to specify**: 5+ days.
- **Fix**: Create a detailed Marc orchestration specification.

### 4.4 Timeline Unrealistic Given Constraints [CRITICAL]

- **Location**: Section 13
- **Details**: 17 days × 1 hour/day = 17 hours total. This must cover: learning the system, debugging, testing, image generation, approval workflows, AND iterating. Zero buffer.
- **Phase 5 starts Day 17**: Requires 3 days → production at Day 20. But success metric says ">100 followers/day sustained after Week 2" = by Day 14-15. The timeline and metrics are incompatible.
- **Fix**: Extend timeline to 25-30 days with explicit buffer phases.

### 4.5 Section Numbering Error [HIGH]

- **Location**: Lines 207-249
- **Problem**: Heading `## 8. User Stories` contains subsections numbered "7.1", "7.2", "7.3", "7.4". The next heading is also `## 8. Telegram Command Specification`. Two Section 8s exist.
- **Fix**: Renumber sections correctly.

### 4.6 F9 (Human Approval Flow) Under-Specified [HIGH]

- **Location**: Section 5.1, F9
- **Missing**: What happens if media is not provided? Approval timeout is undefined. No mechanism to rescind approval. What if approved Monday but images not until Wednesday — does post go live with no TTL?
- **Fix**: Specify approval edge cases including timeout/TTL.

### 4.7 Approval Flow Contradiction [HIGH]

- **Location**: Section 4.1 vs Section 9.2 vs Section 5.3
- **Details**:
  - Section 4.1: Human approves "7:00-9:00 AM"; first post at 9:00 AM
  - Section 9.2: "Human doesn't approve by 9:00 AM → Marc sends reminder. Posts wait."
  - But: Posts created at 8:59 AM — go live at 9:00 or wait?
  - Section 5.1 F4: "Scheduled at optimal times" determined by Strategist, not human
- **Fix**: Clarify the exact approval→posting pipeline timing.

### 4.8 Missing Content Status "Approved but Unscheduled" [HIGH]

- **Location**: Section 9.1
- **Problem**: Strategist runs at 0:30 AM (determines posting times), BEFORE the 7:00-9:00 approval window. So when posts are approved, they don't yet have scheduled times. There's no `approved_unscheduled` status.
- **Fix**: Either add the missing status or change the pipeline order.

### 4.9 `failed` Status Has No Retry Mechanism [HIGH]

- **Location**: Section 9.2
- **Problem**: Max retries not specified. Retry backoff strategy absent. Escalation defined but no action. No `/retry <post_id>` command.
- **Fix**: Specify retry logic and add `/retry` command.

### 4.10 Follower Anomaly Detection Not Implemented [HIGH]

- **Location**: Section 11.2 vs User Stories
- **Details**: Section 11.2 requires "Follower anomaly detection works." US-12 says "Be alerted immediately if account loses >10% followers." But no agent is assigned this, no implementation plan exists, no detection logic is specified.
- **Fix**: Assign to Analyst or Marc and specify the logic.

### 4.11 Agent Implementation Sequencing Not Planned [HIGH]

- **Location**: Section 13 (Timeline)
- **Problem**: Scout/Strategist depend on each other; Creator depends on Strategist output format; Publisher depends on Creator. No time allocated for interface finalization. Marc must be partially built in Phase 1 to orchestrate Scout/Strategist, but no separate Marc phase exists.
- **Fix**: Add interface specification tasks to Phase 1 and allocate Marc implementation time.

### 4.12 8 Missing User Stories [HIGH]

The following scenarios have no user stories:

| # | Missing Story | Impact |
|---|---|---|
| 1 | Content rejection/regeneration — what happens when human rejects a post? | Creator can't improve |
| 2 | Manual content override — requesting entirely new content for a category | Operator is stuck with AI output |
| 3 | System recovery/retry — manually triggering re-collection or retrying failed posts | No error recovery path |
| 4 | Multi-account awareness — different strategies per account, pausing only one account | EN/JP can't diverge |
| 5 | Content idea submission — suggesting topics to the system | Operator can't influence direction |
| 6 | Outbound engagement visibility — seeing what likes/replies/follows were performed | No transparency |
| 7 | Rule learning transparency — understanding/editing Marc's learned rules | Opaque system behavior |
| 8 | Cost tracking — budget dashboard, spending alerts | "<$350/month" metric unmonitorable |

### 4.13 Launch Criteria Too Vague to Be Testable [MEDIUM]

- **Location**: Section 11
- **Examples**:
  - Phase 1: "Strategist generates a coherent strategy document" — "coherent" is subjective
  - Phase 4: "Real data" is undefined
  - Phase 4: "No manual intervention" contradicts the approval requirement
  - Phase 5: "Zero pipeline failures" is unrealistic (transient API timeouts)
  - Phase 5: "3 consecutive days" autonomous is too short for confidence
- **Fix**: Add measurable, objective criteria for each phase gate.

### 4.14 A/B Testing Methodology Missing [MEDIUM]

- **Location**: Section 3.2, Section 10
- **Quote**: "Determine whether EN or JP market is more viable for AI beauty content (A/B test conclusion)"
- **Problem**: No statistical power analysis, no randomization strategy, no control for external factors. 17 days is too short for statistical significance (typical minimum: 2-4 weeks).
- **Fix**: Either specify a proper A/B methodology or reframe as "qualitative comparison."

### 4.15 API Rate Limit Budget Tighter Than Claimed [MEDIUM]

- **Location**: Section 6.1
- **Quote**: "Scout optimized for ~10,700 reads/month with 30% buffer"
- **Problem**: 10,700 × 1.30 = 13,910. Remaining for all other operations: 1,090 reads. Two accounts with daily operations easily exceed this. The "30% buffer" is the total-to-limit gap, not a true operational buffer.
- **Fix**: Recalculate and present honest buffer numbers.

### 4.16 Missing Risk: Cron Job Overlap / Stalled Pipeline [MEDIUM]

- **Location**: Section 12
- **Problem**: No locking mechanism. No daemon health monitoring. If Telegram Bot crashes at 3 AM, system won't know until 7 AM morning check.
- **8 total missing risks**: Account suspension from AI content policy changes, human availability slippage, Claude Code CLI deprecation, cron overlap, image file mismatch, silent X API changes, Telegram Bot token leak, anomaly detection gap.

### 4.17 Telegram Command Gaps [MEDIUM]

Missing commands: `/recall` (undo post), `/retry` (retry failed), `/add-competitor` and `/remove-competitor` (manage competitor list without editing JSON), batch editing, rate-limit status in `/status`, insights/recommendations command.

### 4.18 No Way to Explicitly Reject Posts [MEDIUM]

- **Location**: Section 9.2
- **Problem**: `rejected` is not a valid status. Rejected posts remain `draft` indefinitely. No explicit rejection mechanism with feedback for regeneration.
- **Fix**: Add `rejected` status with feedback field.

### 4.19 Engagement Rate Definition Ambiguous [LOW]

- **Location**: Section 3.2
- **Quote**: "(likes + RT + replies + quotes) / impressions"
- **Problem**: Unclear if this includes own outbound engagement or only inbound. When impressions are NULL (Playwright failure), formula breaks.

---

## 5. Compliance vs Design Conflicts

These are the most dangerous issues because they risk **account suspension** if implemented as designed.

### 5.1 Automated Likes Are Prohibited [CRITICAL]

- **X Terms**: Automated likes are explicitly banned.
- **Spec Design**: Publisher (Section 3.4, lines 489-495) includes "30/day likes" as a core outbound engagement feature.
- **Spec Section 2.3**: Labels likes as "Safe" in the Hybrid Strategy table.
- **Impact**: If implemented, account suspension is likely.
- **Decision needed**: Remove automated likes entirely, or accept BAN risk.

### 5.2 Automated Follows Risk BAN [CRITICAL]

- **X Terms**: Automated follows carry high BAN risk (classified as "bulk/aggressive" behavior).
- **Spec Design**: Publisher includes "5/day follows" as core functionality.
- **Impact**: Even low-volume automated follows can trigger suspension.
- **Decision needed**: Remove automated follows entirely, or accept BAN risk.

### 5.3 Cold Replies Require Prior Interaction [CRITICAL]

- **X Terms**: Automated replies to users who haven't interacted with the account first are banned.
- **Spec Design**: Section 2.4 is vague about "reactive-only" vs cold outreach.
- **PRD**: Line 117 says "outbound engagement" without clarifying the constraint.
- **Decision needed**: Explicitly define "reactive-only" replies and add enforcement logic.

### 5.4 Playwright Scraping Is Banned [CRITICAL]

- **X Terms**: Browser automation against X violates terms; compliance review says "may result in permanent account suspension."
- **Spec Design**: Playwright is a core component for impression scraping and is included in Phase 0 setup.
- **Spec Section 2.3**: Describes Playwright use as "low-risk" and "minimal risk" — directly contradicts the compliance review's "permanent suspension" assessment.
- **Decision needed**: Remove Playwright entirely (lose impression data), accept BAN risk, or find compliant alternative.

### 5.5 Bot Account Labeling Missing from Spec/PRD [MEDIUM]

- **X Terms**: Automated accounts must be labeled.
- **Status**: Only partially mentioned in Phase 0 Runbook Step 3 ("automation labeling"). Not in spec or PRD account setup procedures.
- **Fix**: Add to Phase 0 spec checklist.

### 5.6 Cross-Account Content Must Be Unique [MEDIUM]

- **X Terms**: Content across multiple accounts must be genuinely unique.
- **Spec/PRD Design**: EN/JP accounts share images, only text differs.
- **Risk**: Shared images could be flagged as coordinated inauthentic behavior.
- **Fix**: Address in Creator's design — ensure visual uniqueness across accounts.

### 5.7 Use Case Description Is Binding [MEDIUM]

- **X Terms**: The use case description submitted to the developer portal is binding.
- **Status**: Phase 0 Runbook Step 3 includes a sample description that mentions "likes, replies" — features that may need to be removed per Issues 5.1 and 5.3. Changing features after submission could itself be a compliance issue.
- **Fix**: Finalize the feature set (including compliance decisions) before writing the use case description.

---

## 6. Recommendations & Action Items

### Before Phase 0 Starts [BLOCKING]

| # | Action | Effort | Blocks |
|---|---|---|---|
| 1 | **Resolve 4 compliance conflicts** — Decide for each: remove feature, accept risk, or find alternative. This decision cascades to spec, PRD, runbook, and use case description. | 1 hour decision + 2-3 hours doc updates | Phase 0 Step 3 (use case description) |
| 2 | **Fix PRD cross-references** — Change v2.1 → v2.3 filename on lines 8, 359, 400 | 10 min | Anyone following PRD |
| 3 | **Delete spec Section 17** — Remove duplicate Risk Management section | 5 min | Document clarity |
| 4 | **Reconcile post frequency** — Pick 4/day (implementation reality) and update header, API calcs | 30 min | API budget accuracy |
| 5 | **Update PRD open questions** — Mark OQ-3, OQ-6, OQ-7 as resolved | 10 min | Decision tracking |
| 6 | **Add compliance review cross-references** to spec and PRD | 15 min | Awareness |
| 7 | **Reconcile `global_rules` format** — JSON or Markdown, not both | 20 min | Implementation |
| 8 | **Fix PRD section numbering** — Resolve dual Section 8 | 10 min | Document navigation |
| 9 | **Reconcile human time commitment** — Pick one number, factor in image generation | 30 min | Realistic expectations |
| 10 | **Resolve Phase count mismatch** — PRD should match spec's 7-phase plan | 20 min | Timeline accuracy |

### Before Phase 1 Starts [HIGH]

| # | Action | Effort |
|---|---|---|
| 11 | **Specify Telegram Bot daemon architecture** — polling vs webhook, Claude invocation, authentication, concurrency | 3-5 hours |
| 12 | **Specify Marc orchestration logic** — decision criteria, failure handling, War Room format | 5+ days |
| 13 | **Define approval flow edge cases** — timeouts, late approval, TTL, rejection mechanism | 2-3 hours |
| 14 | **Add SQLite schema constraints** — PRIMARY KEY, UNIQUE, NULL handling | 1 hour |
| 15 | **Specify OAuth refresh flow** — proactive vs reactive, failure recovery | 2 hours |
| 16 | **Add security hardening checklist** — SSH keys, disable root, encrypted secrets, audit logging | 2 hours |
| 17 | **Add missing user stories** — 8 stories identified in Section 4.12 | 2 hours |
| 18 | **Add concurrency control** — file locks, SQLite WAL mode, cron guard | 2 hours |
| 19 | **Fix runbook bash compatibility** — `${agent^}` doesn't work in zsh on macOS | 15 min |
| 20 | **Add `aiosqlite` to spec deployment deps** | 5 min |

### Before Phase 2 Starts [MEDIUM]

| # | Action | Effort |
|---|---|---|
| 21 | Redesign Publisher per compliance decisions | Depends on compliance resolution |
| 22 | Specify cross-account content uniqueness for EN/JP | 2 hours |
| 23 | Add measurable launch criteria per phase | 2 hours |
| 24 | Extend timeline to 25-30 days with buffer phases | 1 hour |
| 25 | Add missing risk items to PRD (8 identified) | 1 hour |

### Decision Points Requiring Shimpei's Input

| # | Decision | Options | Impact |
|---|---|---|---|
| D1 | **Automated likes** | Remove entirely / Accept BAN risk | Changes Publisher design, API budget, engagement metrics |
| D2 | **Automated follows** | Remove entirely / Accept BAN risk | Changes growth strategy, Publisher design |
| D3 | **Cold replies** | Reactive-only / Accept BAN risk | Changes outbound engagement design |
| D4 | **Playwright scraping** | Remove (lose impressions) / Accept BAN risk / Find alternative | Changes Analyst, Phase 0 setup, VPS requirements |
| D5 | **Use case description wording** | Include likes/replies (risk if removed later) / Exclude from start | Must resolve D1-D3 first |
| D6 | **10K follower target** | Keep as north-star / Adjust to timeline-realistic target | Changes success metrics framing |
| D7 | **Human time commitment** | <30 min (exclude images) / <1 hour (include images) / <2 hours (realistic) | Changes daily workflow design |
| D8 | **Post frequency** | Exactly 4/day / Range 3-5/day | Changes API budget, scheduling |

---

## Appendix: Document Health Summary

| Document | Completeness | Internal Consistency | Cross-Doc Alignment | Implementation Ready? |
|---|---|---|---|---|
| Spec v2.3 | 75% — missing Telegram Bot, OAuth details, Playwright selectors | Low — duplicate section, format conflicts, frequency contradiction | Medium — compliance not reflected | **No** — needs cleanup before Phase 0 |
| PRD v1.0 | 70% — missing user stories, vague criteria, unrealistic timeline | Low — time contradictions, section numbering, phase count | Low — broken spec links, missing compliance reference | **No** — needs updates |
| Compliance Review | 90% — thorough identification of issues | High — internally consistent | Low — not referenced by spec or PRD | **Yes** — but needs to be integrated |
| Phase 0 Runbook | 85% — complete step-by-step with test scripts | Medium — bash compat issue, includes compliance-risky content | Medium — correct spec reference, no PRD link | **Mostly** — fix bash compat, await compliance decisions |
| Context.md | 95% — most comprehensive document | High — internally consistent | High — correctly tracks all decisions | **Yes** — reference quality |
| Framework Analysis | 85% — solid analysis for its purpose | High — internally consistent | N/A — historical reference | **N/A** — historical document |
