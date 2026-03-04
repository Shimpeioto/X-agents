# Phase 4 Product Requirements — Analyst + Manual Metrics + War Room Upgrade

**Document version**: 1.0
**Date**: March 4, 2026
**Status**: Draft
**Phase**: 4 of 6 (Days 13-16)
**Parent document**: [Product Requirements Document v1.1](./x-ai-beauty-prd-v1.md)
**Technical companion**: [Phase 4 Technical Specification](./phase-4-spec.md)

---

## 1. Executive Summary

Phase 4 builds the **measurement layer** — the feedback loop that transforms the pipeline from "post and hope" to "post, measure, and adapt."

Phases 1-3 established the intelligence pipeline (Scout + Strategist), content creation (Creator), human approval (Telegram bot), and live posting (Publisher). **8 real tweets have been posted.** But without measurement, the system is flying blind — there's no way to know whether the strategy is working, which content categories perform best, or whether the accounts are growing.

Phase 4 delivers three capabilities:

1. **Automated Metrics Collection (Analyst)**: A new Python agent that batch-fetches engagement data (likes, retweets, replies, quotes, bookmarks) for all posted tweets via X API, takes daily account snapshots (followers, following), calculates growth deltas, and stores everything in SQLite for historical analysis.

2. **Manual Impression Input (3 Methods)**: Since the X API Basic plan does not provide impression data, operators can input impressions through Telegram commands, analytics screenshots (parsed by Claude Vision), or CSV/JSON file imports.

3. **Performance-Driven Decision Making**: Marc's War Room upgrades from simple consistency checks to scored quality evaluation (0-100), follower anomaly detection (>10% change alerts), and daily reports with real engagement data — closing the feedback loop between what we post and how it performs.

**Key change from parent spec**: Playwright-based impression scraping has been removed entirely due to compliance risk. Impressions are collected manually only.

**Prerequisite**: Phases 1-3 must be complete. At least one day of posted tweets must exist for Analyst to collect metrics.

---

## 2. Goals & Success Criteria

### 2.1 What Phase 4 IS Measuring

Phase 4 is the first phase that measures **our own performance**. Phases 1-3 measured competitors only (Scout) and validated outputs structurally. Phase 4 introduces own-account metrics: engagement data, follower growth, and content quality scores.

### 2.2 Phase 4 Goals

| # | Goal | Why It Matters |
|---|---|---|
| G1 | Collect engagement data for all posted tweets automatically | Without knowing how posts perform, strategy adjustments are guesswork |
| G2 | Accumulate historical metrics in SQLite for trend analysis | Single-day snapshots are less useful than trends over time — need historical data to see what's working |
| G3 | Enable manual impression input through 3 methods | X API Basic plan doesn't provide impressions, but operators can get them from X Analytics UI |
| G4 | Score content quality with a repeatable rubric (0-100) | Subjective quality assessment is inconsistent. A rubric makes quality measurable and improvable. |
| G5 | Detect follower anomalies automatically | A sudden follower drop could indicate a problem (content issue, shadow ban). Early detection enables faster response. |
| G6 | Validate the full 6-agent pipeline end-to-end | Before deploying to VPS (Phase 5), the entire system must be proven reliable over multiple consecutive days |

### 2.3 Success Criteria

| Criterion | Metric | Target |
|---|---|---|
| Metrics coverage | Posted tweets with collected metrics | 100% of posted tweets have API metrics within 24h |
| Account snapshots | Daily snapshots with follower delta | Both accounts have daily snapshots with non-NULL `followers_change` by Day 2 |
| Manual input | At least 1 method operational | Impressions input via Telegram or CSV import works |
| War Room scoring | Content plans scored | Both accounts scored 0-100 with rubric breakdown |
| Anomaly detection | Alert fires on threshold breach | Simulated >10% drop triggers Telegram alert |
| E2E reliability | Consecutive successful runs | 2+ days of full pipeline (all 6 agents) without failure |
| SQLite integrity | Data stored correctly | `validate.py analyst_metrics` passes for all test days |

### 2.4 Design Principle: Measurement Closes the Loop

Without measurement, the pipeline is an open loop — it produces content based on competitor analysis but never learns from its own results. Phase 4 closes this loop:

```
Scout → Strategist → Creator → Publisher → Analyst → (back to Strategist)
                                                           ↑
                                                     Daily Report
                                                     (human review)
```

**Note**: Phase 4 closes the loop through the **human operator** (daily report → human judgment → strategy input). Automated strategy adaptation from own metrics is a Phase 5+ capability.

| Principle | What It Means |
|---|---|
| **Measure what matters** | Engagement rate without impressions is a proxy. Manual impression input bridges the gap until a better solution exists. Don't over-index on proxy metrics. |
| **Historical data is the real asset** | SQLite isn't just storage — it's the foundation for trend analysis, strategy optimization, and ROI measurement in later phases. |
| **Quality scoring must be calibrated** | The War Room rubric (Section 4.5 of spec) will likely need tuning after real-world usage. The first calibration is a starting point, not a final answer. |

---

## 3. Features in Scope (Phase 4 Only)

### F6: Metrics Collection (Analyst)

**Source**: PRD Feature F6 (Engagement Metrics)

| Aspect | Phase 4 Scope |
|---|---|
| Post metrics | Likes, retweets, replies, quotes, bookmarks for all posted tweets |
| Account snapshots | Followers, following, total_posts, followers_change per account per day |
| Collection method | Batch tweet lookup via X API v2 (automated) |
| Impressions | Manual input only — 3 methods (Telegram, screenshot, CSV/JSON) |
| Storage | SQLite (`data/metrics_history.db`) + JSON summaries |
| Frequency | 2 runs/day (1h and 24h after posting), plus manual triggers |
| NOT in Phase 4 | Automated impressions, Playwright scraping, engagement prediction |

**What it delivers to the operator**: Automated daily data on how every posted tweet performs — engagement numbers, follower growth, and the beginning of a historical dataset for trend analysis.

### F6a: Manual Impression Input

**Source**: New feature — addresses the gap left by removing Playwright

| Aspect | Phase 4 Scope |
|---|---|
| Telegram `/metrics` | View today's summary or input metrics inline (e.g., `/metrics EN_20260304_01 impressions=5000`) |
| Screenshot parsing | Send X Analytics screenshot to Telegram bot → Claude Vision extracts metrics → confirm to save |
| CSV/JSON import | `python3 scripts/analyst.py import --file data/manual.csv` — bulk import for operators who prefer file-based workflow |
| NOT in Phase 4 | Automated import from X Analytics export, scheduled reminders to input impressions |

**What it delivers to the operator**: Three flexible ways to add impression data that the API doesn't provide, bridging the gap until a more automated solution becomes available.

### F7a: War Room Full Scoring

**Source**: PRD Feature F7 (Quality Assurance)

| Aspect | Phase 4 Scope |
|---|---|
| Scoring rubric | 6 criteria, 0-100 scale (category match, hashtag compliance, text quality, image variety, reply templates, A/B test) |
| Thresholds | 90-100 excellent, 70-89 good, 50-69 warning, <50 poor |
| Action on low score | Telegram alert for scores <50, warnings logged for 50-69 |
| NOT in Phase 4 | Historical score trends, automated Creator re-runs on low scores, scoring calibration dashboard |

**What it delivers to the operator**: A consistent, repeatable measure of content quality — no more subjective "does this look good?" assessments.

### F7b: Daily Report with Metrics

**Source**: Extension of Phase 3's Telegram reporting

| Aspect | Phase 4 Scope |
|---|---|
| Report contents | Account growth, post performance (engagement per post), outbound summary, War Room scores |
| Delivery | Telegram message from Marc |
| Frequency | Once per day, after Analyst collection |
| NOT in Phase 4 | Weekly/monthly trend reports, comparative analysis with competitor metrics |

**What it delivers to the operator**: A single daily message with everything you need to know about how the accounts performed today.

### F7c: Follower Anomaly Detection

**Source**: New feature — proactive monitoring

| Aspect | Phase 4 Scope |
|---|---|
| Threshold | >10% change (positive or negative) in follower count |
| Alert | Telegram message with change details and percentage |
| NOT in Phase 4 | Configurable thresholds, trend-based anomaly detection, automated investigation |

**What it delivers to the operator**: Early warning if something unusual happens to follower counts — whether it's a problem (shadow ban, content issue) or an opportunity (viral post, media mention).

### F11: Outbound Log Migration (JSON → SQLite)

**Source**: Technical debt — preparing for historical analysis

| Aspect | Phase 4 Scope |
|---|---|
| Migration approach | Dual-write — Publisher writes to both JSON and SQLite |
| JSON format | Unchanged (backward compatible) |
| SQLite | New `timestamp` column added to existing `outbound_log` table |
| NOT in Phase 4 | Full migration of historical JSON logs to SQLite, JSON deprecation |

**What it delivers to the operator**: Outbound engagement data in a queryable database, alongside the existing human-readable JSON.

### F12: Validation Extensions

**Source**: Extension of existing validation framework

| Aspect | Phase 4 Scope |
|---|---|
| New modes | `analyst` (8 checks on summary JSON) + `analyst_metrics` (6 checks on SQLite) |
| Existing modes | Unchanged — backward compatible |
| NOT in Phase 4 | Validation analytics (which rules fire most), auto-simplification |

---

## 4. Features NOT in Scope

Explicitly excluded from Phase 4 to prevent scope creep:

| Feature | Phase | Why Not Now |
|---|---|---|
| **Cron scheduling** | Phase 5 | Pipeline still triggered manually. VPS deployment enables cron. |
| **VPS deployment** | Phase 5 | Development is local-first. Phase 4 validates the system before deployment. |
| **`/edit`, `/strategy`, `/competitors` commands** | Phase 4+ | Lower priority than measurement. Can be added incrementally. |
| **Playwright impression scraping** | Removed | Compliance risk. Manual input is safer and sufficient. |
| **Automated impressions** | Removed | No safe automated method available for Basic plan. |
| **Posting time optimization** | Phase 5+ | Requires historical data (which Phase 4 starts collecting). |
| **Strategy auto-adaptation from own metrics** | Phase 5+ | Strategist will eventually use Analyst data, but human review comes first. |

---

## 5. User Stories (Phase 4)

### 5.1 Operator Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| P4-01 | Operator | See engagement metrics for every posted tweet | I know which content performs best | Analyst summary shows likes/retweets/replies for all posted tweets |
| P4-02 | Operator | Track follower growth day-over-day | I can measure overall account health | `account_metrics` table shows daily follower counts with delta |
| P4-03 | Operator | Input impression data via Telegram | I can add data the API doesn't provide without leaving the chat | `/metrics EN_20260304_01 impressions=5000` saves to SQLite |
| P4-04 | Operator | Send an analytics screenshot and have it parsed | I can quickly input metrics from X Analytics without typing numbers | Screenshot → Claude Vision → parsed metrics → confirm → saved |
| P4-05 | Operator | Bulk-import metrics from a CSV file | I can catch up on historical data efficiently | `analyst.py import --file data/manual.csv` imports all rows |
| P4-06 | Operator | See a content quality score (0-100) for each day's plans | I have an objective measure of Creator output quality | War Room scores both accounts against the rubric |
| P4-07 | Operator | Be alerted if followers drop >10% | I can investigate potential issues quickly | Telegram anomaly alert with exact numbers and percentage |
| P4-08 | Operator | Receive a daily report with real engagement data | I can review performance in one message | Telegram daily report includes actual metrics, not placeholders |
| P4-09 | Operator | Query historical metrics from SQLite | I can analyze trends over time | `db_manager.get_account_metrics_range()` returns correct data |

### 5.2 System Stories (for Phase 5 readiness)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| P4-10 | Strategist agent (Phase 5+) | Have historical engagement data in SQLite | I can factor own-account performance into strategy recommendations |
| P4-11 | Marc agent (Phase 5) | Have validated metrics collection proven over 2+ days | I can safely schedule this via cron without manual supervision |
| P4-12 | Analyst agent (future) | Have a clean SQLite schema with WAL mode | I can support concurrent reads from multiple agents without lock contention |

---

## 6. Exit Criteria

**Go/no-go checklist for Phase 5 (VPS deployment)**:

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 1 | Analyst collects post metrics for both accounts automatically | `SELECT COUNT(*) FROM post_metrics WHERE date(measured_at) = date('now')` returns > 0 for both accounts | [ ] |
| 2 | Account snapshots include follower change by Day 2 | `SELECT followers_change FROM account_metrics WHERE account='EN' ORDER BY date DESC LIMIT 1` returns non-NULL | [ ] |
| 3 | Summary JSON passes validation for both accounts | `python3 scripts/validate.py analyst data/metrics_{date}_{account}.json` → PASS | [ ] |
| 4 | SQLite integrity validation passes | `python3 scripts/validate.py analyst_metrics data/metrics_history.db` → PASS | [ ] |
| 5 | At least 1 manual metrics method works end-to-end | Verify impression value in SQLite after Telegram `/metrics` or CSV import | [ ] |
| 6 | War Room scores content plans for both accounts | Pipeline state shows `war_room` task with scores in notes | [ ] |
| 7 | Follower anomaly detection fires on simulated data | Telegram receives alert with correct numbers after simulated >10% drop | [ ] |
| 8 | Daily report includes real data (not placeholders) | Telegram daily report shows actual engagement numbers from Analyst | [ ] |
| 9 | Outbound actions in both JSON and SQLite | Same action count in `outbound_log_{date}.json` and `SELECT COUNT(*) FROM outbound_log WHERE date = ?` | [ ] |
| 10 | All 6 agents run in sequence without errors | Full pipeline: Scout → Strategist → Creator → Publisher → Analyst → Marc report completes with exit 0 | [ ] |
| 11 | At least 2 consecutive E2E days completed | Dated files exist in `data/` for 2+ consecutive days, all pipeline states show `status: completed` | [ ] |
| 12 | All validation modes pass | All `validate.py` modes (scout, strategist, cross, creator, creator_cross, publisher, publisher_rate_limits, analyst, analyst_metrics) return PASS | [ ] |

---

## 7. Risks Specific to Phase 4

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Deleted tweets break batch lookup | Low | Low — graceful handling | Batch response omits deleted tweets. Analyst logs warning and skips. Edge cases covered in Section 10.1 of spec. |
| Claude Vision misreads screenshots | Medium | Low — human confirms | `/confirm` flow lets operator review parsed data before saving. Vision errors are caught before DB writes. |
| Anthropic API key management | Low | Medium — screenshot feature breaks | Check `ANTHROPIC_API_KEY` env var first (already set for Claude Code), fallback to `config/accounts.json`. Clear error message if missing. |
| SQLite concurrency issues | Low | Medium — data loss | WAL mode handles concurrent reads and writes. Publisher and Analyst never write the same table simultaneously. Bot writes are serialized by Telegram's update handling. |
| Manual impression input becomes a burden | Medium | Medium — data gaps | Provide 3 methods (Telegram, screenshot, CSV) so operator can choose the least friction path. Phase 5+ can explore automated alternatives. |
| War Room scoring calibration is off | Medium | Low — scores misleading | Initial rubric is a starting point. After 10+ days, review score distribution and adjust weights. Track which criteria deduct the most points. |
| Follower anomaly threshold too sensitive | Low | Low — alert fatigue | 10% is a conservative threshold. If false positives occur, increase to 15-20%. First-day skip avoids false alarm on initial collection. |

---

## 8. Timeline

### 8.1 Day-by-Day Plan

| Day | Calendar | Focus | Deliverables |
|---|---|---|---|
| **Day 13** | Day 13 from project start | Analyst core + DB upgrades + X API batch + validation | `scripts/analyst.py` (collect + summary), `scripts/db_manager.py` (insert/query functions, WAL mode, migration), `scripts/x_api.py` (get_tweets_batch), `scripts/validate.py` (analyst + analyst_metrics modes), Tests 1-8 pass |
| **Day 14** | Day 14 from project start | Manual metrics input (3 methods) | Telegram `/metrics` command, photo handler + Claude Vision integration, `/confirm` + `/cancel` flow, CSV/JSON import in analyst.py, Tests 9-14 pass |
| **Day 15** | Day 15 from project start | War Room + daily report + anomaly + outbound migration | Follower anomaly detection, Marc War Room rubric scoring, daily report with real data, Publisher dual-write to SQLite, `agents/marc.md` updated, `agents/analyst.md` completed, Tests 15-18 pass |
| **Day 16+** | Days 16-18 from project start | End-to-end testing | 2-3 consecutive full pipeline days (Scout → Strategist → Creator → approve → Publisher → Analyst → Daily Report). Tests 19-21 pass. All exit criteria verified. |

---

## 9. Feature-to-Spec Mapping

Traceability from PRD features to Technical Specification deliverables:

| PRD Feature | Spec Section | Files |
|---|---|---|
| F6: Metrics Collection (Analyst) | Spec 3.1, 5.1 | `scripts/analyst.py`, `scripts/db_manager.py`, `scripts/x_api.py` |
| F6a: Manual Impression Input | Spec 4.4, 5.4 | `scripts/telegram_bot.py`, `scripts/analyst.py` (import) |
| F7a: War Room Full Scoring | Spec 3.2, 4.5, 5.6 | `agents/marc.md` (Step 11 replacement) |
| F7b: Daily Report with Metrics | Spec 3.2 | `agents/marc.md` (Step P8) |
| F7c: Follower Anomaly Detection | Spec 3.2 | `agents/marc.md` (Step P8) |
| F11: Outbound Log Migration | Spec 3.3, 5.2 | `scripts/publisher.py`, `scripts/db_manager.py` |
| F12: Validation Extensions | Spec 5.5 | `scripts/validate.py` |
| Analyst skill file | Spec 5.7 | `agents/analyst.md` |

---

*Phase 4 Product Requirements v1.0*
*Date: March 4, 2026*
*Parent: [PRD v1.1](./x-ai-beauty-prd-v1.md)*
