# Product Requirements Document (PRD)
# X (Twitter) AI Beauty Growth Agent System

**Document version**: 1.1
**Date**: March 2, 2026
**Author**: Shimpei (Founder & CEO, Amarry Technologies Inc.)
**Status**: Draft
**Related documents**: [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md), [Compliance Review](./x-developer-terms-compliance-review.md)

---

## 1. Executive Summary

Build an autonomous AI agent system that grows AI-generated beauty content accounts on X (Twitter) from 0 to 10,000 followers. The system operates overnight and throughout the day with minimal human intervention — the human's role is limited to morning approval of content and image preparation. A COO agent (Marc) orchestrates five specialist agents, communicates with the human via Telegram, and continuously improves strategy based on performance data.

The system runs two parallel accounts (EN for global market, JP for 日本市場) as an A/B test to determine which language/market yields faster growth for AI beauty content.

---

## 2. Problem Statement

Growing a social media account in the AI beauty niche requires daily, consistent effort across multiple dimensions: competitor research, strategy formulation, content creation, posting at optimal times, outbound engagement, and performance analysis. This is a full-time job that doesn't scale — doing it manually for one account is tedious, doing it for two simultaneously is impractical.

The opportunity is to automate 90%+ of this workflow using AI agents, reducing the human's role to creative judgment (approving content, preparing images) while the system handles everything else autonomously — including learning from its own performance data and adapting strategy over time.

---

## 3. Goals & Success Metrics

### 3.1 Primary Goal

**North-star goal**: 10,000 followers on at least one account (EN or JP).

**Interim milestones**:

| Milestone | Target Followers | Timeframe |
|---|---|---|
| Early traction | 500 | Week 2 |
| Growth validation | 1,000 | Month 1 |
| Scaling | 5,000 | Month 3 |
| North-star | 10,000 | As fast as possible |

### 3.2 Success Metrics

| Metric | Target | Measurement Method | Timeframe |
|---|---|---|---|
| Follower count | 10,000 on either EN or JP | X API `public_metrics` | As fast as possible |
| Follower growth rate | >100 followers/day sustained | Account metrics DB (daily delta) | After Week 2 |
| Engagement rate | >3% average across posts | Inbound only: (likes + RT + replies + quotes) / impressions. When impressions are NULL (Basic plan), use API-only proxy: (likes + RT + replies + quotes) / followers | Rolling 7-day |
| Post consistency | 3-5 posts/day per account, zero missed days | Pipeline logs | Ongoing |
| System uptime | >95% pipeline completion rate | Marc's execution logs | Ongoing |
| Human time spent | <1 hour/day (including image generation) | Self-reported | After Phase 5 launch |
| Monthly cost | <$350/month | Billing records | Ongoing |

**Cost breakdown**: X API Basic $200/mo + Claude Max $100/mo = **$300/mo during development**. Add Vultr VPS $12/mo at Phase 5 = **$312/mo in production**.

### 3.3 Secondary Goals

- Determine whether EN or JP market is more viable for AI beauty content (A/B test conclusion)
- Build a reusable multi-agent framework that can be adapted to other niches/accounts
- Accumulate a proprietary dataset of AI beauty content performance metrics
- Validate the Claude Code + cron + Telegram architecture for autonomous agent systems

### 3.4 Non-Goals (Explicit Scope Exclusions)

- Video content (static images only for v1)
- Multi-platform posting (X only — no Instagram, TikTok, etc.)
- Monetization (no affiliate links, sponsorships, or product sales in v1)
- AI image generation (human prepares images using external tools; the system only provides prompts)
- Full automation without human approval (human-in-the-loop is mandatory in v1)
- Real-time trend-jacking (overnight batch pipeline, not real-time reaction)

---

## 4. User Personas & Workflows

### 4.1 Primary User: Shimpei (Account Owner / Operator)

**Context**: Solo founder running this as a side project alongside Amarry Technologies. Based in Japan (JST timezone). Available for up to 1 hour in the morning (7-9 AM JST window) for content approval and image preparation.

**Daily workflow**:

1. **7:00 AM** — Receive morning brief from Marc via Telegram. Review yesterday's performance, today's content plan, and strategy updates.
2. **7:00-9:00 AM** — Review drafted posts. Approve via `/approve` command (or selectively with `/approve 1,3,5`). Use image prompts to generate AI images with Midjourney/Stable Diffusion. Place images in `media/pending/` directory.
3. **Throughout the day** — Optionally check Telegram for alerts. No action needed unless Marc escalates something.
4. **23:30** — Optionally review daily report from Marc. No action needed.

**Key needs**:
- Minimal daily time commitment (<1 hour)
- Clear, actionable Telegram reports (not information overload)
- Confidence that the system won't damage account reputation (spam, low-quality content, BAN risk)
- Ability to override/pause the system at any time via Telegram commands
- Visibility into what's working and what isn't (data-driven, not guesswork)

### 4.2 Secondary User: Marc (COO Agent)

While Marc is an AI agent, it's useful to define his "user experience" since he interacts with every other component.

**Marc's workflow**:
1. Wake up at 0:30 AM via cron
2. Run health checks on all dependencies (X API, Playwright, SQLite, disk space)
3. Invoke Scout → validate output → invoke Strategist → validate → invoke Creator → validate
4. Run War Room review (lite at 2:30 AM, full at 6:00 AM)
5. Send morning brief at 7:00 AM
6. Wait for human approval → route to Publisher throughout the day
7. Trigger Analyst at scheduled times
8. Send daily report at 23:30
9. Run retrospective at 23:45 → update rules

**Marc's needs**:
- Reliable access to all agent outputs (filesystem-based shared state)
- Clear success/failure signals from each agent
- Ability to retry, skip, or escalate based on error type
- Persistent memory of rules learned from past failures (CLAUDE.md / global_rules)

---

## 5. Product Scope & Features

### 5.1 Core Features (MVP — Phases 0-4)

| # | Feature | Description | Priority |
|---|---|---|---|
| F1 | Competitor intelligence | Daily automated scraping of 10+ competitor accounts via X API. Viral post detection, engagement pattern analysis, follower tracking. | P0 |
| F2 | Strategy engine | Data-driven daily strategy updates. Optimal posting times, content mix ratios, hashtag strategy, outbound engagement policy. | P0 |
| F3 | Content generation | AI-drafted post text (EN + JP) with image prompts. Reply templates for outbound engagement. | P0 |
| F4 | Automated posting | X API-based post publishing with image upload. Scheduled at optimal times. Rate-limit-aware. | P0 |
| F5 | Outbound engagement | Automated likes, replies, and follows via X API. Human-like pacing with random delays. Conservative daily limits. ⚠️ See compliance review — automated likes, follows, and cold replies carry X Terms risk. Risk accepted. | P0 |
| F6 | Metrics collection | Post performance tracking (public_metrics via API + impressions via Playwright). Account-level daily snapshots. SQLite storage. | P0 |
| F7 | COO orchestration | Marc manages the full pipeline: agent sequencing, dependency management, error handling, War Room reviews. *Note: Detailed Marc orchestration specification to be developed during Phase 1 implementation.* | P0 |
| F8 | Telegram interface | Morning briefs, daily reports, instant alerts. Command processing (/approve, /status, /pause, /edit, /strategy). | P0 |
| F9 | Human approval flow | Draft → approve → media_ready → posted lifecycle. No content goes live without explicit human approval. | P0 |
| F10 | EN/JP A/B testing | Parallel accounts with comparative analytics to determine market fit. | P0 |

### 5.2 Post-Launch Features (Phase 5+)

| # | Feature | Description | Priority |
|---|---|---|---|
| F11 | Auto-posting mode | Option to skip human approval for posts that meet quality thresholds (e.g., strategy alignment score >90%). | P1 |
| F12 | Advanced A/B testing | Systematic variable testing (hashtag count, CTA style, posting time, image style) with statistical significance tracking. | P1 |
| F13 | Follower quality analysis | Track follower-to-engagement ratio, identify bot followers, measure audience quality. | P1 |
| F14 | CLAUDE.md memory system | Integrate Claude Code's native memory hierarchy for agent behavioral instructions, replacing JSON-based rules. | P1 |
| F15 | Multi-niche expansion | Adapt the framework for additional content niches beyond AI beauty. | P2 |
| F16 | Cross-platform support | Extend to Instagram, TikTok, or other platforms. | P2 |
| F17 | Monetization layer | Affiliate links, sponsored content tracking, revenue attribution. | P2 |

### 5.3 Feature Dependency Map

```
F1 (Scout) ──▶ F2 (Strategist) ──▶ F3 (Creator) ──▶ F9 (Approval) ──▶ F4 (Publisher)
                     │                                                       │
                     └──────── F5 (Outbound) ◀──────────────────────────────┘
                                    │
F6 (Analyst) ◀─────────────────────┘
     │
     └──▶ F2 (feeds back into next day's strategy)

F7 (Marc) orchestrates all of the above
F8 (Telegram) is Marc's communication channel
F10 (A/B) is a cross-cutting concern across F1-F6
```

---

## 6. System Constraints & Assumptions

### 6.1 Constraints

| Constraint | Impact | Mitigation |
|---|---|---|
| X API Basic plan: 15,000 reads/month | Limits competitor scraping depth | Scout optimized for ~10,700 reads/month with 30% buffer |
| X API Basic plan: no `non_public_metrics` | Cannot get impressions via API | Playwright scrapes own post pages as workaround |
| Claude Code is session-based (not a daemon) | Cannot listen for events; must be cron-triggered | Cron handles scheduling; Telegram Bot runs as separate Python daemon |
| Human timezone (JST) | Approval window is 7-9 AM JST; posts before that must wait | Pipeline runs overnight; first post at 9:00 AM after approval |
| Single-operator system | No team collaboration features needed | All Telegram communication is 1:1 with Shimpei |
| VPS resource limits (2 vCPU / 4 GB) | Playwright + Claude Code may compete for resources | Stagger execution; Playwright only runs during Analyst windows |

### 6.2 Assumptions

- Shimpei will be available for 30-60 minutes daily (7-9 AM JST) for content approval and image preparation
- X API Basic plan pricing and features will remain stable during the project
- AI-generated beauty content will not violate X's terms of service (no policy against AI-generated images as of March 2026)
- Competitor accounts will remain public (private accounts cannot be scraped via API)
- The VPS will have >95% uptime
- Claude Code CLI will remain available and functionally stable
- Telegram Bot API will remain free and available

### 6.3 Dependencies

| Dependency | Type | Risk Level | Fallback |
|---|---|---|---|
| X API v2 (Basic plan) | External service | Medium | Playwright for all operations (higher BAN risk) |
| Claude Code CLI | External tool | Low | Direct Anthropic API calls via Python |
| Telegram Bot API | External service | Low | Email notifications (degraded experience) |
| Playwright + Chromium | Open source tool | Low | Skip impression tracking (use public_metrics only) |
| Midjourney / Stable Diffusion | External tool (human-operated) | Low | Any AI image generation tool |
| VPS provider (Hetzner/Vultr) | Infrastructure | Low | Migrate to another provider |

---

## 7. Agent Design Philosophy

These principles guide how agents are designed in this system. They are derived from lessons learned during the development of Claude Code (source: *"Lessons from Building Claude Code: Seeing like an Agent"*) and apply to both this demo and any future project built on the autonomous agent framework. Full technical details are in the [Technical Specification, Section 14](./x-ai-beauty-spec-v2.3.md).

| Principle | What It Means for This Product | Example |
|---|---|---|
| **Minimal tool count** | Each agent gets only the tools it needs. No "Swiss army knife" agents with access to everything. | Scout has X API read tools only — it can never accidentally post or like. |
| **Structured elicitation** | When the system needs human input, it presents structured options rather than open-ended questions. | Morning brief ends with `/approve`, `/details`, `/approve 1,3,5` — not "what do you think?" |
| **Task-based coordination** | Agents coordinate through a task state file with explicit dependencies, not rigid checklists. Marc can adapt the pipeline at runtime. | If Scout fails, Marc can skip to a cached strategy instead of halting the entire pipeline. |
| **Progressive disclosure** | Agents build their own context incrementally by reading files as needed, rather than receiving everything upfront. | Scout reads yesterday's report only if comparison is needed, not by default. |
| **Revisit tool assumptions** | Weekly review of whether agents' tools and instructions still match their needs as models improve. | If human approval is always "approve all" for 2+ weeks, consider auto-approval. |
| **Add capability without tools** | New abilities are added through skill file updates or subagents before reaching for a new tool. | Adding sentiment analysis to Scout = updated instructions, not a new tool. |

**Design implication for the operator**: These principles mean the system will evolve. Skill files, tool assignments, and even agent boundaries should be treated as living configurations that improve over time based on observed agent behavior.

---

## 8. User Stories

### 8.1 Daily Operations

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| US-01 | Operator | Receive a morning brief on Telegram at 7 AM | I can quickly understand yesterday's performance and today's plan | Brief includes: follower delta, best post metrics, today's post count, action items, strategy highlights |
| US-02 | Operator | Approve all posts with a single `/approve` command | I don't waste time approving posts one by one | All `draft` posts move to `approved` status; Marc confirms via Telegram |
| US-03 | Operator | Selectively approve posts with `/approve 1,3,5` | I can reject posts I don't like | Only specified posts move to `approved`; rejected posts remain `draft` |
| US-04 | Operator | See image prompts for each post | I can generate the right AI images | Content plan includes detailed prompts with tool, style, aspect ratio |
| US-05 | Operator | Place images in a folder and have them auto-associated | I don't need to manually map images to posts | Naming convention `{post_id}.png` in `media/pending/` auto-links to posts |
| US-06 | Operator | Check system status anytime with `/status` | I know if the pipeline is running normally | Returns: last pipeline run time, agent statuses, today's post count, error count |
| US-07 | Operator | Pause all automated activity with `/pause` | I can stop the system immediately if something goes wrong | Publisher halts all posting and outbound; Marc confirms pause; `/resume` to restart |

### 8.2 Strategy & Content

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| US-08 | Operator | See EN vs JP performance comparison | I can decide which market to focus on | Daily report includes side-by-side metrics for both accounts |
| US-09 | Operator | Override strategy via `/strategy "directive"` | I can steer the content direction without editing files | Marc relays directive to Strategist; next content plan reflects the change |
| US-10 | Operator | Edit a specific post via `/edit 3 "new text"` | I can fix content without regenerating the whole plan | Specified post text is updated; Marc confirms the change |
| US-11 | Operator | See which content categories perform best | I can refine the content strategy | Weekly strategy report includes category-level engagement breakdown |

### 8.3 Monitoring & Alerts

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| US-12 | Operator | Be alerted immediately if an account loses >10% followers | I can investigate potential issues (shadowban, controversy) | Marc sends Telegram alert within 5 minutes of Analyst detecting anomaly |
| US-13 | Operator | Be alerted if the pipeline fails | I know the system is down | Marc sends Telegram alert with error type, affected agent, and recommended action |
| US-14 | Operator | See a daily error summary | I can track system reliability over time | Daily report includes error count by type and resolution method |
| US-15 | Operator | Be notified if API rate limits are approaching | I can avoid unexpected service interruption | Marc warns when usage exceeds 80% of monthly allocation |

### 8.4 System Administration

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| US-16 | Operator | Add/remove competitor accounts without touching code | I can update the competitive landscape easily | Edit `config/competitors.json`; Scout picks up changes on next run |
| US-17 | Operator | View historical performance data | I can track progress over weeks/months | SQLite database retains all metrics; queryable via Analyst reports |
| US-18 | Operator | Back up system data | I don't lose historical data if VPS fails | Automated daily backup of SQLite + config to cloud storage |

---

## 9. Telegram Command Specification

| Command | Arguments | Description | Agent Routed To |
|---|---|---|---|
| `/approve` | None | Approve all draft posts for today | Marc (updates status directly) |
| `/approve` | `1,3,5` (post indices) | Approve specific posts only | Marc (updates status directly) |
| `/edit` | `<index> "<new text>"` | Edit a specific post's text | Creator (via Marc) |
| `/status` | None | Current pipeline state & health | Marc (responds directly) |
| `/pause` | None | Halt all automated posting & outbound | Marc → Publisher |
| `/resume` | None | Resume after pause | Marc → Publisher |
| `/strategy` | `"<directive>"` | Override/adjust strategy | Marc → Strategist |
| `/details` | None | Full today's content plan | Marc (responds directly) |
| `/metrics` | Optional: `en` or `jp` | Latest performance metrics | Marc (queries SQLite) |
| `/competitors` | None | Current competitor list & stats | Marc (reads Scout data) |
| `/help` | None | List available commands | Marc (responds directly) |

---

## 10. Content Lifecycle

### 10.1 Post Status Definitions

| Status | Definition | Transition Trigger | Owner |
|---|---|---|---|
| `draft` | Post text and image prompt created, awaiting human review | Creator completes content plan | Creator |
| `approved` | Human has approved the post text | `/approve` command via Telegram | Human → Marc |
| `media_ready` | Approved post + corresponding image file exists in `media/pending/` | Human places image file; Marc detects it | Human → Marc |
| `scheduled` | Post is queued for publishing at its designated time slot | Marc confirms `media_ready` and time slot is upcoming | Marc |
| `posted` | Post has been published to X via API | Publisher successfully calls POST /2/tweets | Publisher |
| `measured` | Post metrics have been collected (at least one snapshot) | Analyst runs 6h or 24h collection | Analyst |
| `rejected` | Human explicitly rejected the post during review | Human declines via selective `/approve` (post not included) or explicit rejection | Human → Marc |
| `failed` | Post could not be published after max retries | Publisher exhausts retry attempts | Publisher → Marc (escalation) |

### 10.2 Edge Cases

| Scenario | Behavior |
|---|---|
| Human doesn't approve by 9:00 AM | Marc sends reminder at 9:00 AM. Posts wait. No automatic approval ever. |
| Human approves but doesn't provide images | Posts remain `approved`. Marc sends reminder at 9:30 AM listing missing images. |
| Image file naming doesn't match post ID | Marc alerts human with expected filename format. Post waits. |
| Human approves after the scheduled time slot | Marc reschedules to the next available slot. |
| Human sends `/pause` mid-day | Publisher immediately stops. Remaining posts are deferred to tomorrow (or next `/resume`). |
| Post fails after 3 retries | Status set to `failed`. Marc escalates to human with error details. |

---

## 11. Data & Privacy

### 11.1 Data Collected

| Data Type | Source | Storage | Retention |
|---|---|---|---|
| Competitor public posts | X API (public data) | `data/scout_report_*.json` | 90 days (archived) |
| Own post metrics | X API + Playwright | SQLite `post_metrics` table | Indefinite |
| Account follower counts | X API | SQLite `account_metrics` table | Indefinite |
| Outbound engagement log | System-generated | SQLite `outbound_log` table | Indefinite |
| Pipeline execution logs | System-generated | `logs/` directory | 30 days |
| API tokens & credentials | User-provided | `config/accounts.json` (gitignored) | Until rotated |

### 11.2 Privacy Considerations

- All competitor data is sourced from public X posts via official API — no private data is accessed
- Playwright only accesses our own account pages — no third-party scraping
- API tokens stored locally on VPS, never transmitted to third parties
- No personal data of X users is stored beyond public handles and public_metrics
- SQLite database lives on VPS only; backups should be encrypted

---

## 12. Launch Criteria

### 12.1 Phase-by-Phase Go/No-Go

| Phase | Complete When | Go/No-Go Criteria |
|---|---|---|
| Phase 0 (Environment) | All infrastructure is set up and verified | VPS running, Claude Code authenticated, X API tokens working, Telegram Bot responding, Playwright can log into both accounts |
| Phase 1 (Intelligence) | Scout + Strategist produce valid outputs | Scout report contains data for 10+ competitors; Strategist generates a coherent strategy document |
| Phase 2 (Content) | Creator produces approvable content via Telegram | Creator generates 4 posts per account; Morning brief arrives on Telegram; `/approve` command works |
| Phase 3 (Publishing) | Posts go live on X | At least 1 post successfully published per account via API; Image upload works; Outbound like/reply/follow works |
| Phase 4 (Analytics) | Full pipeline runs end-to-end | Analyst collects metrics for published posts; Daily report includes real data; No manual intervention needed beyond approval |
| Phase 5 (VPS Deployment) | System deployed and operational on VPS | All API credentials work from VPS; cron installed; health check passes |
| Phase 6 (Autonomous) | System runs autonomously for 3 consecutive days | Zero pipeline failures; All scheduled posts published; Metrics collected; Reports delivered on time |

### 12.2 Production Launch Checklist

- [ ] Full pipeline runs for 3 consecutive days without critical errors
- [ ] Morning brief and daily report arrive on time and contain accurate data
- [ ] All Telegram commands work correctly
- [ ] Rate limit management prevents any API limit breaches
- [ ] Error escalation notifications work for all error types
- [ ] EN and JP accounts are properly isolated (no cross-posting)
- [ ] Follower anomaly detection works (tested with mock data)
- [ ] SQLite backup mechanism is in place
- [ ] `global_rules.md` contains at least 5 learned rules from test runs
- [ ] Human can complete daily workflow in <1 hour

---

## 13. Risks & Mitigation

### 13.1 Product Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| AI beauty content doesn't gain traction on X | Medium | High — project fails to reach 10K | A/B test EN vs JP quickly; pivot content style based on data within 2 weeks |
| X changes API pricing or features | Low | High — cost increase or capability loss | Monitor X developer announcements; Playwright fallback for critical features |
| Account gets shadowbanned or suspended | Low | Critical — total loss of progress | Conservative engagement limits; all operations via official API; avoid aggressive follow/unfollow |
| Content quality is insufficient | Medium | Medium — slow growth | Human approval prevents bad content from publishing; strategy engine adapts based on performance data |
| Competitor landscape shifts | Low | Low — strategy becomes stale | Scout runs daily; Strategist adapts; human can add/remove competitors anytime |

### 13.2 Technical Risks

See [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md), Section 8 (Risk Management) for infrastructure and system-level risks.

### 13.3 X Developer Terms Compliance

A full compliance review of X Developer Terms against this project's design is documented in [`x-developer-terms-compliance-review.md`](./x-developer-terms-compliance-review.md). Summary of 7 issues identified:

- **4 Critical (🔴)**: Automated likes prohibited (Issue 1), automated follows risk (Issue 2), cold outbound replies prohibited (Issue 3), Playwright scraping banned (Issue 4)
- **3 Medium (🟡)**: Bot account labeling required (Issue 5), cross-account content uniqueness (Issue 6), use case description is binding (Issue 7)

**Decision**: Risk accepted for all 4 critical issues. Implement with awareness; monitor for enforcement changes. Each issue is scheduled for detailed review during the relevant implementation phase (see compliance review for schedule).

---

## 14. Timeline

| Phase | Duration | Calendar (from project start) | Key Deliverable |
|---|---|---|---|
| Phase 0: Environment Setup | 2 days | Day 1-2 | All infrastructure operational (local) |
| Phase 1: Intelligence Layer | 3 days | Day 3-5 | Scout + Strategist + Marc foundation |
| Phase 2: Content Layer | 3 days | Day 6-8 | Creator + Telegram command flow working |
| Phase 3: Publishing Layer | 4 days | Day 9-12 | Posts going live on X via API |
| Phase 4: Analytics Layer | 4 days | Day 13-16 | Full pipeline end-to-end (2-3 day manual test) |
| Phase 5: VPS Deployment | 2 days | Day 17-18 | System deployed to VPS with cron |
| Phase 6: Autonomous Operation | Day 19+ | Day 19-25+ | 3-day autonomous validation, then ongoing |
| **Total to autonomous** | **~25 days** (with buffer) | | |

> Phases 0-4 run on your local machine. Phase 5 deploys to VPS. Phase 6 is autonomous operation. See [Technical Specification](./x-ai-beauty-spec-v2.3.md) Section 7 for detailed phase descriptions.

---

## 15. Open Questions

| # | Question | Impact | Status |
|---|---|---|---|
| OQ-1 | Which AI image generation tool will be primary (Midjourney, Stable Diffusion, Flux, etc.)? | Affects image prompt format in Creator agent | Open |
| OQ-2 | What is the initial competitor list (10+ accounts)? | Blocks Phase 1 Scout testing | Open |
| OQ-3 | Should we create fresh X accounts or use existing ones? | Affects Phase 0 setup and early growth dynamics | **Resolved**: Use existing accounts |
| OQ-4 | What is the monthly budget ceiling if costs exceed estimates? | Determines whether to continue at $350+ | Open |
| OQ-5 | Should the system operate on weekends/holidays, or weekdays only? | Affects cron scheduling and human availability | Open |
| OQ-6 | VPS provider preference (Hetzner, Vultr, DigitalOcean, etc.)? | Affects Phase 5 deployment | **Resolved**: Vultr Tokyo ($12/mo) |
| OQ-7 | Claude subscription tier (Pro $20 vs Max $100)? Token budget per day? | Affects monthly cost and agent capability | **Resolved**: Claude Max ($100/mo) |
| OQ-8 | Backup destination for SQLite + config (S3, Google Drive, local)? | Affects Phase 4 backup implementation | Open |

---

## 16. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | March 1, 2026 | Shimpei | Initial PRD |
| 1.1 | March 2, 2026 | Shimpei | Document review fixes: fixed broken spec v2.1 references → v2.4, resolved OQ-3/OQ-6/OQ-7, updated timeline to 7 phases (~25 days), fixed section numbering (duplicate Section 8), standardized human time to "<1 hour/day", added compliance review reference (Section 13.3), reframed 10K target as north-star with interim milestones, added cost breakdown, added F5 compliance note, added F7 Marc note, added `rejected` post status, clarified engagement rate definition with NULL/proxy formula, added revision history |

---

*This PRD defines what to build and why. For how to build it, see the [Technical Specification v2.4](./x-ai-beauty-spec-v2.3.md).*
