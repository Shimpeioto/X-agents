"""Telegram bot daemon for human-in-the-loop command processing.

Usage:
    python3 scripts/telegram_bot.py

Commands:
    /approve [account] [slots]  — Approve posts (all, by account, or by slot)
    /status                     — Pipeline status summary
    /details                    — All posts with status emojis
    /pause                      — Pause pipeline
    /resume                     — Resume pipeline
    /help                       — List commands

Start with: python3 scripts/telegram_bot.py
Stop with: Ctrl+C or kill the process
"""

import json
import os
import signal
import subprocess
import sys
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
        "/pause — Pause pipeline\n"
        "/resume — Resume pipeline\n"
        "/help — This message\n"
        "\nFuture commands (not yet implemented):\n"
        "/edit, /strategy, /metrics, /competitors"
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
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("help", cmd_help))

    # Stub handlers for future phases
    for cmd in ["edit", "strategy", "metrics", "competitors"]:
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
