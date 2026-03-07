"""Telegram bot daemon with conversational Marc + Agent Teams execution.

Architecture:
    Conversational Layer (claude -p via Max plan) — handles message intake + clarification
    Execution Layer (Claude Code Agent Teams) — spawns Marc as Team Leader with teammates

Usage:
    python3 scripts/telegram_bot.py

Commands:
    /approve [account] [slots]  — Approve posts (all, by account, or by slot)
    /publish [account]          — Publish approved posts
    /pipeline                   — Run today's daily content pipeline
    /task <description>         — Send a task to Marc
    /status                     — Pipeline status summary
    /details                    — All posts with status emojis
    /metrics [account]          — View metrics summary
    /metrics post_id key=value  — Input manual metrics
    /confirm                    — Confirm pending screenshot metrics
    /cancel                     — Cancel pending screenshot metrics
    /running                    — Check active tasks
    /pause                      — Pause pipeline
    /resume                     — Resume pipeline
    /help                       — List commands

    Or just send a free-form message — Marc will respond conversationally.

Start with: python3 scripts/telegram_bot.py
Stop with: Ctrl+C or kill the process
"""

import asyncio
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("telegram_bot")

CONFIG_PATH = "config/accounts.json"
DATA_DIR = "data"
PAUSE_FLAG = os.path.join(DATA_DIR, ".paused")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_config() -> tuple[str, str]:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return config["telegram"]["bot_token"], config["telegram"]["chat_id"]


BOT_TOKEN, AUTHORIZED_CHAT_ID = load_config()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def today_str() -> str:
    """Return today's date as YYYYMMDD in JST."""
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")


def today_iso() -> str:
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d")


def is_authorized(update: Update) -> bool:
    return str(update.effective_chat.id) == AUTHORIZED_CHAT_ID


def load_json(path: str) -> dict | None:
    try:
        with open(path) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_json(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_content_plan(account: str) -> tuple[dict | None, str]:
    date = today_str()
    path = os.path.join(DATA_DIR, f"content_plan_{date}_{account}.json")
    return load_json(path), path


def _generate_task_id() -> str:
    """Generate a unique task ID: YYYYMMDD_NNN."""
    from zoneinfo import ZoneInfo
    date_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
    tasks_dir = os.path.join(DATA_DIR, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)

    existing = [f for f in os.listdir(tasks_dir) if f.startswith(f"task_{date_str}_")]
    seq = 1
    for f in existing:
        try:
            n = int(f.replace(f"task_{date_str}_", "").replace(".json", "").replace(".md", ""))
            seq = max(seq, n + 1)
        except ValueError:
            pass
    return f"{date_str}_{seq:03d}"


# ---------------------------------------------------------------------------
# URL Detection & Fetching
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r'https?://[^\s<>\"]+')


def _extract_urls(text: str) -> list[str]:
    """Extract URLs from message text."""
    return _URL_PATTERN.findall(text)


def _fetch_url_content(url: str, max_chars: int = 5000) -> str | None:
    """Fetch URL content using fetch_url module. Returns text or None on failure."""
    try:
        from fetch_url import fetch_url
        return fetch_url(url, max_chars=max_chars)
    except Exception as e:
        logger.warning(f"Failed to fetch URL {url}: {e}")
        return None


def _enrich_message_with_urls(text: str) -> str:
    """If message contains URLs, fetch their content and append to the message."""
    urls = _extract_urls(text)
    if not urls:
        return text

    fetched_parts = []
    for url in urls[:3]:  # Limit to 3 URLs per message
        logger.info(f"Fetching URL: {url}")
        content = _fetch_url_content(url)
        if content:
            fetched_parts.append(f"--- Content from {url} ---\n{content}\n--- End of content ---")
        else:
            fetched_parts.append(f"--- Could not fetch content from {url} ---")

    return text + "\n\n" + "\n\n".join(fetched_parts)


# ---------------------------------------------------------------------------
# Conversational Marc (claude -p, uses Max plan)
# ---------------------------------------------------------------------------

_marc_system_prompt: str = ""
_conversation_history: list[dict] = []  # [{"role": "user"|"assistant", "content": str}]


def _load_marc_system_prompt() -> str:
    path = os.path.join(PROJECT, "agents", "marc_conversation.md")
    with open(path) as f:
        return f.read()


def _reset_conversation():
    """Reset conversation history for a fresh session."""
    global _conversation_history
    _conversation_history = []


def _build_conversation_prompt(user_message: str) -> str:
    """Build a full prompt for claude -p including system prompt + history."""
    global _marc_system_prompt
    if not _marc_system_prompt:
        _marc_system_prompt = _load_marc_system_prompt()

    # Format conversation history
    history_lines = []
    for msg in _conversation_history:
        role = "Operator" if msg["role"] == "user" else "Marc"
        history_lines.append(f"{role}: {msg['content']}")

    history_text = "\n".join(history_lines) if history_lines else "(no prior messages)"

    return f"""{_marc_system_prompt}

## Conversation History
{history_text}

Operator: {user_message}

## Response Instructions
Respond to the operator's latest message as Marc. Be concise.

If you decide to start executing a task, include a JSON block at the END of your response
on its own line, formatted exactly like this (no markdown fences):

START_TASK:{{"task_description": "what to do", "task_type": "research|pipeline|publishing|report|custom", "agents_needed": ["scout", "strategist"], "notes": "any context"}}

If you're just chatting (no task to execute), respond normally without any START_TASK line.
Today's date: {today_iso()}"""


async def chat_with_marc(user_message: str) -> tuple[str, dict | None]:
    """Send message to conversational Marc via claude -p.

    Returns (response_text, tool_call_or_none).
    """
    global _conversation_history

    # Keep history manageable (last 20 messages)
    if len(_conversation_history) > 20:
        _conversation_history = _conversation_history[-20:]

    prompt = _build_conversation_prompt(user_message)

    # Add to history before calling (so next call sees it)
    _conversation_history.append({"role": "user", "content": user_message})

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        proc = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True, text=True, timeout=120, cwd=PROJECT, env=env,
            ),
        )
    except subprocess.TimeoutExpired:
        _conversation_history.append({"role": "assistant", "content": "(timed out)"})
        return "Sorry, I took too long to respond. Try again.", None

    if proc.returncode != 0:
        logger.error(f"claude -p failed: {proc.stderr[:300]}")
        _conversation_history.append({"role": "assistant", "content": "(error)"})
        return f"Marc encountered an error. stderr: {proc.stderr[:200]}", None

    output = proc.stdout.strip()

    # Parse for START_TASK marker
    tool_call = None
    response_text = output

    if "START_TASK:" in output:
        lines = output.split("\n")
        text_lines = []
        for line in lines:
            if line.strip().startswith("START_TASK:"):
                json_str = line.strip()[len("START_TASK:"):]
                try:
                    task_json = json.loads(json_str)
                    tool_call = {
                        "task_description": task_json["task_description"],
                        "task_type": task_json["task_type"],
                        "agents_needed": task_json.get("agents_needed", []),
                        "notes": task_json.get("notes", ""),
                    }
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse START_TASK JSON: {e}")
                    text_lines.append(line)
            else:
                text_lines.append(line)
        response_text = "\n".join(text_lines).strip()

    _conversation_history.append({"role": "assistant", "content": response_text})

    return response_text, tool_call


# ---------------------------------------------------------------------------
# Execution Layer (Claude Code Agent Teams)
# ---------------------------------------------------------------------------

_active_tasks: dict[str, subprocess.Popen] = {}
_active_tasks_lock = threading.Lock()


async def _execute_task(update: Update, task_id: str, tool_call: dict):
    """Spawn Marc as Agent Teams leader for execution."""
    task_desc = tool_call["task_description"]
    task_type = tool_call["task_type"]
    agents = tool_call.get("agents_needed", [])
    notes = tool_call.get("notes", "")

    # Write task file (audit trail)
    task_data = {
        "task_id": task_id,
        "description": task_desc,
        "task_type": task_type,
        "agents_planned": agents,
        "notes": notes,
        "created_at": datetime.now().astimezone().isoformat(),
        "status": "running",
    }
    tasks_dir = os.path.join(DATA_DIR, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    task_path = os.path.join(tasks_dir, f"task_{task_id}.json")
    save_json(task_path, task_data)

    # Determine which playbook to reference
    playbook_ref = {
        "pipeline": "Read agents/marc_pipeline.md for the Pipeline Playbook.",
        "publishing": "Read agents/marc_publishing.md for the Publishing Playbook.",
    }.get(task_type, "")

    prompt = f"""You are Marc, the COO and Team Leader.
Read agents/marc.md for your full instructions.
{playbook_ref}

IMPORTANT: You are running in non-interactive mode. Execute ALL scripts directly using your bash tool — do not ask the user to run commands or paste output. The operator is NOT watching this session. You must run everything yourself and deliver results via Telegram.

Task from the operator (confirmed via Telegram conversation):
{task_desc}

Additional context from conversation: {notes}
Agents the operator discussed using: {', '.join(agents)}

Today's date: {today_iso()}
Task ID: {task_id}

Execute this task:
1. Spawn the necessary teammates using the Agent tool
2. Coordinate their work via the shared task list
3. Review quality and iterate if needed
4. Report results to the operator via: python3 scripts/telegram_send.py "message"
5. For file deliverables: python3 scripts/telegram_send.py --document path/to/file "caption"
6. If any part cannot be done, report the limitation via Telegram
7. When finished, clean up the team."""

    env = os.environ.copy()
    env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
    env.pop("CLAUDECODE", None)

    proc = subprocess.Popen(
        ["claude", "-p", prompt, "--dangerously-skip-permissions"],
        env=env, cwd=PROJECT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    with _active_tasks_lock:
        _active_tasks[task_id] = proc

    logger.info(f"Task {task_id} started (PID: {proc.pid})")
    await update.message.reply_text(f"Task {task_id} started. I'll report results via Telegram when ready.")

    # Monitor process in background thread
    def _monitor():
        proc.wait()
        with _active_tasks_lock:
            _active_tasks.pop(task_id, None)

        # Update task file
        try:
            task_data_updated = load_json(task_path) or task_data
            task_data_updated["status"] = "completed" if proc.returncode == 0 else "failed"
            task_data_updated["completed_at"] = datetime.now().astimezone().isoformat()
            task_data_updated["exit_code"] = proc.returncode
            save_json(task_path, task_data_updated)
        except Exception as e:
            logger.error(f"Failed to update task file: {e}")

        logger.info(f"Task {task_id} finished (exit code: {proc.returncode})")

    thread = threading.Thread(target=_monitor, daemon=True)
    thread.start()


# ---------------------------------------------------------------------------
# Command Handlers
# ---------------------------------------------------------------------------


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    args = context.args or []

    if len(args) == 0:
        accounts = ["EN", "JP"]
        slots = None
    elif len(args) == 1:
        accounts = [args[0].upper()]
        slots = None
    else:
        accounts = [args[0].upper()]
        try:
            slots = [int(s.strip()) for s in args[1].split(",")]
        except ValueError:
            await update.message.reply_text("Invalid slot numbers. Use: /approve EN 1,3,5")
            return

    results = []
    for account in accounts:
        plan, path = load_content_plan(account)
        if plan is None:
            results.append(f"{account}: No content plan found for today")
            continue

        count = 0
        for post in plan.get("posts", []):
            if post.get("status") != "draft":
                continue
            if slots is not None and post.get("slot") not in slots:
                continue
            post["status"] = "approved"
            count += 1

        save_json(path, plan)
        results.append(f"{account}: {count} post(s) approved")

    await update.message.reply_text("\n".join(results))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    date = today_str()
    state = load_json(os.path.join(DATA_DIR, f"pipeline_state_{date}.json"))

    if state is None:
        await update.message.reply_text(f"No pipeline state found for {today_iso()}")
        return

    status = state.get("status", "unknown")
    emoji = {"running": "\u23f3", "completed": "\u2705", "failed": "\u274c"}.get(status, "\u2753")
    tasks_done = sum(1 for t in state.get("tasks", []) if t.get("status") == "completed")
    tasks_total = len(state.get("tasks", []))
    errors = len(state.get("errors", []))
    warnings = len(state.get("warnings", []))
    duration = state.get("duration_seconds")
    dur_str = f" ({duration}s)" if duration else ""

    paused = os.path.exists(PAUSE_FLAG)
    pause_str = " [PAUSED]" if paused else ""

    msg = (
        f"{emoji} Pipeline {today_iso()}{pause_str}\n"
        f"Status: {status}{dur_str}\n"
        f"Tasks: {tasks_done}/{tasks_total} completed\n"
        f"Errors: {errors} | Warnings: {warnings}"
    )
    await update.message.reply_text(msg)


async def cmd_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    lines = [f"Content Plan \u2014 {today_iso()}\n"]
    for account in ["EN", "JP"]:
        plan, _ = load_content_plan(account)
        if plan is None:
            lines.append(f"\n{account}: No plan found")
            continue

        lines.append(f"\n{account}:")
        for post in plan.get("posts", []):
            status = post.get("status", "unknown")
            emoji = {"draft": "\u270f\ufe0f", "approved": "\u2705", "posted": "\U0001f4e4", "failed": "\u274c"}.get(status, "\u2753")
            text = post.get("text", "")[:60]
            slot = post.get("slot", "?")
            cat = post.get("category", "?")
            time = post.get("scheduled_time", "?")
            lines.append(f"  {emoji} Slot {slot} [{cat}] {time}\n     {text}...")

    await update.message.reply_text("\n".join(lines))


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PAUSE_FLAG, "w") as f:
        f.write(datetime.utcnow().isoformat())
    await update.message.reply_text("Pipeline PAUSED. Use /resume to continue.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    if os.path.exists(PAUSE_FLAG):
        os.remove(PAUSE_FLAG)
        await update.message.reply_text("Pipeline RESUMED.")
    else:
        await update.message.reply_text("Pipeline is not paused.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    msg = (
        "Available commands:\n"
        "/approve \u2014 Approve all posts\n"
        "/approve EN \u2014 Approve all EN posts\n"
        "/approve EN 1,3 \u2014 Approve specific EN slots\n"
        "/publish \u2014 Publish approved posts (both accounts)\n"
        "/publish EN \u2014 Publish approved EN posts only\n"
        "/pipeline \u2014 Run today's daily content pipeline\n"
        "/task <desc> \u2014 Send a task to Marc\n"
        "/status \u2014 Pipeline status summary\n"
        "/details \u2014 All posts with statuses\n"
        "/metrics \u2014 View metrics summary\n"
        "/metrics EN \u2014 View EN metrics\n"
        "/metrics post_id key=value \u2014 Input manual metrics\n"
        "Send photo \u2014 Parse metrics from screenshot\n"
        "/confirm \u2014 Save parsed screenshot metrics\n"
        "/cancel \u2014 Discard parsed screenshot metrics\n"
        "/running \u2014 Check active tasks\n"
        "/pause \u2014 Pause pipeline\n"
        "/resume \u2014 Resume pipeline\n"
        "/help \u2014 This message\n"
        "\nOr just send a message \u2014 Marc will respond conversationally."
    )
    await update.message.reply_text(msg)


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route /publish through conversational Marc → execution."""
    if not is_authorized(update):
        return

    args = context.args or []
    account_str = args[0].upper() if args else "both EN and JP"

    response_text, tool_call = await chat_with_marc(
        f"[PUBLISH] Publish approved posts for {account_str} account(s). "
        f"Today's date: {today_iso()}."
    )

    if response_text:
        await update.message.reply_text(response_text)

    if tool_call:
        task_id = _generate_task_id()
        await _execute_task(update, task_id, tool_call)


async def cmd_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run today's daily content pipeline via conversational Marc → execution."""
    if not is_authorized(update):
        return

    response_text, tool_call = await chat_with_marc(
        f"[PIPELINE] Run today's daily content pipeline. Today's date: {today_iso()}."
    )

    if response_text:
        await update.message.reply_text(response_text)

    if tool_call:
        task_id = _generate_task_id()
        await _execute_task(update, task_id, tool_call)


async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a task to Marc via conversational layer."""
    if not is_authorized(update):
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: /task <description>\n"
            "Example: /task Analyze top 5 competitors and recommend content strategy"
        )
        return

    description = " ".join(args)

    response_text, tool_call = await chat_with_marc(
        f"[TASK REQUEST] {description}"
    )

    if response_text:
        await update.message.reply_text(response_text)

    if tool_call:
        task_id = _generate_task_id()
        await _execute_task(update, task_id, tool_call)


async def cmd_running(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show currently running tasks."""
    if not is_authorized(update):
        return

    with _active_tasks_lock:
        if not _active_tasks:
            await update.message.reply_text("No active tasks.")
            return

        lines = ["Active tasks:"]
        for task_id, proc in _active_tasks.items():
            status = "running" if proc.poll() is None else f"exited ({proc.returncode})"
            lines.append(f"  {task_id}: PID {proc.pid} \u2014 {status}")

    await update.message.reply_text("\n".join(lines))


async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View metrics or input manual metrics."""
    if not is_authorized(update):
        return

    args = context.args or []

    if len(args) == 0:
        await _show_metrics_summary(update)
        return

    if len(args) == 1 and args[0].upper() in ("EN", "JP"):
        await _show_metrics_summary(update, account=args[0].upper())
        return

    # Input mode: post_id key=value pairs
    post_id = args[0]
    metrics = {}
    for arg in args[1:]:
        if "=" not in arg:
            await update.message.reply_text(f"Invalid format: '{arg}'. Use key=value (e.g., impressions=5000)")
            return
        key, val = arg.split("=", 1)
        try:
            metrics[key.strip()] = int(val.strip())
        except ValueError:
            await update.message.reply_text(f"Invalid value for {key}: '{val}'. Must be a number.")
            return

    if not metrics:
        await update.message.reply_text("No metrics provided. Use: /metrics post_id impressions=5000")
        return

    try:
        import db_manager
        db_manager.init()

        account = post_id.split("_")[0] if "_" in post_id else "EN"
        measured_at = datetime.now().astimezone().isoformat()

        db_manager.insert_post_metrics(
            post_id=post_id,
            tweet_id=metrics.get("tweet_id", "manual"),
            account=account,
            measured_at=measured_at,
            hours_after_post=metrics.get("hours_after_post", 0),
            likes=metrics.get("likes"),
            retweets=metrics.get("retweets"),
            replies=metrics.get("replies"),
            quotes=metrics.get("quotes"),
            bookmarks=metrics.get("bookmarks"),
            impressions=metrics.get("impressions"),
            engagement_rate=None,
            source="manual_telegram",
        )

        parts = [f"{k}={v}" for k, v in metrics.items()]
        await update.message.reply_text(f"Saved metrics for {post_id}:\n" + "\n".join(parts))

    except Exception as e:
        await update.message.reply_text(f"Error saving metrics: {e}")


async def _show_metrics_summary(update: Update, account: str | None = None) -> None:
    """Query db_manager and show formatted metrics summary."""
    try:
        import db_manager
        db_manager.init()

        date = today_iso()
        accounts = [account] if account else ["EN", "JP"]
        lines = [f"Metrics Summary \u2014 {date}\n"]

        for acct in accounts:
            summary = db_manager.get_daily_summary(acct, date)
            am = summary.get("account_metrics")
            posts = summary.get("post_metrics", [])
            totals = summary.get("totals", {})

            lines.append(f"\n{acct}:")

            if am:
                change = am.get("followers_change")
                change_str = f" ({change:+d})" if change is not None else ""
                lines.append(f"  Followers: {am.get('followers', '?')}{change_str}")
            else:
                lines.append("  No account data yet")

            if posts:
                lines.append(f"  Posts measured: {len(posts)}")
                lines.append(f"  Total: {totals.get('likes', 0)} likes, "
                             f"{totals.get('retweets', 0)} RTs, "
                             f"{totals.get('replies', 0)} replies")
            else:
                lines.append("  No post metrics yet")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        await update.message.reply_text(f"Error loading metrics: {e}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle screenshot photo — parse metrics via claude -p with image."""
    if not is_authorized(update):
        return

    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        os.makedirs(os.path.join(PROJECT, "data", "temp"), exist_ok=True)
        temp_path = os.path.join(PROJECT, "data", "temp", f"screenshot_{today_str()}.jpg")
        await file.download_to_drive(temp_path)

        await update.message.reply_text("Analyzing screenshot...")

        prompt = (
            "This is a screenshot of X (Twitter) Analytics or post metrics. "
            "Extract the following metrics as JSON: "
            '{"post_id": "if visible", "impressions": number, "likes": number, '
            '"retweets": number, "replies": number, "quotes": number, "bookmarks": number}. '
            "Return ONLY valid JSON, no commentary. If a metric is not visible, omit it."
        )

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        proc = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                ["claude", "-p", prompt, "-a", temp_path],
                capture_output=True, text=True, timeout=120, cwd=PROJECT, env=env,
            ),
        )

        if proc.returncode != 0:
            await update.message.reply_text(f"Error analyzing screenshot: {proc.stderr[:200]}")
            return

        text = proc.stdout.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        parsed = json.loads(text)

        context.user_data["pending_screenshot_metrics"] = parsed
        context.user_data["pending_screenshot_path"] = temp_path

        display_lines = ["Parsed metrics from screenshot:"]
        for k, v in parsed.items():
            if v is not None:
                display_lines.append(f"  {k}: {v}")
        display_lines.append("\nUse /confirm to save or /cancel to discard.")

        await update.message.reply_text("\n".join(display_lines))

    except json.JSONDecodeError:
        await update.message.reply_text(
            "Could not parse metrics from screenshot. Please try a clearer image or use /metrics command."
        )
    except Exception as e:
        logger.error(f"Screenshot processing error: {e}")
        await update.message.reply_text(f"Error processing screenshot: {e}")


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirm and save pending screenshot metrics to SQLite."""
    if not is_authorized(update):
        return

    pending = context.user_data.get("pending_screenshot_metrics")
    if not pending:
        await update.message.reply_text("No pending metrics to confirm. Send a screenshot first.")
        return

    try:
        import db_manager
        db_manager.init()

        post_id = pending.get("post_id", "screenshot_" + today_str())
        account = post_id.split("_")[0] if "_" in post_id else "EN"
        measured_at = datetime.now().astimezone().isoformat()

        db_manager.insert_post_metrics(
            post_id=post_id,
            tweet_id="screenshot",
            account=account,
            measured_at=measured_at,
            hours_after_post=0,
            likes=pending.get("likes"),
            retweets=pending.get("retweets"),
            replies=pending.get("replies"),
            quotes=pending.get("quotes"),
            bookmarks=pending.get("bookmarks"),
            impressions=pending.get("impressions"),
            engagement_rate=None,
            source="manual_screenshot",
        )

        del context.user_data["pending_screenshot_metrics"]
        context.user_data.pop("pending_screenshot_path", None)

        await update.message.reply_text(f"Saved screenshot metrics for {post_id}")

    except Exception as e:
        await update.message.reply_text(f"Error saving metrics: {e}")


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel pending screenshot metrics."""
    if not is_authorized(update):
        return

    if "pending_screenshot_metrics" in context.user_data:
        del context.user_data["pending_screenshot_metrics"]
        context.user_data.pop("pending_screenshot_path", None)
        await update.message.reply_text("Pending screenshot metrics discarded.")
    else:
        await update.message.reply_text("Nothing to cancel.")


# ---------------------------------------------------------------------------
# Default message handler (conversational Marc)
# ---------------------------------------------------------------------------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form text messages — route to conversational Marc."""
    if not is_authorized(update):
        return

    text = update.message.text
    if not text:
        return

    try:
        # Fetch content from any URLs in the message
        enriched_text = await asyncio.get_event_loop().run_in_executor(
            None, _enrich_message_with_urls, text
        )
        response_text, tool_call = await chat_with_marc(enriched_text)

        if response_text:
            # Telegram has a 4096 char limit per message
            for i in range(0, len(response_text), 4000):
                await update.message.reply_text(response_text[i:i + 4000])

        if tool_call:
            task_id = _generate_task_id()
            await _execute_task(update, task_id, tool_call)

    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await update.message.reply_text(f"Error processing message: {e}")


async def cmd_stub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    cmd = update.message.text.split()[0] if update.message.text else "command"
    await update.message.reply_text(f"{cmd} is coming in a future phase.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print(f"Starting Telegram bot with Conversational Marc (chat_id: {AUTHORIZED_CHAT_ID})...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers (registered before the default text handler)
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CommandHandler("pipeline", cmd_pipeline))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("details", cmd_details))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.add_handler(CommandHandler("confirm", cmd_confirm))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("running", cmd_running))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Stub handlers for future phases
    for cmd in ["edit", "competitors"]:
        app.add_handler(CommandHandler(cmd, cmd_stub))

    # Default text handler LAST — catches all free-form messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    def shutdown(signum, frame):
        print("\nShutting down bot...")
        # Terminate any active tasks
        with _active_tasks_lock:
            for task_id, proc in _active_tasks.items():
                if proc.poll() is None:
                    logger.info(f"Terminating task {task_id} (PID: {proc.pid})")
                    proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Bot is running. Press Ctrl+C to stop.")
    print("Marc is listening for messages and commands.")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
