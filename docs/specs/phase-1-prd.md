# Phase 1 Product Requirements — Scout + Strategist + Marc Foundation

**Document version**: 1.0
**Date**: March 3, 2026
**Status**: Draft
**Phase**: 1 of 6 (Days 3-5)
**Parent document**: [Product Requirements Document v1.1](./x-ai-beauty-prd-v1.md)
**Technical companion**: [Phase 1 Technical Specification](./phase-1-spec.md)

---

## 1. Executive Summary

Phase 1 builds the **intelligence layer** — the foundation that all downstream agents depend on. It delivers two core capabilities:

1. **Competitor Intelligence (Scout)**: Daily automated research of all competitor accounts in `config/competitors.json` (41 at time of writing: 24 EN, 15 JP, 2 both) across EN and JP markets, extracting engagement data, posting patterns, hashtag usage, and trend analysis via X API v2.

2. **Growth Strategy Engine (Strategist)**: Daily data-driven strategy generation that analyzes Scout's findings and produces specific, actionable recommendations — posting schedules, content mix ratios, hashtag strategies, and outbound engagement policies — for both EN and JP accounts.

3. **Pipeline Orchestration (Marc foundation)**: Automated sequencing of Scout → Strategist with output validation, cross-checking, and logging. This is the skeleton that will grow into full COO orchestration in later phases.

**No content is created and no posts go live in Phase 1.** This phase is purely analytical — it produces the intelligence and strategy documents that Phase 2 (Creator) will consume.

**Prerequisite**: Phase 0 must be complete — X API credentials working, Claude Code authenticated, `config/accounts.json` and `config/competitors.json` populated. See [Phase 0 Runbook](../phase-0-runbook.md).

---

## 2. Phase 1 Goals & Success Criteria

### 2.1 What Phase 1 is NOT Measuring

Phase 1 does **not** measure follower growth, engagement rates on our own posts, or any audience-facing metrics — because nothing is posted yet. The system is not yet visible to the outside world.

### 2.2 Phase 1 Goals

| # | Goal | Why It Matters |
|---|---|---|
| G1 | Scout produces actionable competitive intelligence | Without understanding the competitive landscape, all content decisions are guesswork |
| G2 | Strategist produces specific, data-driven recommendations | Strategy must be concrete enough for Creator (Phase 2) to execute without ambiguity |
| G3 | Marc reliably orchestrates the pipeline with validation | The pipeline must be trustworthy before adding more agents — a broken pipeline multiplies errors |
| G4 | System identifies top-performing content themes | Knowing what works for competitors before we post our first content gives us a head start |
| G5 | System produces daily posting schedules and hashtag strategies | These outputs become direct inputs to Creator in Phase 2 — they must be ready |

### 2.3 Success Criteria

| Criterion | Metric | Target |
|---|---|---|
| Competitor coverage | Competitors with data in Scout report | ≥ 90% of competitors in `config/competitors.json` (allowing for protected/suspended) |
| Data completeness | Fields populated per competitor | All required fields present (handle, user_id, followers, engagement_rate, recent_posts) |
| Strategy actionability | Strategist output contains both EN/JP sections with posting_schedule | Both accounts have 3-5 time slots with categories |
| Pipeline reliability | Full pipeline runs without errors | Successful end-to-end completion |
| Validation coverage | All validation rules pass | Scout + Strategist + cross-validation all pass |
| Reproducibility | Pipeline produces consistent outputs on re-run | Same structure, comparable insights across multiple runs |

### 2.4 Design Principle: Harness Quality

The pipeline harness (Marc as Claude agent + `validate.py`) is the product — not the prompts, not the model. Harness engineering research ("Agent Harness is the Real Product") demonstrates that output quality is primarily a function of validation, context assembly, and error handling, not prompt length or model sophistication. Marc's skill file (`agents/marc.md`) defines the orchestration, while `scripts/validate.py` provides the deterministic feedback loop.

**Implications for Phase 1:**

| Principle | What It Means |
|---|---|
| **Validation is the product** | A missed validation rule is a product defect — it lets bad data flow to downstream agents. Every validation check in Marc's pipeline is a quality gate, not busywork. |
| **Context assembly matters** | How Strategist receives its inputs (file path reference vs. full content injection) directly affects output quality. Progressive disclosure — letting the model read what it needs — keeps context budgets healthy. |
| **Plan for simplification** | If the pipeline grows more complex over time while model capabilities improve, something is wrong. Track which validation rules actually fire, and remove those that never do. The harness should get simpler, not heavier. |

---

## 3. Features in Scope (Phase 1 Only)

### F1: Competitor Intelligence (Scout)

**Source**: PRD Feature F1 (Competitor Intelligence)

| Aspect | Phase 1 Scope |
|---|---|
| Competitor count | All accounts in `config/competitors.json` (41 at time of writing: 24 EN, 15 JP, 2 both) |
| Data per competitor | Followers, following, tweet count, recent posts (10), engagement rates, hashtags |
| Frequency | Manual trigger via CLI (daily when in use) |
| Output | `data/scout_report_{YYYYMMDD}.json` |
| Viral post detection | Top 3 posts per competitor by engagement rate |
| Hashtag analysis | Frequency count across all competitors, broken down by market |
| Market comparison | EN vs JP averages (followers, engagement, posting frequency, top hashtags) |
| Trend research | Keyword search for 8 tracked terms, new account discovery |

**What it delivers to the operator**: A single JSON file containing a complete daily snapshot of the competitive landscape — who's growing, what content performs best, which hashtags are trending, and how EN and JP markets compare.

### F2: Strategy Engine (Strategist)

**Source**: PRD Feature F2 (Strategy Engine)

| Aspect | Phase 1 Scope |
|---|---|
| Input | Scout report (today's) |
| Output | Per-account (EN + JP) strategy document |
| Posting schedule | 3-5 optimal time slots per account with content categories |
| Content mix | Percentage breakdown by content category |
| Hashtag strategy | Always-use, rotate, and trending hashtag recommendations |
| Outbound strategy | Daily limits and target accounts for likes/replies/follows |
| A/B test design | One active test variable per account |
| Insights | 3-5 actionable observations from today's data |
| NOT in Phase 1 | Performance analysis of own posts (no posts yet), Analyst data integration (no Analyst yet) |

**What it delivers to the operator**: A concrete action plan for each account — exactly what to post, when to post it, which hashtags to use, and where to focus outbound engagement. Ready for Creator to consume in Phase 2.

### F7: Marc Orchestration (Foundation)

**Source**: PRD Feature F7 (COO Orchestration)

| Aspect | Phase 1 Scope |
|---|---|
| Pipeline sequencing | Scout → validate → Strategist → validate → cross-check |
| Output validation | Schema validation + data quality checks for both agents |
| Cross-validation | Consistency checks between Scout and Strategist outputs |
| Logging | Timestamped pipeline log with agent attribution |
| Pipeline state | Task-based state tracking in `pipeline_state_{date}.json` |
| NOT in Phase 1 | Telegram reporting, War Room, command processing, Creator/Publisher/Analyst orchestration, error escalation via Telegram |

**What it delivers to the operator**: A single command (`bash scripts/run_pipeline.sh`) that invokes Marc (Claude agent) to run the entire intelligence pipeline, validate all outputs via `scripts/validate.py`, and log results — with confidence that bad data won't silently pass through.

### Partial F10: EN/JP Market Comparison

**Source**: PRD Feature F10 (EN/JP A/B Testing)

| Aspect | Phase 1 Scope |
|---|---|
| Market comparison | Scout's `market_comparison` section compares EN vs JP competitor performance |
| Strategy differentiation | Strategist produces separate strategies for each market |
| NOT in Phase 1 | Own-account A/B test results (no posts yet), follower growth comparison |

---

## 4. Features NOT in Scope

Explicitly excluded from Phase 1 to prevent scope creep:

| Feature | Phase | Why Not Now |
|---|---|---|
| **F3: Content Generation** (Creator) | Phase 2 | Depends on Strategy output (which Phase 1 builds) |
| **F4: Automated Posting** (Publisher) | Phase 3 | Depends on Creator content + human approval flow |
| **F5: Outbound Engagement** execution | Phase 3 | Publisher handles execution; Phase 1 only plans the strategy |
| **F6: Metrics Collection** (Analyst) | Phase 4 | No posts to measure yet |
| **F8: Telegram Commands** | Phase 2 | Marc's Phase 1 scope is pipeline-only; Telegram comes in Phase 2 |
| **F9: Human Approval Flow** | Phase 2 | No content to approve yet |
| **Cron scheduling** | Phase 5 | All Phase 1 testing is manual CLI |
| **VPS deployment** | Phase 5 | Development is local-first |

---

## 5. User Stories (Phase 1)

### 5.1 Operator Stories

| ID | As a... | I want to... | So that... | Acceptance Criteria |
|---|---|---|---|---|
| P1-01 | Operator | See which competitors are growing fastest | I know who to learn from | Scout report includes follower counts and engagement rates for all competitors |
| P1-02 | Operator | See what content competitors are posting | I understand what works in this niche | Scout report includes recent posts with text, metrics, and hashtags |
| P1-03 | Operator | See what hashtags perform best in my niche | I can use effective hashtags from day one | Scout report includes hashtag frequency analysis, broken down by market |
| P1-04 | Operator | Receive a daily strategy document | I know exactly what to post, when, and with which hashtags | Strategist produces JSON with posting schedule, content mix, and hashtag strategy for both EN and JP |
| P1-05 | Operator | Compare EN vs JP market engagement and growth | I can decide which market to focus on early | Scout's market_comparison section shows per-market averages |
| P1-06 | Operator | Run the full pipeline with one command | I don't need to manually chain agents | `bash scripts/run_pipeline.sh` invokes Marc (Claude agent) to run Scout → Strategist end-to-end |
| P1-07 | Operator | Trust that pipeline outputs are validated | Bad data doesn't silently propagate | Pipeline validates both outputs and logs any failures |
| P1-08 | Operator | Test incrementally (1 competitor, then 5, then all) | I can verify the system works before committing to a full run | `--max-competitors` CLI flag controls how many competitors Scout fetches |

### 5.2 System Stories (for Phase 2 readiness)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| P1-09 | Creator agent (Phase 2) | Have a `strategy_current.json` with posting schedule | I know exactly what content to produce and when |
| P1-10 | Creator agent (Phase 2) | Have hashtag recommendations per post | I can apply the right hashtags without guessing |
| P1-11 | Marc agent (Phase 2) | Have validated pipeline state JSON | I can extend the pipeline with Creator without rewriting validation |

---

## 6. Phase 1 Exit Criteria

**Go/no-go checklist for Phase 2**:

| # | Criterion | How to Verify | Status |
|---|---|---|---|
| 1 | Scout report covers all competitors in `config/competitors.json` (minus protected/suspended) | Check `competitors_fetched` count in scout report | [ ] |
| 2 | All accessible competitor `user_id`s resolved and saved | Check `config/competitors.json` for empty user_ids | [ ] |
| 3 | Scout report contains engagement data (followers, engagement_rate, recent_posts) | Inspect any competitor entry in the report | [ ] |
| 4 | Strategy document provides posting schedule for both EN and JP | Check for `EN.posting_schedule` and `JP.posting_schedule` | [ ] |
| 5 | Strategy `content_mix` sums to 100 for each account | Verify manually or with validation script | [ ] |
| 6 | Pipeline runs without manual intervention (beyond initial command) | `bash scripts/run_pipeline.sh` completes successfully | [ ] |
| 7 | Output JSONs pass all validation checks | Pipeline state shows all validations passed | [ ] |
| 8 | At least 3 successful pipeline runs completed | Check dated files in `data/` directory | [ ] |
| 9 | Pipeline log shows complete execution history | `logs/pipeline_{date}.log` has entries for all runs | [ ] |
| 10 | `strategy_current.json` exists and is valid | `python3 -m json.tool data/strategy_current.json` | [ ] |

---

## 7. Risks Specific to Phase 1

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| X API rate limits throttle Scout | Low | Medium — incomplete data for some competitors | Phase 1 uses ~11% of monthly read budget. Start with `--max-competitors 5` and scale up. Retry logic with exponential backoff. |
| Competitor accounts are private/suspended | Medium | Low — data gaps for specific accounts | Mark and skip. Losing a few accounts is acceptable. Report skipped accounts in output for human review. |
| Strategist output quality inconsistent | Medium | Medium — strategy may not be actionable | Detailed skill file with exact JSON schema. Validation catches structural issues. Iterate skill file based on output quality. |
| Claude produces invalid JSON | Medium | Low — caught by validation | Strip markdown code fences. Retry once if JSON is invalid. Skill file emphasizes "output ONLY valid JSON". |
| bearer_token is invalid or expired | Low | High — Scout cannot run at all | Caught on first API call. Clear error message with instructions to check `config/accounts.json`. Tested in Phase 0. |
| tweepy API changes | Very Low | Medium — Scout breaks | Pin tweepy version in `requirements.txt`. |
| user_id resolution fails for many accounts | Low | Medium — can't fetch timelines | Use `--max-competitors` for incremental testing. Log failures clearly. Manual fallback: look up user_id on X.com. |
| Pipeline harness accumulates complexity across phases | Medium | Medium — harder to debug, slower to iterate | Track validation rule hit rates. Remove rules that never fire after 10+ runs. Review harness complexity at each phase boundary. Complexity growth while model outputs stabilize = product smell (see Section 2.4). |

---

## 8. Timeline

### 8.1 Day-by-Day Plan

| Day | Calendar | Focus | Deliverables |
|---|---|---|---|
| **Day 3** | Day 3 from project start | X API wrapper + Scout | `scripts/x_api.py` (tested), `scripts/scout.py` (tested with 1 → 5 → all competitors), first `scout_report_{date}.json` |
| **Day 4** | Day 4 from project start | Strategist skill file + testing | `agents/strategist.md` (complete), first `strategy_{date}.json`, iterated based on output quality |
| **Day 5** | Day 5 from project start | Marc agent + validation + end-to-end | `agents/marc.md` (full orchestration skill file), `scripts/validate.py` (tested), `scripts/run_pipeline.sh` (wrapper), 3+ successful pipeline runs, exit criteria verified |

### 8.2 Day 3 Breakdown

1. Write `scripts/x_api.py` wrapper class
2. Test: resolve 1 user handle → verify user_id + public_metrics returned
3. Test: fetch 1 user timeline → verify tweets with public_metrics returned
4. Test: search 1 keyword → verify results returned
5. Write `scripts/scout.py` with full logic
6. Test: `--max-competitors 1` → inspect output
7. Test: `--max-competitors 5` → inspect output
8. Test: full run (all competitors) → verify all data collected
9. Verify `config/competitors.json` has user_ids populated

### 8.3 Day 4 Breakdown

1. Write `agents/strategist.md` skill file with exact output schema
2. Run: `claude -p "You are the Strategist agent. Read agents/strategist.md for full instructions. Scout report: data/scout_report_{date}.json. Write output to data/strategy_{date}.json." --dangerously-skip-permissions`
3. Inspect output: is it valid JSON? Does it have EN + JP? Is it actionable?
4. Iterate skill file based on output quality (2-3 iterations expected)
5. Test edge case: what happens with a small Scout report (1 competitor)?
6. Test edge case: does Claude wrap JSON in code fences? Add stripping logic if needed.

### 8.4 Day 5 Breakdown

1. Write `scripts/validate.py` (unified validation: scout, strategist, cross modes)
2. Test validate.py: `python3 scripts/validate.py scout <report>`, `strategist <strategy>`, `cross <report> <strategy>`
3. Write `agents/marc.md` (full orchestration skill file — see Phase 1 spec Section 5.4)
4. Write `scripts/run_pipeline.sh` (thin shell wrapper invoking Marc)
5. Test: Marc scout-only → verify Scout runs + validates
6. Test: Marc strategist-only → verify Strategist runs with existing report
7. Test: full pipeline (`bash scripts/run_pipeline.sh`) → verify end-to-end
8. Run full pipeline 3 times → verify reproducibility
9. Check all exit criteria

---

## 9. Feature-to-Spec Mapping

Traceability from PRD features to Technical Specification deliverables:

| PRD Feature | Spec Deliverable | Files |
|---|---|---|
| F1: Competitor Intelligence | Scout agent | `scripts/x_api.py`, `scripts/scout.py`, `agents/scout.md` |
| F2: Strategy Engine | Strategist agent | `agents/strategist.md` |
| F7: Marc Orchestration (foundation) | Marc as Claude agent + validation scripts | `agents/marc.md`, `scripts/validate.py`, `scripts/run_pipeline.sh` |
| F10: EN/JP Comparison (partial) | Market comparison in Scout output | `data/scout_report_{date}.json` → `market_comparison` section |

---

*Phase 1 Product Requirements v1.0*
*Date: March 3, 2026*
*Parent: [PRD v1.1](./x-ai-beauty-prd-v1.md)*
