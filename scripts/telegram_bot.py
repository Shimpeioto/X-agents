"""Telegram bot daemon for human-in-the-loop command processing.

Usage:
    python3 scripts/telegram_bot.py

Commands:
    /approve [account] [slots]  — Approve posts (all, by account, or by slot)
    /status                     — Pipeline status summary
    /details                    — All posts with status emojis
    /metrics [account]          — View metrics summary
    /metrics post_id key=value  — Input manual metrics
    /confirm                    — Confirm pending screenshot metrics
    /cancel                     — Cancel pending screenshot metrics
    /task <description>         — Queue a task for Marc
    /pause                      — Pause pipeline
    /resume                     — Resume pipeline
    /help                       — List commands

Start with: python3 scripts/telegram_bot.py
Stop with: Ctrl+C or kill the process
"""

import json
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

logger = logging.getLogger(__name__)

CONFIG_PATH = "config/accounts.json"
DATA_DIR = "data"
PAUSE_FLAG = os.path.join(DATA_DIR, ".paused")


def load_config() -> tuple[str, str]:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    return config["telegram"]["bot_token"], config["telegram"]["chat_id"]


BOT_TOKEN, AUTHORIZED_CHAT_ID = load_config()


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


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return

    args = context.args or []

    if len(args) == 0:
        # Approve all posts for both accounts
        accounts = ["EN", "JP"]
        slots = None
    elif len(args) == 1:
        # /approve EN or /approve JP
        accounts = [args[0].upper()]
        slots = None
    else:
        # /approve EN 1,3,5
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

    lines = [f"Content Plan — {today_iso()}\n"]
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
        "/approve — Approve all posts\n"
        "/approve EN — Approve all EN posts\n"
        "/approve EN 1,3 — Approve specific EN slots\n"
        "/publish — Publish approved posts (both accounts)\n"
        "/publish EN — Publish approved EN posts only\n"
        "/status — Pipeline status summary\n"
        "/details — All posts with statuses\n"
        "/metrics — View metrics summary\n"
        "/metrics EN — View EN metrics\n"
        "/metrics post_id key=value — Input manual metrics\n"
        "Send photo — Parse metrics from screenshot\n"
        "/confirm — Save parsed screenshot metrics\n"
        "/cancel — Discard parsed screenshot metrics\n"
        "/task <description> — Queue a task for Marc\n"
        "/pause — Pause pipeline\n"
        "/resume — Resume pipeline\n"
        "/help — This message\n"
        "\nFuture commands (not yet implemented):\n"
        "/edit, /competitors"
    )
    await update.message.reply_text(msg)


async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run publisher.py post for specified account(s)."""
    if not is_authorized(update):
        return

    args = context.args or []
    accounts = [args[0].upper()] if args else ["EN", "JP"]

    for account in accounts:
        if account not in ("EN", "JP"):
            await update.message.reply_text(f"Invalid account: {account}. Use EN or JP.")
            return

    results = []
    for account in accounts:
        # Check if there are approved posts first
        plan, _ = load_content_plan(account)
        if plan is None:
            results.append(f"{account}: No content plan found for today")
            continue
        approved = sum(1 for p in plan.get("posts", []) if p.get("status") == "approved")
        if approved == 0:
            results.append(f"{account}: No approved posts to publish")
            continue

        await update.message.reply_text(f"Publishing {approved} approved post(s) for {account}...")

        try:
            result = subprocess.run(
                ["python3", os.path.join(PROJECT, "scripts", "publisher.py"), "post", "--account", account],
                capture_output=True, text=True, timeout=120, cwd=PROJECT,
            )
            if result.returncode == 0:
                # Re-read plan to get results
                plan, _ = load_content_plan(account)
                posted = sum(1 for p in plan.get("posts", []) if p.get("status") == "posted") if plan else 0
                failed = sum(1 for p in plan.get("posts", []) if p.get("status") == "failed") if plan else 0
                results.append(f"{account}: {posted} posted, {failed} failed")
            else:
                results.append(f"{account}: Publisher error — {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            results.append(f"{account}: Publisher timed out (120s)")
        except Exception as e:
            results.append(f"{account}: Error — {str(e)[:200]}")

    await update.message.reply_text("\n".join(results))


async def cmd_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View metrics or input manual metrics.

    /metrics           — View summary for both accounts
    /metrics EN        — View summary for EN
    /metrics EN_20260304_01 impressions=5000 — Input manual metrics
    """
    if not is_authorized(update):
        return

    args = context.args or []

    if len(args) == 0:
        # View mode: show both accounts
        await _show_metrics_summary(update)
        return

    if len(args) == 1 and args[0].upper() in ("EN", "JP"):
        # View mode: specific account
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

        # Derive account from post_id
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
        lines = [f"Metrics Summary — {date}\n"]

        for acct in accounts:
            summary = db_manager.get_daily_summary(acct, date)
            am = summary.get("account_metrics")
            posts = summary.get("post_metrics", [])
            totals = summary.get("totals", {})

            flag = {"EN": "US", "JP": "JP"}.get(acct, "")
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
    """Handle screenshot photo — parse metrics via Claude Vision API."""
    if not is_authorized(update):
        return

    try:
        import anthropic

        photo = update.message.photo[-1]  # Highest resolution
        file = await photo.get_file()

        # Download to temp location
        os.makedirs(os.path.join(PROJECT, "data", "temp"), exist_ok=True)
        temp_path = os.path.join(PROJECT, "data", "temp", f"screenshot_{today_str()}.jpg")
        await file.download_to_drive(temp_path)

        await update.message.reply_text("Analyzing screenshot...")

        # Read image and send to Claude Vision
        import base64
        with open(temp_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a screenshot of X (Twitter) Analytics or post metrics. "
                            "Extract the following metrics as JSON: "
                            '{"post_id": "if visible", "impressions": number, "likes": number, '
                            '"retweets": number, "replies": number, "quotes": number, "bookmarks": number}. '
                            "Return ONLY valid JSON, no commentary. If a metric is not visible, omit it."
                        ),
                    },
                ],
            }],
        )

        # Parse Claude's response
        text = response.content[0].text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        parsed = json.loads(text)

        # Store in user_data for confirmation
        context.user_data["pending_screenshot_metrics"] = parsed
        context.user_data["pending_screenshot_path"] = temp_path

        # Format for display
        display_lines = ["Parsed metrics from screenshot:"]
        for k, v in parsed.items():
            if v is not None:
                display_lines.append(f"  {k}: {v}")
        display_lines.append("\nUse /confirm to save or /cancel to discard.")

        await update.message.reply_text("\n".join(display_lines))

    except ImportError:
        await update.message.reply_text(
            "anthropic package not installed. Install with: pip install anthropic"
        )
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

        # Clear pending
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


def _generate_task_id() -> str:
    """Generate a unique task ID: YYYYMMDD_NNN."""
    from zoneinfo import ZoneInfo
    date_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
    tasks_dir = os.path.join(DATA_DIR, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)

    # Find next sequence number for today
    existing = [f for f in os.listdir(tasks_dir) if f.startswith(f"task_{date_str}_")]
    seq = 1
    for f in existing:
        try:
            n = int(f.replace(f"task_{date_str}_", "").replace(".json", ""))
            seq = max(seq, n + 1)
        except ValueError:
            pass
    return f"{date_str}_{seq:03d}"


async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Queue a task for Marc to execute.

    /task <description> — Create a task for Marc to handle autonomously.
    """
    if not is_authorized(update):
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: /task <description>\n"
            "Example: /task Analyze top 5 competitors and recommend content strategy for next week"
        )
        return

    description = " ".join(args)
    task_id = _generate_task_id()

    task_data = {
        "task_id": task_id,
        "status": "pending",
        "description": description,
        "created_at": datetime.now().astimezone().isoformat(),
        "started_at": None,
        "completed_at": None,
        "result": None,
    }

    tasks_dir = os.path.join(DATA_DIR, "tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    task_path = os.path.join(tasks_dir, f"task_{task_id}.json")
    save_json(task_path, task_data)

    await update.message.reply_text(
        f"Task queued: {task_id}\n"
        f"Description: {description}\n"
        f"To execute: ./scripts/run_task.sh {task_id}"
    )


async def cmd_stub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update):
        return
    cmd = update.message.text.split()[0] if update.message.text else "command"
    await update.message.reply_text(f"{cmd} is coming in a future phase.")


def main():
    print(f"Starting Telegram bot (chat_id: {AUTHORIZED_CHAT_ID})...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("details", cmd_details))
    app.add_handler(CommandHandler("metrics", cmd_metrics))
    app.add_handler(CommandHandler("confirm", cmd_confirm))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Stub handlers for future phases
    for cmd in ["edit", "competitors"]:
        app.add_handler(CommandHandler(cmd, cmd_stub))

    def shutdown(signum, frame):
        print("\nShutting down bot...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
