# X AI Beauty Growth Agent System

## Architecture (v5 — Meruru as Unified Creative Agent)

The system uses **zero X API credits**. All X interactions (posting, likes, follows, replies) are done manually by the operator. The system focuses on character-driven content creation via a single LLM agent — **Meruru** — that holds her personality, visual style, voice, and feed awareness in one prompt.

**v5 (Session 49, April 7 2026)** collapsed the v4 multi-agent split (Strategist + Creator + Marc Review) into a single Meruru creative agent because no agent in v4 embodied the character. See `docs/x-agent-redesign-v5-architecture.md` for the full rationale.

1. **Orchestrator** (`scripts/orchestrator.py`) — Python script. Handles all mechanical coordination: feed balance computation, unused reference pool, prompt building, validation, file saves, Telegram delivery. Zero LLM cost for coordination.
2. **Conversational Layer** (`scripts/telegram_bot.py`) — Marc responds to operator messages via `claude -p` (Sonnet). Commands route to the orchestrator.
3. **Meruru** (Opus, single LLM agent) — Invoked by orchestrator via `claude -p` with the unified prompt at `prompts/meruru.md`. She is the strategist + creator + reviewer in one entity.

### Primary Flows (v5)

**`/create` — Daily content plan (1 LLM call, ~3-5 min)**
```
orchestrator.py create [--account EN] [--context "optional steering"]
  1. analyze_references.py             # Python (auto-pickup of new references)
  2. feed_balance.compute_feed_balance() # Python (instant, no LLM)
  3. feed_balance.get_unused_references() # Python (instant)
  4. Build Meruru prompt                  # Python — ~30K chars
  5. claude -p Meruru (Opus, ~3-5 min)    # LLM 1 — generates 6 candidates
  6. validate.py creator                  # Python — Tier 1 only
  7. feed_balance.mark_references_used()  # Python — single-use tracking
  8. Save content_plan_{date}_EN.json
  9. Generate HTML report
  10. Send to Telegram
```

Output: 6 candidate posts (3 reference-based + 3 creative). Operator picks 4 to actually post on X.

**`/balance` — Feed balance check (1 LLM call, ~10-15 sec)**
```
orchestrator.py balance [--account EN]
  1. feed_balance.compute_feed_balance()  # Python
  2. claude -p Meruru balance (Opus)      # LLM 1 — interprets balance, recommends
  3. Send recommendation to Telegram
```

Operator runs this when they want a quick read on what's missing in the feed.

### Automation (LaunchAgent)

| Schedule | Command | Purpose |
|---|---|---|
| Daily 06:00 JST | `cron_wrapper.sh create` (`com.xagents.create.plist`) | Generates content plan overnight, ready when operator wakes up |

War room LaunchAgents (`morning_warroom`, `evening_warroom`, `pipeline`) are unloaded but the .plist files are kept in `~/Library/LaunchAgents/` for fallback re-enabling.

### Reference image system

The operator curates reference images in `media/reference/`. They're auto-analyzed into `data/content/reference_catalog.json`. For each `/create` run, Meruru receives 8-12 **unused** references with one-line summary + outfit + pose. She picks 3 (one per ref-based post) and adopts each one's costume + pose while keeping her character lock and choosing a fresh background. Single-use tracking in `data/content/reference_usage.json` prevents reuse.

### Removed in v5
- **Strategist agent** — feed balance (Python) replaces content_mix percentages and creative briefs
- **Creator agent (separate)** — Meruru is the creator
- **Marc Review (LLM)** — replaced with Python-only Tier 1 validation
- **War Room flow** — operator never reviewed outputs; feedback loop amplified wrong signal
- **Standing Directives system** — coordination mechanism for multi-agent communication; single agent embeds rules in identity

### Legacy v4 (kept temporarily for fallback)
- `orchestrator.py pipeline` — Strategist + Creator + Marc Review
- v4 prompts archived at `prompts/archive/` (loaded automatically via `build_prompt()` fallback)
- Will be removed after ~2 weeks of stable v5 operation

### Discontinued (no longer used)
- scout.py, analyst.py collect, publisher.py, publisher_outbound_data.py
- research_engagers.py, outbound_context.py, outbound flow
- War room morning/evening sessions

## Global Rules
@config/global_rules.md

## Documentation
- All project docs live in `docs/`
- v5 architecture: `docs/x-agent-redesign-v5-architecture.md`
- v4 architecture (historical): `docs/x-agent-redesign-architecture.md`
- Project context: `docs/context.md`
- Agent building guide: `docs/guides/agent-building-guidelines.md`

## Project Context
- Two accounts: EN (global) and JP (日本市場)
- Account status tracked in `config/account_status.json` (EN active via sub-account @meruru_tcbn, JP suspended)
- When account status changes, update `config/account_status.json`
- X API: pay-as-you-go, project not profitable — system is designed to use zero API
- Operator posts manually on X; content plan `status: "draft"` is the expected end state
- All Telegram communication goes through Marc (COO)

## Agent Definitions
- `agents/marc_conversation.md` — Conversational Marc (Telegram interaction, v5-aware)
- `config/meruru_identity.md` — Meruru's first-person identity (personality, voice, body lock, visual style, content balance)
- `prompts/meruru.md` — Unified Meruru creative prompt (6 candidates per run)
- `prompts/meruru_balance.md` — Lightweight balance-check prompt
- `prompts/archive/` — Legacy v4 prompts (strategist, creator, marc_review, warroom, outbound)

## Supporting Scripts (no LLM, no API)
- `scripts/feed_balance.py` — Feed balance computation + unused reference pool + usage tracking
- `scripts/validate.py` — Output validation (Tier 1 enforcement, accepts 6 posts)
- `scripts/generate_html_report.py` — HTML report generation (groups posts by type)
- `scripts/analyze_references.py` — Auto-analyzes new images dropped into `media/reference/`
- `scripts/telegram_send.py` — Send messages/documents via Telegram
- `scripts/analyst.py import` — Import operator-provided metrics CSV (legacy, optional)
- `scripts/analyst.py summary` — Generate metrics summary from local SQLite (legacy, optional)

## Content Quality
- Meruru's visual style is in `config/meruru_identity.md` Section 4 (derived from 12 high-performance posted images)
- Image prompts follow Higgsfield-compatible structured schema: see `config/image_prompt_guide.md`
- Tier 1 constraints (enforced by `validate.py`): character lock, iPhone camera, negative prompt, prompt length, hashtag policy, caption length
- Captions: character-first, 30-100 chars EN, lowercase, no generic engagement bait
- 6 candidates per plan: 3 reference-based + 3 creative

## Shared Conventions
- Date format: ISO 8601
- All times in JST
- Post IDs: {account}_{YYYYMMDD}_{slot} (slots 1-6 in v5)
- Log format: [YYYY-MM-DD HH:MM:SS] [AGENT] [LEVEL] message

## Preferences
- In interactive sessions (direct CLI use): Don't try to run scripts with bash tool. Write the script and tell me how to execute it, asking me for its output instead.
- In non-interactive sessions (telegram bot execution, orchestrator.py): Execute ALL scripts directly. The operator is not watching.
