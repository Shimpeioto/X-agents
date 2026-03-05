# Phase 5 Product Requirements — Claude Hybrid Agent Conversion

**Document version**: 1.0
**Date**: March 5, 2026
**Status**: Draft
**Phase**: 5 of 7
**Parent document**: [Product Requirements Document v1.1](./x-ai-beauty-prd-v1.md)
**Technical companion**: [Phase 5 Technical Specification](./phase-5-spec.md)

---

## 1. Executive Summary

Phase 5 converts three Python-only agents (Analyst, Scout, Publisher outbound) into **Claude hybrid agents** — "Claude brain, Python hands." Python scripts continue to handle all API calls, rate limiting, and data storage. Claude subagents add intelligence: anomaly detection, reply filtering, contextual engagement, and automated reporting.

This conversion addresses specific, measured deficiencies:
- **Analyst**: Zero interpretation — Marc manually does all analysis (anomaly detection, report composition)
- **Scout**: 36.9% reply contamination in engagement data, hardcoded trending threshold returns zero results, 59 unfiltered new accounts
- **Publisher outbound**: `random.choice(reply_templates)` for replies, always targets `recent_tweets[0]`, no relevance filtering

Phase 5 delivers three capabilities: intelligent daily reports, enriched competitive intelligence, and contextual outbound engagement. No new API credentials, no new infrastructure, no changes to the deterministic post-publishing flow.

---

## 2. Goals & Success Criteria

### 2.1 What Phase 5 IS Measuring

Phase 5 measures the value of adding Claude reasoning to existing data pipelines:
- Does AI-generated analysis match or exceed human manual analysis?
- Does contextual reply selection outperform random selection?
- Does enriched competitive intelligence improve strategy quality?

Phase 5 does NOT measure account growth (too early, too many confounders).

### 2.2 Phase 5 Goals

| # | Goal | Why It Matters |
|---|---|---|
| **G1** | Automate daily report composition | Marc currently reads raw metrics and manually composes Telegram reports — error-prone and slow |
| **G2** | Add anomaly detection to Analyst | 14.3% follower drop on EN (Mar 4) went un-flagged; operator learned about it only by reading raw JSON |
| **G3** | Clean competitive intelligence data | 36.9% of sampled tweets are reply contamination; engagement rates are systematically biased |
| **G4** | Enable contextual outbound engagement | `random.choice` replies feel bot-like; contextual replies build genuine connections |
| **G5** | Establish fallback-first hybrid pattern | Every Claude enhancement must degrade gracefully to Phase 4 behavior if Claude fails |

### 2.3 Success Criteria

| Criterion | Metric | Target |
|---|---|---|
| **Report quality** | Daily report covers followers, engagement, categories, A/B tests, outbound | All 5 sections present in `daily_report` JSON |
| **Anomaly detection** | Known -14.3% EN follower drop is caught | `anomaly: true` with correct percentage |
| **Reply contamination flagged** | Scout analysis identifies @reply tweets | `reply_contamination_rate > 0` in analysis |
| **Scout backward compatibility** | Strategist consumes enriched scout report without errors | Full pipeline passes all existing validation |
| **Contextual replies** | Publisher replies reference target tweet content | `reasoning` field is non-empty for every reply; manual review of 3+ replies confirms relevance to target tweet |
| **Fallback resilience** | All three fallbacks restore Phase 4 behavior | Each fallback tested and verified |
| **No pipeline regression** | Existing pipeline completes as before | Pipeline state `status: "completed"` |

### 2.4 Design Principle: "Claude Brain, Python Hands"

Every Phase 5 feature follows one rule: **Python handles execution (API calls, file I/O, rate limits), Claude handles reasoning (analysis, selection, composition).** This ensures:
- Deterministic execution paths (Python) are never compromised by LLM non-determinism
- Rate limits and safety constraints remain in hardcoded Python logic
- Claude failures degrade gracefully — the system falls back to Phase 4 behavior, not to failure

---

## 3. Features in Scope (Phase 5 Only)

### F13: Analyst Intelligence (Analyst Agent)

**What it does**: After Analyst's Python script collects metrics and generates raw summaries, a Claude subagent reads those summaries plus pipeline context and produces an intelligent daily report with anomaly detection, category breakdown, A/B test evaluation, outbound effectiveness, and a pre-composed Telegram message.

**Why now**: Marc currently owns all analytical reasoning in Step P8 — reading raw JSON, applying anomaly formulas, composing reports. This is duplicated effort that belongs in Analyst. The data and infrastructure already exist (SQLite, JSON summaries); only the reasoning layer is missing.

**What it replaces**: Marc's manual Steps P8 (follower anomaly check + daily report composition).

**Output**: `data/daily_report_{YYYYMMDD}.json` — new file containing structured analysis plus `telegram_report` and `telegram_alerts` fields ready for sending.

**Edge cases**:

| Case | Expected Behavior |
|---|---|
| **First day (no yesterday data)** | Trend comparison skipped; reports "no previous data available" |
| **No posted tweets today** | Category breakdown empty; reports "no content posted" |
| **All metrics zero** | Valid report with zero values; no false anomalies |
| **Outbound log missing** | Reports zero outbound activity |

**What it delivers to the operator**: A single Telegram message each day with everything needed to understand account health — follower trends, engagement by content type, A/B test progress, and automatic alerts for anomalies. No more reading raw JSON files.

---

### F14: Scout Intelligence (Scout Agent)

**What it does**: Instead of running `scout.py` and passing raw data to Strategist, a Claude subagent runs `scout.py --raw --compact` for data collection, then analyzes the compact output: filters reply contamination, computes impression-based engagement, applies dynamic trending thresholds, filters new account discoveries, and writes an executive summary. The enriched report includes an additive `analysis` section while preserving all existing fields for backward compatibility.

**Why now**: Scout produces 457KB of raw data that no one can effectively read. 36.9% of engagement samples are contaminated by reply tweets. Trending always returns zero results (hardcoded threshold too high). 59 new accounts include bots alongside 200K-follower accounts. These are known, measured problems that Claude can solve.

**What it replaces**: Raw scout report goes directly to Strategist. After Phase 5, Strategist receives the same data plus a curated `analysis` section.

**Output**: Enriched `data/scout_report_{YYYYMMDD}.json` with new `analysis` section (backward compatible).

**New Python flag**: `--raw --compact` reduces scout output from ~457KB to ~30KB for Claude context window compatibility.

**Edge cases**:

| Case | Expected Behavior |
|---|---|
| **Scout API collection fails** | Claude subagent reports error; Marc falls back to legacy `scout.py` |
| **All competitors have zero hashtags** | `hashtag_signal` explains this as a strategic signal, not a data gap |
| **Context window exceeded despite `--compact`** | Not expected at 41 competitors (~30KB); if it occurs, Scout reads in batches |
| **Strategist ignores `analysis` section** | Fine — `analysis` is additive; all existing fields unchanged |

**What it delivers to the operator**: Competitive intelligence that's actually intelligent — filtered engagement rates, quality-screened new accounts, and a 3-5 bullet executive summary per market that surfaces actionable patterns instead of raw numbers.

---

### F15: Publisher Smart Outbound (Publisher Agent)

**What it does**: Instead of randomly selecting tweets and reply templates, a Claude subagent reads target account data (via new `publisher_outbound_data.py`), selects relevant tweets to like, crafts contextual replies referencing actual tweet content, and writes an outbound engagement plan. A new `publisher.py smart-outbound` subcommand then executes the plan with the same rate limits and delays as legacy outbound.

**Why now**: Current outbound uses `random.choice(reply_templates)` and always targets `recent_tweets[0]`. This produces generic, bot-like engagement that doesn't build genuine connections. The X API data to make intelligent choices already exists — it just needs reasoning.

**What it replaces**: `publisher.py outbound` for the engagement logic (not API execution). Post subcommand is completely unchanged.

**Output**: `data/outbound_plan_{YYYYMMDD}_{account}.json` containing per-target engagement actions with contextual replies and reasoning.

**Edge cases**:

| Case | Expected Behavior |
|---|---|
| **Target account has only off-topic content** | Marked `skip: true` with reason; no engagement |
| **All targets skipped** | Valid plan with empty actions; Marc logs and reports |
| **Claude subagent fails** | Marc falls back to legacy `publisher.py outbound` |
| **Rate limits nearly exhausted** | `smart-outbound` respects same limits as legacy; stops at limit |

**What it delivers to the operator**: Outbound engagement that feels genuine — replies that reference the target's actual content, likes on relevant posts, and transparent reasoning for every action. Over time, this builds real connections in the AI beauty community.

---

### F15a: Outbound Approval Gate (Marc + Telegram)

**What it does**: For the first 1-2 weeks after Publisher Smart Outbound launches, Marc sends the outbound plan preview to Telegram and waits for operator approval before executing. After quality is verified, switches to autonomous execution.

**Approval mechanism**: Marc formats a summary of the outbound plan (targets, tweets to like, reply text, reasoning) and sends it via `telegram_send.py`. The operator reviews and responds with `/approve` or `/reject` via the existing Telegram bot (`telegram_bot.py`). This requires adding two new command handlers to the bot — see spec §5.9 Step P4 for details. The approval state is tracked in `data/outbound_approval_{YYYYMMDD}_{account}.json`.

**Why now**: Smart Outbound is the highest-risk Phase 5 feature — contextual replies are posted publicly under the brand account. Human review during initial rollout ensures quality.

**What it replaces**: Nothing (new gate).

**Edge cases**:

| Case | Expected Behavior |
|---|---|
| **Operator doesn't respond within 2 hours** | Marc logs timeout, skips outbound for the day |
| **Operator rejects plan** | Marc falls back to legacy outbound |
| **Operator approves but rate limits expired** | Marc checks limits before execution; may have reduced capacity |

**What it delivers to the operator**: Peace of mind during Smart Outbound rollout. The operator sees exactly what the system plans to do before it does it — every like, reply, and follow with reasoning.

---

## 4. Features NOT in Scope

| Feature | Phase | Why Not Now |
|---|---|---|
| **VPS deployment** | Phase 6 | No infrastructure changes needed for hybrid agents |
| **Cron scheduling** | Phase 6 | System still runs via manual triggers |
| **Publisher post changes** | — | Safety-critical, human-gated; adding LLM reasoning would introduce non-determinism |
| **New agents** | — | All 6 agents are built; Phase 5 enhances existing ones |
| **Playwright impression scraping** | — | Deferred indefinitely; manual input sufficient |
| **`validate.py` Claude conversion** | — | Validation must remain deterministic and reproducible |
| **Full autonomous operation** | Phase 7 | Requires VPS (Phase 6) first |

---

## 5. User Stories (Phase 5)

### 5.1 Operator Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| **P5-01** | operator | receive a daily report via Telegram that includes follower trends, engagement by category, and anomaly alerts | I don't have to read raw JSON files to understand account health | `daily_report` JSON has `telegram_report` field; Telegram message received |
| **P5-02** | operator | know immediately if follower count changes by more than 10% | I can investigate potential shadowbans or viral moments | `telegram_alerts` contains anomaly entry when threshold exceeded |
| **P5-03** | operator | see competitive intelligence with reply-filtered engagement rates | I can trust the data when making strategy decisions | `analysis.engagement_adjusted` uses reply-filtered rates |
| **P5-04** | operator | see which new accounts are worth tracking (filtered from raw discoveries) | I don't waste time evaluating bot accounts | `analysis.new_accounts_filtered` has quality-screened entries |
| **P5-05** | operator | review outbound engagement plans before execution (during rollout) | I can verify reply quality before it's posted publicly | Telegram preview sent; `/approve` triggers execution |
| **P5-06** | operator | see reasoning for each outbound action | I understand why the system chose specific tweets and replies | `reasoning` field present in each `reply_to` entry |
| **P5-07** | operator | trust that the system falls back to working behavior if Claude fails | a Claude outage doesn't break the entire pipeline | All three fallbacks tested and verified |

### 5.2 System Stories (Phase 6 Readiness)

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| **P5-08** | pipeline | run Scout with Claude intelligence without manual intervention | the overnight pipeline produces enriched intelligence automatically | Pipeline completes with enriched scout report |
| **P5-09** | pipeline | degrade to Phase 4 behavior when Claude subagents fail | VPS deployment (Phase 6) inherits resilient fallback patterns | Each fallback path verified; pipeline state logged |
| **P5-10** | pipeline | produce daily reports without Marc doing manual math | report composition doesn't depend on Marc's prompt engineering | `daily_report` JSON valid without Marc intervention |

---

## 6. Exit Criteria

**Go/no-go checklist for Phase 6**:

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| **1** | Analyst Intelligence produces valid `daily_report` JSON | `python3 scripts/validate.py analyst_report data/daily_report_{date}.json` → PASS | [ ] |
| **2** | Anomaly detection catches >10% follower change | Test with known -14.3% EN data → `anomaly: true` | [ ] |
| **3** | Scout `--compact` reduces report to <50KB | `wc -c data/scout_compact_{date}.json` < 50,000 | [ ] |
| **4** | Enriched scout report backward compatible | Full pipeline Scout → Strategist → Creator passes all validation | [ ] |
| **5** | Publisher Smart Outbound produces contextual replies | Manual review: replies reference target tweet content | [ ] |
| **6** | Rate limits enforced in `smart-outbound` | Test with near-limit counters → stops at limit | [ ] |
| **7** | All three fallbacks work | Simulate failure for each → legacy path executes | [ ] |
| **8** | No pipeline regression | Full pipeline run matches Phase 4 completion | [ ] |
| **9** | All 20 tests pass | Test results documented in `docs/testing/` | [ ] |

---

## 7. Risks Specific to Phase 5

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Claude subagent produces invalid JSON (code fences, truncation)** | Medium | Low | H3 retry with specific "no fences" instruction; validate.py catches all parse errors |
| **Scout context window overflow (457KB report)** | Low | Medium | `--compact` flag reduces to ~30KB; verified in Test 8 |
| **Smart Outbound replies feel generic despite contextual intent** | Medium | Medium | Initial approval gate (F15a) catches quality issues; operator can reject and fall back |
| **Claude API latency adds >60s to pipeline** | Medium | Low | Subagent calls are not time-critical; pipeline runs overnight |
| **Fallback code path not exercised in production** | Low | High | Explicit fallback tests (Tests 16, 20) in testing strategy; Test 7 in exit criteria |
| **Analyst anomaly threshold too sensitive for small accounts** | Medium | Low | 10% threshold on 6 followers = ±1 follower triggers alert; acceptable for early stage. When either account exceeds 100 followers, reassess threshold (consider absolute minimum like `abs(change) >= 5 AND pct >= 10%`) |
| **Publisher outbound data fetcher rate-limited** | Low | Low | Uses same XApiClient with existing retry logic; 2-5 API calls per account |

---

## 8. Timeline

### 8.1 Sub-Phase Plan

| Sub-Phase | Focus | Key Deliverable | Gate Criteria |
|---|---|---|---|
| **Sub-Phase 1** | Analyst Intelligence | `daily_report` JSON with anomaly detection, category breakdown, A/B evaluation | Tests 1-5 pass; anomaly catches -14.3% drop |
| **Sub-Phase 2** | Scout Intelligence | Enriched `scout_report` with `analysis` section; `--compact` flag | Tests 6-11 pass; backward compatible with Strategist |
| **Sub-Phase 3** | Publisher Smart Outbound | Outbound plan with contextual replies; `smart-outbound` subcommand | Tests 12-17 pass; replies reference tweet content |
| **End-to-End** | Full integration | All three hybrid agents in pipeline and publishing flows | Tests 18-20 pass; all exit criteria met |

---

## 9. Feature-to-Spec Mapping

| PRD Feature | Spec Section | Files |
|---|---|---|
| **F13: Analyst Intelligence** | §3.1, §5.1, §6.1 | `agents/analyst.md`, `scripts/validate.py`, `agents/marc_publishing.md` |
| **F14: Scout Intelligence** | §3.2, §5.2, §5.4, §6.2, §6.3 | `agents/scout.md`, `scripts/scout.py`, `scripts/validate.py`, `agents/marc_pipeline.md` |
| **F15: Publisher Smart Outbound** | §3.3, §5.3, §5.5, §5.6, §6.4 | `agents/publisher.md`, `scripts/publisher.py`, `scripts/publisher_outbound_data.py` (new), `scripts/validate.py`, `agents/marc_publishing.md` |
| **F15a: Outbound Approval Gate** | §3.3, §5.9 | `agents/marc_publishing.md` |

---

*Phase 5 Product Requirements v1.0*
*Date: March 5, 2026*
*Parent: [PRD v1.1](./x-ai-beauty-prd-v1.md)*
