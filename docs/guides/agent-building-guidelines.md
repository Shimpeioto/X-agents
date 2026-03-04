# Agent Building Guidelines

A practical guide for building new agents in the X-Agents system. Covers principles,
architecture patterns, file conventions, and integration steps — distilled from
the patterns established across Scout, Strategist, Creator, Publisher, and Analyst.

---

## Table of Contents

1. [Principles](#1-principles)
2. [Decision Framework](#2-decision-framework)
3. [Agent Anatomy](#3-agent-anatomy)
4. [Script Companion](#4-script-companion)
5. [I/O Contract](#5-io-contract)
6. [Orchestration Integration](#6-orchestration-integration)
7. [Validation & Error Handling](#7-validation--error-handling)
8. [Testing](#8-testing)
9. [New Agent Checklist](#9-new-agent-checklist)
10. [References](#10-references)

---

## 1. Principles

Eight principles govern how agents are designed and built in this system. Every
decision about a new agent should trace back to one or more of these.

### 1.1 Harness as OS

The agent harness (shell scripts, validate.py, pipeline state) is the operating
system; Claude is the CPU; the context window is RAM; `data/` is the file system.
Agents are applications running on this OS.

| OS Concept | Maps To |
|---|---|
| CPU | Claude model (reasoning engine) |
| RAM | Context window (per-invocation, fresh each time) |
| Operating System | Shell scripts + validate.py + pipeline state |
| Application | Agent instance (skill file + task prompt) |
| File System | `data/` directory (JSON, SQLite) |
| IPC | File-based JSON exchange between agents |

This analogy (Schmid 2026) means: agents should not try to be the OS. They
should focus on their application logic and trust the harness for orchestration,
validation, state tracking, and error recovery.

### 1.2 Validation-First

Every agent output passes through `scripts/validate.py` before the pipeline
continues. Design your agent's output schema first, then write validation rules,
then build the agent. The validation layer is the contract enforcement mechanism.

### 1.3 Specialist Isolation

Each `claude -p` invocation is a fresh context. Agents never share state through
the context window — only through files. This prevents cross-contamination and
makes each agent independently testable.

A single agent should do one thing well. If you find an agent doing two unrelated
things, split it.

### 1.4 Minimal Tools Per Agent

Each agent gets the minimum set of tools it needs:

| Agent | Tools |
|---|---|
| Scout | X API read only |
| Strategist | File read/write only |
| Creator | File read/write only |
| Publisher | X API write + media upload + rate limits |
| Analyst | X API read + SQLite write |
| Marc | Subagent invocation + file read/write + Telegram |

When designing a new agent, ask: "What is the absolute minimum this agent needs
to touch?" Grant only that. This limits blast radius when things go wrong.

### 1.5 Progressive Disclosure

Don't put everything in one file. Load instructions only when needed.

Marc demonstrates this pattern — the hub file (`marc.md`, ~131 lines) contains
identity, task handling, and agent team reference. Pipeline steps, publishing
steps, and schemas live in separate files loaded on demand. This keeps context
windows lean.

Rule of thumb: if a skill file exceeds ~200 lines, consider splitting it into a
hub (identity + routing) and reference documents (mode-specific instructions).

### 1.6 Claude Is Smart — Be Concise

Anthropic's best practices: "Claude is smart enough to fill in gaps. Write less,
trust more." Don't over-specify. Give the model clear constraints (schemas,
validation rules, format rules) and let it reason about the content.

What to specify explicitly:
- Output schema (exact JSON structure)
- Validation rules (what will be checked)
- Constraints (limits, forbidden patterns)
- Format rules ("Output ONLY valid JSON — no markdown fences, no commentary")

What to leave implicit:
- How to think about the problem
- Step-by-step reasoning instructions
- Obvious inferences from the data

### 1.7 Human Gating at Decision Points

Content follows a strict status flow: `draft -> approved -> posted`. No content
reaches X without human approval via Telegram. This is non-negotiable.

When designing a new agent, identify its decision points — places where a wrong
output could cause irreversible harm. Add human gates there.

### 1.8 Errors Are Context, Not Dead Ends (H3 Pattern)

When a subagent fails, Marc reads the error, crafts a targeted retry prompt that
includes the specific failure, and retries once. The error becomes context for
the retry — not "try again" but "fix this specific issue."

Design your agent to produce useful error messages. When validation fails, the
failure description should contain enough information for Marc to craft a
targeted retry.

---

## 2. Decision Framework

Before creating a new agent, determine the right approach.

### When to Create a New Agent

Create a new agent when ALL of these are true:
- The task is a recurring responsibility (not a one-off)
- It requires a distinct expertise or perspective
- It produces structured output consumed by other agents
- It needs its own tool set (principle 1.4)

### When to Extend an Existing Agent

Extend an existing agent when:
- The new task shares the same tools and data sources
- It fits naturally as a new "mode" of an existing agent
- Adding it doesn't push the skill file past ~200 lines

### When to Use a Script Only

Use a standalone script (no skill file) when:
- The task is purely deterministic (no LLM reasoning needed)
- Input → output is a fixed transformation
- Examples: validate.py, db_manager.py, telegram_send.py

### Decision Matrix

| Criteria | New Agent | Extend Existing | Script Only |
|---|---|---|---|
| Needs LLM reasoning | Yes | Yes | No |
| Distinct tool set | Yes | No | N/A |
| Recurring task | Yes | Yes | Yes |
| Structured output schema | Yes | Yes | Yes |
| Consumes other agents' output | Usually | Usually | Sometimes |
| Deterministic logic | Partial | Partial | Fully |

---

## 3. Agent Anatomy

### 3.1 Skill File Structure

Every agent skill file follows this section order:

```markdown
<!-- Agent Metadata (YAML-like comment block) -->

# {Agent Name} — {Role Description}

## Identity & Goal           (who you are, what you optimize for)
## Modes                     (if multiple operating modes)
## Step 1: Read Inputs       (what to read, from where)
## Step 2: Process           (what to analyze/generate)
## Step N: ...               (additional steps as needed)
## Output Schema             (exact JSON structure with ```json block)
## Validation Rules          (numbered list the agent MUST satisfy)
## Format Rules              (output-only constraints)
## Error Handling            (if the agent has error scenarios)
## CLI Usage                 (if backed by a Python script)
```

### 3.2 Agent Metadata Header

Every skill file starts with a metadata comment block:

```markdown
<!-- Agent Metadata
name: agent_name
role: Brief Role Description
invocation: how Marc invokes this agent
modes: comma-separated list of operating modes
inputs: what files/data this agent reads
outputs: what files this agent produces
dependencies: which agents must run before this one
-->
```

This metadata is for human reference and tooling — it is not parsed by Claude
but provides quick orientation when scanning agent files.

### 3.3 Naming Conventions

| Thing | Convention | Example |
|---|---|---|
| Skill file | `agents/{name}.md` | `agents/scout.md` |
| Hub file (if split) | `agents/{name}.md` | `agents/marc.md` |
| Reference file | `agents/{name}_{topic}.md` | `agents/marc_pipeline.md` |
| Python script | `scripts/{name}.py` | `scripts/scout.py` |
| Log agent name | `[AGENT_NAME]` uppercase | `[SCOUT]`, `[PUBLISHER]` |
| Pipeline task ID | `{phase}_{action}` | `pipeline_scout`, `publish_post_en` |
| Subagent prompt | "You are the {Name} agent..." | "You are the Scout agent..." |

### 3.4 When to Split a Skill File

Split when any of these apply:
- File exceeds ~200 lines
- Agent has 3+ distinct operating modes
- Schemas or step sequences are long enough to dominate the file

Current agent line counts for reference:

| File | Lines | Notes |
|---|---|---|
| `marc.md` | ~131 | Hub — identity + task handling |
| `marc_pipeline.md` | ~201 | Pipeline steps 1-13 |
| `marc_publishing.md` | ~138 | Publishing steps P1-P8 |
| `marc_schemas.md` | ~140 | Schemas and formats |
| `scout.md` | ~119 | Single file (two modes) |
| `strategist.md` | ~165 | Single file (two modes) |
| `creator.md` | ~145 | Single file (one mode) |
| `publisher.md` | ~88 | Single file (two modes via CLI) |
| `analyst.md` | ~155 | Single file (three modes via CLI) |

Marc was split because it exceeded 400+ lines as a single file. Scout,
Strategist, Creator, Publisher, and Analyst are each under 200 lines and remain
as single files.

### 3.5 New Agent Template

Copy this as a starting point for any new agent:

```markdown
<!-- Agent Metadata
name: {agent_name}
role: {Brief Role Description}
invocation: {python3 scripts/{name}.py | Claude subagent with agents/{name}.md}
modes: {mode1, mode2}
inputs: {input files or data sources}
outputs: {output file pattern}
dependencies: {agent names that must run before this one}
-->

# {Agent Name} — {Role Description}

## Identity & Goal

You are {Name}, the {role description}. Your goal is to {primary objective}.

## Step 1: Read Inputs

1. Read {input file} at the path provided in the prompt
2. Read `config/global_rules.md` for constraints
3. The prompt tells you {what context Marc provides}

## Step 2: {Core Processing}

{Describe what the agent analyzes, generates, or transforms.}

## Output Schema

Write valid JSON to the file path specified in the prompt:

\```json
{
  "date": "YYYY-MM-DD",
  "generated_at": "ISO 8601 timestamp with timezone",
  "{input_reference}": "{path to input file used}",
  "data": {}
}
\```

## Validation Rules

1. {Rule 1 — structural check}
2. {Rule 2 — field presence}
3. {Rule 3 — value constraint}
4. {Rule 4 — business logic}

## Format Rules

Output ONLY valid JSON — no markdown fences, no commentary.
First character `{`, last character `}`.
```

---

## 4. Script Companion

### 4.1 When an Agent Needs a Python Script

An agent needs a companion script when:
- It makes API calls (X API, Telegram, external services)
- It writes to a database (SQLite)
- It needs deterministic control flow (rate limiting, retry logic, file I/O)
- It performs operations that must not vary between runs

Agents that are purely analytical or creative (Strategist, Creator) typically
don't need scripts — they run as Claude subagents and write JSON to files.

Current script assignments:

| Agent | Script | Why |
|---|---|---|
| Scout | `scout.py` | X API reads, 50+ API calls per run |
| Publisher | `publisher.py` | X API writes, rate limiting, media upload |
| Analyst | `analyst.py` | X API reads, SQLite writes, batch queries |
| Marc | (shell scripts) | `run_pipeline.sh`, `run_task.sh` for entry |
| Strategist | (none) | Pure Claude subagent, file I/O only |
| Creator | (none) | Pure Claude subagent, file I/O only |

### 4.2 Script Structure Template

```python
#!/usr/bin/env python3
"""
{Agent Name} Agent — {Brief Description}

Usage:
    python3 scripts/{name}.py [command] [options]
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Project path setup ---
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [{AGENT_NAME}] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- Timezone ---
JST = ZoneInfo("Asia/Tokyo")


def load_json(path: str) -> dict | None:
    """Load JSON file with code-fence stripping."""
    try:
        with open(path) as f:
            content = f.read().strip()
        # Strip markdown code fences (defensive against LLM output)
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load {path}: {e}")
        return None


def save_json(path: str, data: dict) -> None:
    """Write JSON to file with pretty formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {path}")


def today_str() -> str:
    """Return today's date as YYYYMMDD in JST."""
    return datetime.now(JST).strftime("%Y%m%d")


def main():
    parser = argparse.ArgumentParser(
        description="{Agent Name} Agent — {Brief Description}"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Log actions without executing")

    # --- Subcommands (if needed) ---
    subparsers = parser.add_subparsers(dest="command")
    cmd1 = subparsers.add_parser("command1", help="...")
    cmd1.add_argument("--account", choices=["EN", "JP"])
    # Add more subcommands as needed

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN — no side effects")

    if args.command == "command1":
        run_command1(args)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
```

### 4.3 Code-Fence Stripping

Claude subagents sometimes wrap JSON output in markdown triple backticks, even
when instructed not to. Every `load_json()` function includes defensive stripping:

```python
if content.startswith("```"):
    lines = content.split("\n")
    lines = [l for l in lines if not l.strip().startswith("```")]
    content = "\n".join(lines)
```

This is a project-wide convention. Always include it in `load_json()`.

### 4.4 Logging Convention

All scripts use the same format:

```
[2026-03-04 14:30:00] [SCOUT] [INFO] Starting competitor scan...
[2026-03-04 14:30:01] [SCOUT] [WARNING] Account @example suspended, skipping
[2026-03-04 14:30:02] [SCOUT] [ERROR] Rate limit hit, waiting 60s
```

Pattern: `[%(asctime)s] [{AGENT_NAME}] [%(levelname)s] %(message)s`

The agent name is hardcoded per script — not derived from the Python logger name.
Use uppercase: `[SCOUT]`, `[PUBLISHER]`, `[ANALYST]`, etc.

### 4.5 Exit Codes

| Code | Meaning | When |
|---|---|---|
| 0 | Success | Normal completion, including "nothing to do" |
| 1 | Failure | Unrecoverable error (missing file, API auth failure) |
| 2 | Usage error | Bad arguments, missing required flags |

Marc checks exit codes to decide whether to proceed or trigger error recovery.

### 4.6 Shared Libraries

Import from the `scripts/` directory:

| Library | Purpose | Key Exports |
|---|---|---|
| `x_api.py` | X API client | `XApiClient` (read), `XApiWriteClient` (write) |
| `db_manager.py` | SQLite operations | `init()`, `insert_*()`, `get_*()` |
| `telegram_send.py` | Telegram messaging | `send_message()`, `send_document()` |

To import:
```python
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))
from x_api import XApiClient
from db_manager import DBManager
```

---

## 5. I/O Contract

### 5.1 File Naming Conventions

| Pattern | Example | Written By |
|---|---|---|
| `data/scout_report_{YYYYMMDD}.json` | `scout_report_20260304.json` | Scout |
| `data/strategy_{YYYYMMDD}.json` | `strategy_20260304.json` | Strategist |
| `data/strategy_current.json` | `strategy_current.json` | Marc only |
| `data/content_plan_{YYYYMMDD}_{account}.json` | `content_plan_20260304_EN.json` | Creator |
| `data/pipeline_state_{YYYYMMDD}.json` | `pipeline_state_20260304.json` | Marc |
| `data/rate_limits_{YYYYMMDD}.json` | `rate_limits_20260304.json` | Publisher |
| `data/outbound_log_{YYYYMMDD}.json` | `outbound_log_20260304.json` | Publisher |
| `data/metrics_{YYYYMMDD}_{account}.json` | `metrics_20260304_EN.json` | Analyst |
| `data/metrics_history.db` | (fixed name) | Analyst |
| `media/pending/{post_id}.{ext}` | `pending/EN_20260304_01.png` | Human |
| `media/posted/{post_id}.{ext}` | `posted/EN_20260304_01.png` | Publisher |

### 5.2 Dated vs. Current Files

Agents always write dated files (`strategy_20260304.json`). Marc promotes the
latest to `_current` files (`strategy_current.json`) at the end of a successful
pipeline run. This preserves history while giving downstream consumers a stable
path.

When designing a new agent:
- Your agent writes: `data/{type}_{YYYYMMDD}.json`
- Marc promotes: `data/{type}_current.json` (if needed by downstream agents)

### 5.3 Post ID Format

Pattern: `{account}_{YYYYMMDD}_{slot}` with zero-padded 2-digit slot number.

```
EN_20260304_01    ← Account EN, March 4 2026, slot 1
JP_20260304_03    ← Account JP, March 4 2026, slot 3
```

Post IDs are created by Creator and used by Publisher, Analyst, and the metrics
database as the primary identifier for a piece of content.

### 5.4 Date Handling

| Context | Format | Example |
|---|---|---|
| JSON field values | ISO 8601 (`YYYY-MM-DD`) | `"2026-03-04"` |
| Timestamps | ISO 8601 with timezone | `"2026-03-04T14:30:00+09:00"` |
| Filenames | `YYYYMMDD` (no hyphens) | `scout_report_20260304.json` |
| Timezone | JST (Asia/Tokyo) always | `ZoneInfo("Asia/Tokyo")` |
| Log timestamps | `YYYY-MM-DD HH:MM:SS` | `[2026-03-04 14:30:00]` |

All dates and times are in JST unless explicitly noted otherwise. EN posting
times use UTC in strategy schedules, but file dates are always JST.

### 5.5 Schema Evolution

When you need to change an existing schema:
1. Add new fields as optional (with sensible defaults) — don't break existing consumers
2. Update `scripts/validate.py` to check the new fields
3. Update the agent's skill file schema documentation
4. Update `marc_schemas.md` if it's a pipeline state or report format change
5. Run validation against the most recent existing file to confirm backward compatibility

### 5.6 Data Flow Map

```
                    config/competitors.json
                            |
                            v
  Scout (scout.py) ---> data/scout_report_{date}.json
                            |
                            v
  Strategist (subagent) --> data/strategy_{date}.json
                            |
                     +------+------+
                     |             |
                     v             v
  Creator EN    Creator JP
  (subagent)    (subagent)
     |               |
     v               v
  content_plan    content_plan
  _{date}_EN      _{date}_JP
     |               |
     +------+--------+
            |
     [Human Approval via Telegram]
            |
            v
  Publisher (publisher.py) ---> posted tweets + outbound log
                            |
                            v
  Analyst (analyst.py) ---> data/metrics_{date}_{account}.json
                            + data/metrics_history.db
```

---

## 6. Orchestration Integration

### 6.1 How Marc Invokes Agents

Marc uses two invocation patterns:

**Pattern A — Python Script** (for API-heavy, deterministic agents):
```bash
python3 scripts/{name}.py {command} --account {EN|JP} [--dry-run]
```
Used by: Scout, Publisher, Analyst

**Pattern B — Claude Subagent** (for reasoning-heavy agents):
```bash
claude -p "{prompt}" --dangerously-skip-permissions
```
Used by: Strategist, Creator

### 6.2 Subagent Prompt Template

When Marc spawns a Claude subagent, the prompt must include these 8 elements:

```
1. Identity:     "You are the {Name} agent."
2. Instructions: "Read agents/{name}.md, section '{Mode}' for your instructions."
3. Date:         "Today's date: {YYYY-MM-DD}"
4. Input paths:  "Read the scout report at data/scout_report_{date}.json"
5. Output path:  "Write your output to data/{output}_{date}.json"
6. Account:      "Generate for the {EN|JP} account" (if account-specific)
7. Context:      Any additional context (retry feedback, previous output, etc.)
8. Format rule:  "Output ONLY valid JSON — no markdown fences, no commentary."
```

Example (Creator invocation):
```
You are the Creator agent. Read agents/creator.md for your instructions.
Today's date: 2026-03-04
Read the strategy at data/strategy_20260304.json
Write your output to data/content_plan_20260304_EN.json
Generate content for the EN account.
Output ONLY valid JSON — no markdown fences, no commentary.
```

### 6.3 Registering a New Agent with Marc

To add a new agent to the system, update these 5 locations:

**1. `agents/marc.md` — Agent Team table**

Add a row to the "Agent Team" table with the agent's role, invocation method,
and what it's best for.

**2. `CLAUDE.md` — Agent Definitions**

Add a line: `- @agents/{name}.md — {Brief Role}`

**3. `CLAUDE.md` — Tool Assignment**

Add a line: `- {Name}: {tools this agent uses}`

**4. `scripts/validate.py` — Validation mode**

Add a new validation function `validate_{name}()` and register it in the
mode dispatch. This is how Marc confirms the agent's output is well-formed.

**5. `agents/marc_pipeline.md` or `marc_publishing.md`** (if the agent is part
of the daily pipeline or publishing flow)

Add the appropriate step(s) to the pipeline or publishing sequence, including
validation and error handling.

### 6.4 Pipeline State Task Entry

If your agent participates in the pipeline, it needs task IDs registered in
`marc_schemas.md`. Each task entry in `pipeline_state_{date}.json` looks like:

```json
{
  "task_id": "pipeline_{agent_name}",
  "status": "pending|running|done|failed|skipped",
  "started_at": null,
  "completed_at": null,
  "output_path": "data/{output}_{date}.json",
  "errors": [],
  "warnings": [],
  "retries": 0
}
```

Valid task ID prefixes: `pipeline_` (daily pipeline), `publish_` (publishing),
`metrics_` (metrics collection).

---

## 7. Validation & Error Handling

### 7.1 Adding Validation for a New Agent

Step-by-step:

1. **Define checks** — List every structural and business rule your agent's
   output must satisfy.

2. **Add a mode to validate.py** — Create a function `validate_{name}()`:

```python
def validate_{name}(file_path: str) -> tuple[list[str], list[str]]:
    """Validate {name} agent output. Returns (issues, warnings)."""
    issues = []
    warnings = []

    data = load_json_safe(file_path)
    if data is None:
        return ["{name}_file: Could not load or parse JSON"], []

    # --- Structural checks ---
    if "date" not in data:
        issues.append("{name}_date: Missing 'date' field")

    if "generated_at" not in data:
        issues.append("{name}_generated_at: Missing 'generated_at' field")

    # --- Field type checks ---
    if not isinstance(data.get("items", []), list):
        issues.append("{name}_items_type: 'items' must be an array")

    # --- Business rule checks ---
    # Add domain-specific validation here

    return issues, warnings
```

3. **Register the mode** — Add it to the dispatch in `validate.py`:

```python
if mode == "{name}":
    issues, warnings = validate_{name}(file_path)
```

4. **Add to Marc's pipeline** — After Marc invokes your agent, add a validation
   step that calls `python3 scripts/validate.py {name} {output_path}`.

### 7.2 Validation Check Categories

Organize checks in this order (each level builds on the previous):

| Level | Category | Example |
|---|---|---|
| 1 | File exists | Can the file be opened? |
| 2 | Valid JSON | Does `json.loads()` succeed? |
| 3 | Required fields | Are `date`, `generated_at`, etc. present? |
| 4 | Type checks | Is `posts` an array? Is `total_posts` an integer? |
| 5 | Value constraints | Is `content_mix` sum == 100? Is `daily_likes` <= 30? |
| 6 | Business rules | Do post IDs match `{account}_{date}_{slot}` format? |
| 7 | Cross-validation | Does content plan match strategy's posting schedule? |

Levels 1-5 are per-agent. Level 6 is per-agent with domain logic. Level 7
requires comparing two agent outputs (Marc handles cross-validation).

### 7.3 Issue String Format

All validation issues follow this format:

```
{check_id}: {description}
```

The `check_id` is a unique identifier per check, typically `{agent}_{field}` or
`{agent}_{rule}`. This makes issues grep-able and trackable.

Examples:
```
strategist_content_mix_sum: EN content_mix sums to 95, expected 100
creator_post_id_format: Post id 'EN-20260304-1' doesn't match expected format
publisher_rate_limits: EN daily_likes (35) exceeds limit (30)
```

### 7.4 H3 Error Recovery Protocol

When validation fails, Marc follows this protocol:

1. **Read** — Parse the validation output (`FAIL: N of M checks failed.`) and
   the list of specific issues.

2. **Diagnose** — Identify the root cause. Is it bad JSON? Missing field?
   Business rule violation? The issue strings tell Marc exactly what failed.

3. **Craft retry prompt** — Build a new subagent prompt that includes:
   - The original instructions
   - The previous output path (so the agent can read what it produced)
   - The specific error message(s)
   - Explicit instruction to fix the specific issue(s)

4. **Retry once** — Spawn the subagent with the improved prompt.

5. **Stop after two failures** — If the retry also fails, log both attempts
   with full error details and halt. Don't retry indefinitely.

Example retry prompt:
```
You are the Strategist agent. Read agents/strategist.md for your instructions.
Today's date: 2026-03-04

IMPORTANT: Your previous output at data/strategy_20260304.json failed validation:
- strategist_content_mix_sum: EN content_mix sums to 95, expected 100
- strategist_jp_hashtags: JP hashtag_strategy.always_use is empty

Fix these specific issues. Read your previous output, correct the problems,
and write the fixed version to the same path.
Output ONLY valid JSON — no markdown fences, no commentary.
```

### 7.5 Harness Evolution (H2)

Over time, track which validation checks actually catch real issues:

- **Checks that fire regularly** — These earn their keep. Keep them.
- **Checks that never fire** (after 10+ runs) — Candidates for removal. The
  model has learned the pattern.
- **Checks that fire on first run but not after** — The retry mechanism taught
  the model. Consider simplifying.

The goal is a validation layer that gets simpler over time as model outputs
stabilize. Review at each phase boundary.

---

## 8. Testing

### 8.1 Dry-Run Mode

Every operational script supports `--dry-run`:

```bash
python3 scripts/scout.py --dry-run
python3 scripts/publisher.py --dry-run post --account EN
python3 scripts/analyst.py --dry-run collect
```

In dry-run mode: log what would happen, skip all API calls and file mutations.
Exit 0 on success. This is the first test for any script change.

### 8.2 Max-N Flags

Scripts with iterative operations support `--max-N` flags to limit scope:

```bash
python3 scripts/scout.py --max-competitors 1    # Test with 1 competitor
python3 scripts/scout.py --max-competitors 5    # Test with 5
```

When adding a new script with iterable operations, include a `--max-{items}`
flag for testing.

### 8.3 Isolated Agent Testing

Test a Claude subagent in isolation (no pipeline, no Marc):

```bash
claude -p "You are the {Name} agent. Read agents/{name}.md for your instructions.
Today's date: 2026-03-04
Read {input path}
Write your output to data/test_{name}_output.json
Output ONLY valid JSON — no markdown fences, no commentary." \
  --dangerously-skip-permissions
```

Then validate:
```bash
python3 scripts/validate.py {name} data/test_{name}_output.json
```

This tests the agent without Marc's orchestration layer. Fix any issues before
integrating into the pipeline.

### 8.4 Validation Testing

Test your validation function with these scenarios:

| Scenario | Input | Expected Result |
|---|---|---|
| Good output | Valid agent output | `PASS` |
| Broken JSON | `{"incomplete": ` | `FAIL` (level 2) |
| Empty file | `` | `FAIL` (level 1/2) |
| Missing file | Non-existent path | `FAIL` (level 1) |
| Code-fenced JSON | `` ```json\n{...}\n``` `` | `PASS` (after stripping) |
| Missing fields | Valid JSON, missing required keys | `FAIL` (level 3) |
| Constraint violation | Values out of range | `FAIL` (level 5) |

### 8.5 Pipeline Testing Sequence

When integrating a new agent into the pipeline, follow this sequence:

1. **Dry-run script** (if applicable):
   ```bash
   python3 scripts/{name}.py --dry-run {command}
   ```

2. **Isolated agent test** (subagent without Marc):
   ```bash
   claude -p "..." --dangerously-skip-permissions
   ```

3. **Validate output**:
   ```bash
   python3 scripts/validate.py {name} data/{output}.json
   ```

4. **Dry-run pipeline** (full pipeline with all scripts in dry-run):
   ```bash
   # Run pipeline with DRY_RUN=1 environment variable
   ```

5. **Limited live run** (max-N flags where available):
   ```bash
   python3 scripts/{name}.py --max-{items} 1 {command}
   ```

6. **Full live run** (no limits, real API calls):
   ```bash
   python3 scripts/{name}.py {command}
   ```

---

## 9. New Agent Checklist

### Before You Start

- [ ] Confirm the agent needs to exist (see Decision Framework, Section 2)
- [ ] Identify the agent's single responsibility
- [ ] Identify minimum tool set (Principle 1.4)
- [ ] Identify input files and output schema
- [ ] Identify which existing agents it depends on and which depend on it

### Skill File

- [ ] Create `agents/{name}.md` with metadata header
- [ ] Define Identity & Goal section
- [ ] Define all operating modes
- [ ] Document input reading steps
- [ ] Define exact output JSON schema
- [ ] Write numbered validation rules
- [ ] Add format rules ("Output ONLY valid JSON...")
- [ ] Keep under ~200 lines (split if larger)
- [ ] All times referenced in JST

### Script (if needed)

- [ ] Create `scripts/{name}.py`
- [ ] Include `PROJECT` path setup
- [ ] Include logging with `[{AGENT_NAME}]` format
- [ ] Include `load_json()` with code-fence stripping
- [ ] Include `save_json()` helper
- [ ] Include `--dry-run` flag
- [ ] Include `--max-{items}` flag (if iterative)
- [ ] Use shared libraries (`x_api.py`, `db_manager.py`) — don't duplicate
- [ ] Exit codes: 0 (success), 1 (failure), 2 (usage error)
- [ ] All timestamps in JST (`ZoneInfo("Asia/Tokyo")`)

### Validation

- [ ] Add `validate_{name}()` function to `scripts/validate.py`
- [ ] Cover all 7 validation levels (file → JSON → fields → types → constraints → business → cross)
- [ ] Use `{name}_{check}` format for issue strings
- [ ] Register mode in validate.py dispatch
- [ ] Test with good, broken, empty, missing, and code-fenced inputs

### Marc Integration

- [ ] Add agent to Marc's "Agent Team" table in `agents/marc.md`
- [ ] Add to `CLAUDE.md` Agent Definitions section
- [ ] Add to `CLAUDE.md` Tool Assignment section
- [ ] Add pipeline/publishing steps to `marc_pipeline.md` or `marc_publishing.md` (if applicable)
- [ ] Add task IDs to `marc_schemas.md` (if applicable)
- [ ] Write Marc's invocation prompt (8 required elements)

### File Conventions

- [ ] Output file follows `data/{type}_{YYYYMMDD}[_{account}].json` pattern
- [ ] Dates in filenames: `YYYYMMDD` (no hyphens)
- [ ] Dates in JSON fields: `YYYY-MM-DD`
- [ ] Timestamps: ISO 8601 with timezone
- [ ] Post IDs (if applicable): `{account}_{YYYYMMDD}_{slot}`

### Testing

- [ ] Dry-run passes without errors
- [ ] Isolated agent test produces valid output
- [ ] Validation passes on good output
- [ ] Validation catches bad output (all 7 levels)
- [ ] Limited live run succeeds (max-N)
- [ ] Full live run succeeds

### Documentation

- [ ] Update `docs/harness.md` file layout if new files added
- [ ] Update data flow map if pipeline changes
- [ ] Add any new global rules to `config/global_rules.md`

---

## 10. References

1. [The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Anthropic
2. [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Anthropic Platform Docs
3. [Extend Claude with skills](https://code.claude.com/docs/en/skills) — Claude Code Docs
4. [The importance of Agent Harness in 2026](https://www.philschmid.de/agent-harness-2026) — Phil Schmid
5. [Lessons from Building Claude Code: Seeing Like an Agent](https://www.techtwitter.com/articles/lessons-from-building-claude-code-seeing-like-an-agent) — Tech Twitter
6. [SkillsMP marketplace](https://skillsmp.com) — Skills Marketplace
7. [anthropics/skills repo — skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) — Anthropic GitHub

---

## Related Documentation

- [Harness Architecture](../harness.md) — Three-layer model, OS analogy, key patterns
- [Marc Pipeline](../../agents/marc_pipeline.md) — Full pipeline steps 1-13
- [Marc Publishing](../../agents/marc_publishing.md) — Publishing steps P1-P8
- [Marc Schemas](../../agents/marc_schemas.md) — Pipeline state and report formats
- [Add Competitor Procedure](../procedures/add-competitor.md) — Example of a documented procedure
