# X-Agent System Redesign v5 — Meruru as Unified Creative Agent

**Date:** April 6, 2026
**Status:** Planned
**Supersedes:** v4 Orchestrator + Strategic Manager architecture (March 2026)

---

## 1. Problem Statement

After 6 weeks of v4 operation, the system has failed its core value proposition again. The operator assessed the entire system as **non-functional** in April 2026.

### Root Causes

| # | Issue | Root Cause |
|---|-------|-----------|
| 1 | **System adds overhead, not value** | Operator spends 3hrs/day on content. Only 30min is mechanics — the rest is creative decisions the system doesn't help with. |
| 2 | **Content has no soul** | Character identity split across Strategist, Creator, and Marc Review. No single entity "is" Meruru. |
| 3 | **Image prompts are repetitive** | 5 of last 6 Slot 1 posts are luxury interiors. Reference images template-matched (location/outfit), not creatively adopted. |
| 4 | **Captions sound like AI** | Strategic formats (question format, engagement hooks) override character voice. "gm" is a valid Meruru caption regardless of image — system can't produce this. |
| 5 | **Feed balance not addressed** | Operator manually checks close-ups/full-body, sexy/cute, poses, colors, clothing, lighting. System offers no help with this. |
| 6 | **War rooms are noise** | Operator barely reviews analytics or war room outputs. Same 2 action items flagged for 8+ consecutive days with zero execution. |
| 7 | **X API cost prohibitive** | Pay-as-you-go, project not profitable. Every API call is a direct loss. |

### Architectural Root Cause

The v4 architecture separated **coordination** (Python orchestrator) from **management** (Marc Review) — solving v3's 73% coordination overhead. But it preserved the fundamental split: **Strategist decides what to post** → **Creator executes it** → **Marc reviews it**.

This 3-agent split means:
- **Strategist** doesn't know what Meruru looks like or how she talks
- **Creator** follows strategy briefs rather than thinking "what would Meruru post?"
- **Marc** reviews quality metrics but doesn't embody the character

A human influencer doesn't have a strategist deciding their content mix and a separate creator executing it. **They post what feels right because they know who they are.**

---

## 2. Design Decision: Merge All Creative Functions into Meruru

### Before (v4): Orchestrator + 3 LLM Agents

```
Operator → Telegram → Conversational Marc (Sonnet)
                        ↓ (commands)
              orchestrator.py (Python)
                ├── claude -p Strategist (Opus)     ← LLM 1: abstract strategy
                ├── validate.py (Python)
                ├── claude -p Creator (Sonnet)      ← LLM 2: content from strategy
                ├── validate.py (Python)
                └── claude -p Marc Review (Opus)    ← LLM 3: quality check

+ War Room: claude -p War Room (Opus) + Marc Review (Opus) = 2 more calls
Total: 5-6 LLM calls/day, 8-15 min pipeline
```

### After (v5): Meruru as Single Creative Agent

```
Operator → Telegram → Conversational Marc (Sonnet)
                        ↓ (commands)
              orchestrator.py (Python)
                ├── /create  → feed_balance.py (Python, instant)
                │             → unused reference pool (Python)
                │             → claude -p Meruru (Opus)     ← LLM 1
                │                ↓
                │             6 candidate posts:
                │             • 3 reference-based (costume/pose adoption)
                │             • 3 creative (pure Meruru independence)
                │             → validate.py (Python)
                │             → operator picks 4 to actually post
                │
                └── /balance → feed_balance.py (Python, instant)
                              → claude -p Meruru (Opus)     ← LLM 1: feed analysis

Automated: LaunchAgent runs /create daily at 06:00 JST (operator wakes up with plan ready)
Manual: /balance and /create available via Telegram on demand
Total: 1-2 LLM calls/day, 3-5 min
```

---

## 3. Core Concept: Meruru Thinks Like a Human Influencer

Meruru is not executing a strategy brief. She is a 21-year-old woman deciding what to post on her account.

### How she creates content:

1. **She knows who she is** — personality, aesthetic, voice, what she finds funny or interesting
2. **She looks at her recent feed** — sees what she's posted, feels what's missing or getting repetitive
3. **She decides what to post** — caption and image direction together, driven by personality
4. **She suggests both image AND caption** — as one coherent creative vision, not separate strategy → execution

### Unified Creation (Caption + Image Born Together)

The current system: strategy → image prompt → caption matching image (backwards).

The new system: **character personality drives both caption AND image direction as one creative vision**.

Some posts are caption-driven ("gm" is valid regardless of image). Others are image-driven (a striking reference pose inspires a reaction-caption). The process is not strictly sequential — Meruru thinks about the post holistically, with her personality as the driver.

Each daily plan contains 6 candidate posts split into two types — see "6 Candidates Per Day" and the per-type sub-sections below for details on how each is created.

### 6 Candidates Per Day → Operator Picks 4

Each daily content plan contains **6 candidate posts**, not 4:
- **3 reference-based posts** — adopt costume/pose from specific unused reference images
- **3 creative posts** — pure Meruru creativity, no reference adoption

The operator reviews all 6 candidates and selects 4 to actually post (mentally or via the HTML report). This design serves two purposes:
1. **More variety to choose from** — operator picks the strongest of each type
2. **Training signal over time** — comparing which type the operator selects more often informs whether Meruru's creative independence is improving

As Meruru's creative quality improves with prompt iteration and identity refinement, the ratio may shift toward more creative posts and fewer reference-based ones. Initially, expect heavier reliance on reference adoption.

### Reference Image Adoption (3 posts of 6)

For the 3 reference-based posts, each adopts a **specific unused reference image**. The adoption rule:
- **Keep**: The reference's costume and pose
- **Keep**: Meruru's character lock (body, face, expression, hair color)
- **Change**: Background/scene (fresh setting, informed by feed balance)
- **Single-use**: Once a reference is used in a content plan, it is not reused in future plans

The orchestrator provides 8-12 unused reference image descriptions per prompt. Meruru selects 3 (one per reference-based post) and explains what she adopted from each.

### Creative Posts (3 posts of 6)

For the 3 creative posts, Meruru works without a reference image. She decides costume, pose, scene, and caption purely from her personality, visual style (from `meruru_identity.md`), and feed balance. These posts are her creative independence in action — they reveal whether her identity is rich enough to generate compelling content without leaning on visual prompts.

### Feed Balance Awareness

Instead of content_mix percentages (45% image_showcase, 35% engagement_questions, 20% self_quote_chains), Meruru sees her actual feed:

> "I've posted 8 bedroom/bathroom shots in the last 12 posts. My feed looks same-y. I need something bright — gym, outdoor, or casual lifestyle. And I haven't done a close-up in a week."

This is computed by Python (counting is deterministic), then interpreted by Meruru (deciding what to do about it requires creative judgment).

**Note:** Feed balance is computed from system-generated content plans only. The operator also posts manually outside the system (~15-20 posts/day), which are not tracked. The operator can steer Meruru via free-text context with `/create` (e.g., `/create EN "I posted 3 bedroom shots manually today, avoid indoor"`). Balance is approximate, not authoritative.

---

## 4. What Changes

| Component | v4 Status | v5 Action | Rationale |
|-----------|-----------|-----------|-----------|
| **Strategist** | `prompts/strategist.md` (Opus) | **REMOVE** | Balance analysis replaces useful function. Abstract briefs were the source of soulless content. |
| **Creator** | `prompts/creator.md` (Sonnet) | **REPLACE** with `prompts/meruru.md` (Opus) | Meruru subsumes content generation with character-first approach. |
| **War Room** | `prompts/warroom.md` (Opus) | **REMOVE** | Operator doesn't use it. Feedback loop amplified wrong signal. |
| **Marc Review** | `prompts/marc_review.md` (Opus) | **REPLACE** with Python-only Tier 1 validation | No LLM needed for constraint checking. Operator is the real quality gate. |
| **Standing Directives** | `data/strategy/standing_directives.json` | **REMOVE** | Coordination mechanism for multi-agent system. Single agent embeds rules in identity. |
| **Marc Conversation** | `agents/marc_conversation.md` (Sonnet) | **KEEP + UPDATE** | Still the Telegram interface. Route `/create` and `/balance`. |
| **Validation** | `scripts/validate.py` | **KEEP + SIMPLIFY** | Remove strategist/cross modes. Keep creator Tier 1 checks. |
| **Reference Catalog** | `data/content/reference_catalog.json` | **KEEP + ADD usage tracking** | Track which references are used. Inject 8-12 unused references per prompt. Single-use: once adopted, not reused. |
| **Content Plan Format** | JSON schema in `data/content/` | **KEEP** | HTML reports, Telegram commands, validation all depend on this format. |

---

## 5. New Components

### 5.1 Meruru Identity Document (`config/meruru_identity.md`)

Expanded from `config/meruru_concept.md` into a **first-person identity document**. Not "rules about Meruru" but "Meruru speaking about herself."

**Sections:**

1. **Who I Am** — Personality, energy, how I see the world, what I find funny
2. **How I Talk** — Voice rules, caption philosophy, examples, anti-patterns
3. **What I Look Like** — Character lock (physical traits that never change)
4. **My Visual Style** — Scenes, lighting, and moods Meruru gravitates toward (derived from high-performance posted images + their prompts)
5. **My Content Balance** — Operator-defined: basically sexy, mix of cute+sexy / cool+sexy, half-selfies
6. **What I Never Do** — NG list (body comparisons, politics, generic engagement bait)

**Visual Style Derivation Process — ✅ COMPLETED Apr 7, 2026:**

Section 4 ("My Visual Style") was derived from 12 high-performance posted images and their actual Higgsfield prompts (provided by operator). Patterns analyzed: scenes, lighting, mood, framing, expression, outfits, color palette. Result written in first-person Meruru voice and saved at `docs/meruru_visual_style.md` (approved by operator).

**Status:** Approved standalone draft — will be integrated into `config/meruru_identity.md` during Phase 1 implementation.

This is a **one-time analysis**, not a daily computation. It's manually refreshed when Meruru's style evolves (every few months or after major creative shifts).

Source material: `config/meruru_concept.md` (preserved as reference), `docs/meruru_visual_style.md` (approved visual style section).

### 5.2 Feed Balance Module (`scripts/feed_balance.py`)

Pure Python module (no LLM). Three functions:

**`compute_feed_balance(account, days=14) → dict`**

Reads recent content plans, counts across dimensions:
- Framings (close-up / medium / full-body)
- Poses (standing / seated / reclined / prone / kneeling / etc.)
- Scene types (bedroom / bathroom / gym / outdoor / cafe / etc.)
- Outfit types and coverage levels (minimal / casual / styled)
- Color palettes (dark / bright / pastel / neutral)
- Moods (sexy / cute / playful / confident / cozy)
- Lighting types (natural / warm / moody / golden hour)
- Camera angles (eye-level / low / high)

Returns: structured dict + human-readable summary of what's over/under-represented.

**Note:** Balance is approximate — computed from system-generated plans only, not the operator's manual posts. Operator can supplement with free-text context via `/create`.

**`get_unused_references(account, count=12) → list`**

Reads `data/content/reference_catalog.json` (full reference pool) and `data/content/reference_usage.json` (used references). Returns `count` unused reference descriptions (filename, scene, pose, outfit, mood — compact format) for the requested account.

Used references are tracked via the clean `posts[].reference_filename` field on past content plans (set by Meruru on reference-based posts), not by parsing free-text notes.

If fewer than `count` unused references remain, warns the operator that the reference pool is running low (threshold: 30 unused).

**`mark_references_used(plan_json) → None`**

After a content plan is saved, extracts which references were adopted (from `posts[].reference_filename` field on reference-based posts only) and updates a usage tracking file (`data/content/reference_usage.json`) so they're excluded from future pools. Creative posts have no reference, so they're skipped.

**`reference_usage.json` schema:**

```json
{
  "EN": [
    {
      "filename": "HEBi9Hab0AAibLa.jpeg",
      "used_at": "2026-04-07",
      "plan": "content_plan_20260407_EN.json",
      "post_id": "EN_20260407_01"
    }
  ],
  "JP": []
}
```

`get_unused_references()` reads both this file and `reference_catalog.json` to compute the unused pool.

### 5.3 Meruru Creative Prompt (`prompts/meruru.md`)

Template with placeholders, invoked via `claude -p` (Opus).

**Structure (in priority order):**

```
1. {{identity}}           — Who I am (from meruru_identity.md)         ~3K chars
2. {{feed_balance}}       — What I've posted, what's missing           ~1K chars
3. {{unused_references}}  — 8-12 unused reference image descriptions   ~3K chars
4. {{recent_captions}}    — Captions I've used (don't repeat)          ~500 chars
5. {{operator_context}}   — Optional free-text from operator           ~0-500 chars
6. {{task}}               — Create 6 candidates: 3 ref-based + 3 creative  ~700 chars
7. {{tier1_constraints}}  — iPhone, negative prompt, character lock     ~1K chars
8. {{image_prompt_format}}— Higgsfield-compatible structured schema    ~1.5K chars
9. {{output_format}}      — JSON schema for content plan (6 candidates) ~1K chars
```

**Total prompt: ~13-19K chars** (down from ~100K+ current Creator prompt).

**Key design:** Meruru creates 6 candidate posts (3 reference-based + 3 creative). Each post is caption + image direction born together as one creative act, driven by her personality.

**For each reference-based post (3 of 6):**
1. Consider what the feed needs (from balance data)
2. Pick an unused reference image
3. Decide caption + image direction together — personality drives both
4. Image adopts reference's costume/pose, keeps character lock, fresh background
5. Set `reference_filename` field with the chosen reference; in `notes`, explain what was adopted (costume style, pose technique, why this reference fits the feed need)

**For each creative post (3 of 6):**
1. Consider what the feed needs (from balance data)
2. Decide caption + image direction together — purely from personality and visual style
3. Image keeps character lock, all other elements (costume, pose, scene, lighting) chosen by Meruru from her own taste
4. In notes: explain the creative reasoning (why this scene, this mood, this caption)

**Reference adoption rule (reference-based posts only):**
- Adopt: costume (outfit type, color, style) and pose (position, stance, angle) from the selected reference
- Keep: Meruru's character lock (body, face, expression rules, hair color)
- Change: background/scene (choose based on feed balance — what scenes are underrepresented)

**Output structure:** Each of the 6 posts includes a `type` field: `"reference_based"` or `"creative"`. The operator reviews all 6 and mentally selects which 4 to actually post.

**Image prompt format:** Must remain Higgsfield-compatible with structured fields (meta, subject, outfit, pose, scene, camera, lighting, mood) plus the standard combined negative prompt. The `{{image_prompt_format}}` placeholder is **extracted from `config/image_prompt_guide.md`** (Tier 1 schema only — the structured field definitions and the standard negative prompt block, not the full 615-line guide).

### 5.4 Meruru Balance Prompt (`prompts/meruru_balance.md`)

Lighter prompt for `/balance` command. Meruru receives her identity + feed balance data and produces a natural-language recommendation:

```
Looking at my feed lately...

Heavy on bedroom shots (8 of last 12). Need something different.
Haven't done gym in 10 days. My feed needs energy.
Everything's been dark colors — time for something bright.
No close-ups in a week — my face is my brand too.

What I'd post next:
1. Gym selfie, bright workout outfit, confident energy → "my legs said no but i said one more set"
2. Close-up, natural light, soft/cute mood → "good morning to everyone except my alarm"
3. ...
```

Sent directly to Telegram. Operator reads it, decides what to act on.

---

## 6. New Flows

### 6.1 `/create` Flow (1 LLM call, ~3-5 min)

```
orchestrator.py create [EN] [optional free-text context]
  1. feed_balance.py compute_feed_balance()       # Python (instant)
  2. feed_balance.py get_unused_references(12)    # Python (instant)
  3. Load meruru_identity.md                       # File read
  4. Extract recent captions (7-day blocklist)     # Python
  5. Build prompt from prompts/meruru.md           # Python
     — injects: identity, feed_balance, unused_references,
       recent_captions, operator_context, tier1_constraints,
       image_prompt_format, output_format
  6. claude -p Meruru (Opus, timeout 700s)         # LLM 1 — generates 6 candidates
  7. validate.py creator (Tier 1 only, allows 6 posts)  # Python
  8. feed_balance.py mark_references_used(plan)    # Python (only ref-based posts)
  9. Save content_plan_{date}_{account}.json       # File write (6 candidates)
  10. Generate HTML report (shows 6, grouped by type)  # Python
  11. Send to Telegram                             # API call
```

**Automated execution:** LaunchAgent runs `orchestrator.py create EN` daily at 06:00 JST. Operator wakes up with the content plan ready in Telegram.

**Manual execution:** Operator can also run `/create EN "optional context"` via Telegram at any time for on-demand generation.

### 6.2 `/balance` Flow (1 LLM call, ~1-2 min)

```
orchestrator.py balance [EN]
  1. feed_balance.py compute_feed_balance()       # Python (instant)
  2. Load meruru_identity.md                       # File read
  3. Build prompt from prompts/meruru_balance.md   # Python
  4. claude -p Meruru (Opus, timeout 300s)         # LLM 1
  5. Send recommendation to Telegram               # API call
```

**Manual only.** Operator runs `/balance` when they want guidance on what to post next.

### 6.3 Conversational Marc (unchanged)

```
Operator message → telegram_bot.py
  → chat_with_marc() via claude -p (Sonnet)
  → Routes /create, /balance to orchestrator
  → Routes /approve, /status, /details to local handlers
```

---

## 7. New Operator Workflow

### Before (v4): ~3 hours

1. Run `/pipeline` (3 LLM calls, 8-15 min) — wait
2. Receive content plan with 4 posts — skim
3. Ignore strategy rationale and war room outputs
4. **Manually scroll X profile to check feed balance** (~15 min)
5. **Decide which posts to create / modify** (~30 min)
6. Generate images on Higgsfield from prompts (~60 min, 50% hit rate)
7. **Write or heavily edit captions** (~30 min)
8. Schedule on X (~10 min)

### After (v5): Target ~2-2.5 hours

1. Wake up — content plan already generated at 06:00 JST via LaunchAgent (0 min wait)
2. Optionally run `/balance` to check what's missing (1-2 min)
3. Review content plan in Telegram — captions should need less editing (character-first)
4. Generate images on Higgsfield from prompts (~60 min, 50% hit rate — **unchanged**)
5. Light caption editing if needed (~10-15 min, down from 30)
6. Schedule on X (~10 min)

**Realistic time savings (~30-60 min):**

| Step | Before | After | Saved |
|------|--------|-------|-------|
| Pipeline wait | 8-15 min | 0 (runs overnight) | ~10 min |
| Balance check | 15 min (manual scroll) | 1-2 min (/balance) | ~13 min |
| Decide what to post | 30 min | Reduced (Meruru suggests, references adopted) | ~15 min |
| Higgsfield generation | 60 min (50% hit rate) | 60 min (50% hit rate) | **0** |
| Caption editing | 30 min | 10-15 min (character-first voice) | ~15 min |
| Schedule on X | 10 min | 10 min | 0 |
| War room / analytics noise | 10+ min ignoring | 0 (removed) | ~10 min |
| **Total** | **~3 hrs** | **~2-2.5 hrs** | **~30-60 min** |

**Note:** The biggest time sink (Higgsfield generation at 60 min, 50% hit rate) is unaffected by v5. Future improvement: better reference adoption and focused prompts may improve hit rate, but this is not guaranteed.

---

## 8. Cost & Performance Comparison

| Metric | v4 | v5 | Change |
|--------|-----|-----|--------|
| LLM calls/day (pipeline) | 3 (Opus + Sonnet + Opus) | 1 (Opus) | -67% |
| LLM calls/day (war room) | 2 (Opus + Opus) | 0 | -100% |
| LLM calls/day total | 5-6 | 1-2 | -70% |
| Pipeline runtime | 8-15 min | 3-5 min | -65% |
| Prompt size (Creator) | ~100K+ chars | ~13-19K chars | -82% |
| Posts per plan | 4 | 6 candidates → operator picks 4 | +50% variety |
| X API calls | Pay-as-you-go (avoided) | Zero | Same |
| Claude Max cost | $100/mo (unlimited) | $100/mo (unlimited) | Same |
| Operator overhead | ~3 hrs/day | Target 2-2.5 hrs/day | -20-30% |

---

## 9. What's Removed and Why

### Strategist Agent
**Removed.** Its two functions:
- **Content mix percentages** (45/35/20) → Replaced by feed balance analysis. Meruru sees what she's posted and decides what's missing, rather than following a fixed ratio.
- **Creative briefs** (post_purpose, visual_focus) → Replaced by Meruru's own creative judgment. She doesn't need someone telling her "this slot is body_showcase with bust emphasis." She decides what to showcase based on her personality and feed state.

### War Room
**Removed.** Daily morning/evening war rooms produced the same recommendations for 8+ consecutive days (import analytics CSV, implement reply_templates) with zero operator action. The war room was feeding the Strategist, which was feeding the Creator, and neither produced content with soul. It was a well-engineered loop amplifying the wrong signal.

### Standing Directives
**Removed.** Directives were a coordination mechanism for multi-agent communication: Strategist reads them to adjust briefs, Creator reads them to follow rules, Marc creates/resolves them. With a single Meruru agent, persistent rules are embedded directly in the identity document. No CRUD machinery needed.

### Marc Review (LLM)
**Replaced with Python-only validation.** The quality gate doesn't need an Opus call to check if iPhone camera is specified or if captions meet length requirements. `validate.py` handles this. The operator is the real creative quality gate.

### Content Mix Categories
**Removed.** "image_showcase", "engagement_questions", "self_quote_chains" were strategic abstractions that became constraints. Meruru doesn't categorize her posts — she posts what feels right. The feed balance tool ensures variety without rigid categories.

---

## 9.5 Content Plan JSON Format Changes

The content plan JSON schema is preserved (downstream consumers depend on it), but with field-level adjustments:

| Field | v4 | v5 | Notes |
|-------|-----|-----|-------|
| `posts` | 4 items | **6 items** | 3 reference-based + 3 creative |
| `posts[].type` | (none) | **NEW** — `"reference_based"` or `"creative"` | Identifies candidate type |
| `posts[].category` | Fixed list (`image_showcase`, etc.) | **Free-form** — Meruru describes the post in her own words | Kept for downstream compatibility, no longer enforced |
| `posts[].scheduled_time` | Strategist-decided per slot | **Hardcoded** in prompt template — fixed schedule | Fixed times: 14:00, 17:30, 21:00, 23:30 UTC for EN |
| `posts[].status` | `"draft"` → `"approved"` → `"published"` | `"draft"` only | Operator posts manually on X; `/approve` and `/publish` legacy |
| `posts[].notes` | Strategy reasoning | Reference adoption notes (ref-based) or creative reasoning (creative) | Format changes per type |
| `posts[].reference_filename` | (none) | **NEW** — filename of adopted reference (ref-based posts only) | Clean parseable field for usage tracking; `null` for creative posts |
| `visual_diversity` | Per-4-post matrix | **REMOVED** | Operator picks 4 from 6 — diversity of final selection unknown until pick. Variety enforced via Meruru's identity + feed balance, not validation. |

**`/approve` and `/publish` commands:** Kept for backward compatibility but effectively legacy. Operator posts manually on X. These commands may be removed in a future cleanup phase.

---

## 10. What's Preserved and Why

### Content Plan JSON Format
All downstream consumers depend on it: HTML report generator, Telegram `/approve`/`/status`/`/details`, validation. The format isn't the problem — the content filling it is.

### Tier 1 Validation
Hard constraints that prevent quality failures: character lock, iPhone camera, negative prompt, prompt length, hashtag policy, caption length. These are non-negotiable regardless of architecture.

### Marc Conversational Layer
The Telegram interface works. Operator interacts via Marc. Marc routes commands to the orchestrator. This doesn't need to change.

### Reference Catalog
247 operator-curated images are valuable creative input. The change: instead of injecting 20 random descriptions, inject 8-12 **unused** reference descriptions selected per prompt. Each reference is single-use — once adopted in a content plan, it's tracked and excluded from future pools. Meruru adopts the reference's costume and pose while keeping her character lock and choosing a fresh background.

### Orchestrator Pattern
Python orchestrator sequencing `claude -p` calls with pre/post processing is proven reliable. The change: fewer calls, different prompts, same orchestration pattern.

---

## 11. Implementation Phases

### Phase 0: Visual Style Foundation (operator-driven) — ✅ COMPLETE

| Step | Action | Status |
|------|--------|--------|
| 0a | Operator selected 12 high-performance posted images from `media/posted/` | ✅ Done |
| 0b | Operator provided actual Higgsfield prompts for those images | ✅ Done |
| 0c | Analyzed patterns and wrote "My Visual Style" section in first-person voice | ✅ Done — saved at `docs/meruru_visual_style.md` |
| 0d | Operator approval | ✅ Approved Apr 7, 2026 |

**Output:** `docs/meruru_visual_style.md` — ready for integration into `config/meruru_identity.md` in Phase 1, Step 1.

### Phase 1: Foundation (Priority — get Meruru working end-to-end)

| Step | File | Action |
|------|------|--------|
| 1 | `config/meruru_identity.md` | **CREATE** — Expand `config/meruru_concept.md` into first-person identity. **Integrate `docs/meruru_visual_style.md` verbatim as Section 4 ("My Visual Style")**. |
| 2 | `scripts/feed_balance.py` | **CREATE** — Python feed balance + unused reference pool + usage tracking |
| 3 | `data/content/reference_usage.json` | **CREATE** — Initialize with `{"EN": [], "JP": []}` (empty pools). Schema example in Section 5.2. |
| 4 | `prompts/meruru.md` | **CREATE** — Unified Meruru creative prompt (6 candidates) |
| 5 | `scripts/orchestrator.py` | **MODIFY** — Add `run_create()` function |

### Phase 2: Integration (Wire into Telegram)

| Step | File | Action |
|------|------|--------|
| 6 | `scripts/telegram_bot.py` | **MODIFY** — Add `/create` and `/balance` commands |
| 7 | `scripts/orchestrator.py` | **MODIFY** — Add `run_balance()` function |
| 8 | `prompts/meruru_balance.md` | **CREATE** — Balance analysis prompt |
| 9 | `agents/marc_conversation.md` | **MODIFY** — Update for new architecture |

### Phase 3: Cleanup (Remove dead code)

| Step | File | Action |
|------|------|--------|
| 10 | `prompts/archive/` | **CREATE** dir — Move strategist.md, warroom.md, old creator.md, marc_review.md, outbound.md |
| 11 | `scripts/validate.py` | **MODIFY** — Remove strategist/cross validation modes; allow 6 posts in creator validation |
| 12 | `scripts/orchestrator.py` | **MODIFY** — Remove `run_warroom()`, deprecate `run_pipeline()` |
| 13 | `scripts/cron_wrapper.sh` | **MODIFY** — Replace `pipeline` with `create` |
| 14 | `~/Library/LaunchAgents/com.xagents.*.plist` | **MODIFY** — Update pipeline plist to call `create`; remove war room plists |
| 15 | `scripts/generate_html_report.py` | **MODIFY** — Render 6 candidates grouped by type (reference_based / creative) |
| 16 | `CLAUDE.md` | **MODIFY** — Update architecture documentation |

### Phase 4: Polish (Iterate on quality)

| Step | Action |
|------|--------|
| 17 | Tune Meruru prompt based on real output quality |
| 18 | Track which post type (reference_based vs creative) operator selects more often |
| 19 | Update `docs/context.md` with Session 49 changes |

---

## 12. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Meruru prompt bloats over time | Hard cap at 25K chars. Feed balance and references are pre-computed summaries, not raw data. |
| Single agent = no quality check | Python validate.py handles Tier 1. Operator is the creative quality gate. |
| Operator misses strategic layer | `/balance` provides the strategic input the operator actually wants. War Room can be reintroduced as optional tool later. |
| Backward compatibility | Keep `run_pipeline()` for 2-week fallback period. Remove after validation. |
| Feed balance is approximate | Only tracks system-generated plans, not manual posts. Mitigated by operator context parameter in `/create`. Stated clearly in docs — not authoritative, just directional. |
| Reference pool exhaustion | 247 references ÷ 3 per day = ~82 days of content. `get_unused_references()` warns when pool drops below 30. Operator adds new references to `media/reference/` and re-runs `scripts/analyze_references.py` to update the catalog. |
| JSON format compatibility | `category` field kept as free-form (Meruru chooses, not from fixed list). All downstream consumers (HTML report, Telegram commands, validation) tested during Phase 1. |
| JP account | Out of scope until account is restored. `/create JP` is technically supported but JP-specific content rules (grok_interactive, persona_dialogue) are not in the Meruru identity doc. Add when needed. |
| Multiple `/create` runs per day | Each run sees the latest content plans (including earlier same-day runs) in feed balance. Different reference images selected each time. Operator gets fresh plans. |
| Higgsfield prompt compatibility | Image prompt format preserves Higgsfield-compatible structured schema (meta, subject, outfit, pose, scene, camera, lighting, mood) and standard combined negative prompt. Not simplified — kept technical. |

---

## 13. Entry Points

```bash
# Create content plan (1 LLM call, Meruru as Opus)
python3 scripts/orchestrator.py create [EN|JP] ["optional operator context"]

# Feed balance analysis (1 LLM call, Meruru as Opus)
python3 scripts/orchestrator.py balance [EN|JP]

# Telegram bot (conversational Marc + command routing)
python3 scripts/telegram_bot.py

# LaunchAgent wrapper (scheduled daily at 06:00 JST)
./scripts/cron_wrapper.sh create
```

### Scheduled Automation (LaunchAgents)

| Schedule | Command | Purpose |
|----------|---------|---------|
| Daily 06:00 JST | `cron_wrapper.sh create` | Generate content plan overnight, ready for operator in morning |

**Posting schedule:** Fixed times, operator schedules manually on X. No LaunchAgent needed for posting.

**Removed schedules:** Morning/evening war rooms (removed in v5).

---

## 14. Verification Criteria

1. **`/create` produces content plan**: `orchestrator.py create EN` → valid JSON with 6 candidates (3 ref-based + 3 creative), passes Tier 1 validation, HTML report generated, sent to Telegram
2. **Captions have character**: Captions sound like Meruru, not like strategy artifacts. Operator uses them without heavy editing.
3. **Image prompts have variety**: 3 consecutive daily plans show diverse scene types across the 6 candidates (not just 1-2 settings repeated); poses, outfits, and moods vary within each plan and across days
4. **Reference adoption is faithful**: 3 reference-based posts each adopt a specific unused reference's costume and pose; reference filenames are tracked in `reference_usage.json` and not reused
5. **Creative posts have personality**: 3 creative posts feel like Meruru's own ideas, not random outputs; operator selects them at least sometimes (not 0% pick rate)
6. **Feed balance works**: `/balance` correctly identifies what's over/under-represented in the last 14 days
7. **Prompt is compact**: Meruru prompt < 25K chars (down from 100K+)
8. **Runtime is fast**: `/create` completes in < 5 minutes
9. **Operator time reduced**: Target 2-2.5 hrs/day (measured by operator feedback)
10. **Visual style section exists**: `meruru_identity.md` contains a "My Visual Style" section derived from posted images

---

*X-Agent Redesign v5 · Meruru as Unified Creative Agent · April 2026*
