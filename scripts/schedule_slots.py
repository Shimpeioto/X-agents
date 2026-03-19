"""Schedule per-slot LaunchAgent entries for approved posts.

Called by telegram_bot.py after /approve, or manually:
    python3 scripts/schedule_slots.py --account EN [--date YYYYMMDD]

Creates date-specific LaunchAgent plists that fire once at each slot's scheduled_time,
executing: publisher.py post --account {account} --slot {slot}

For slots whose scheduled time has already passed, posts them immediately with
staggered delays (30min apart) to avoid ghost tweets on new accounts.

All existing X-AGENTS slot LaunchAgents are removed first (clean slate).
"""

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
LAUNCH_AGENTS_DIR = os.path.expanduser("~/Library/LaunchAgents")
SLOT_LABEL_PREFIX = "com.xagents.publish-slot"

JST = ZoneInfo("Asia/Tokyo")
UTC = ZoneInfo("UTC")


def load_content_plan(account: str, date_str: str) -> dict | None:
    path = os.path.join(DATA_DIR, "content", f"content_plan_{date_str}_{account}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def parse_scheduled_time(time_str: str, date_str: str) -> datetime | None:
    """Parse 'HH:MM UTC' or 'HH:MM JST' into a UTC datetime for the given date."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*(UTC|JST)", time_str.strip(), re.IGNORECASE)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    tz_label = m.group(3).upper()

    year = int(date_str[:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])

    tz = UTC if tz_label == "UTC" else JST
    local_dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    return local_dt.astimezone(UTC)


def remove_slot_agents() -> int:
    """Unload and remove all existing slot LaunchAgent plists. Returns count removed."""
    removed = 0
    for fname in os.listdir(LAUNCH_AGENTS_DIR):
        if fname.startswith(SLOT_LABEL_PREFIX) and fname.endswith(".plist"):
            path = os.path.join(LAUNCH_AGENTS_DIR, fname)
            label = fname.replace(".plist", "")
            subprocess.run(["launchctl", "unload", path], capture_output=True)
            os.remove(path)
            removed += 1
    return removed


def create_slot_agent(account: str, slot: int, utc_dt: datetime, date_str: str) -> str:
    """Create a LaunchAgent plist for a single slot. Returns the plist path."""
    # Use JST for the calendar interval (launchd uses local time)
    jst_dt = utc_dt.astimezone(JST)

    label = f"{SLOT_LABEL_PREFIX}.{date_str}-{account.lower()}-{slot:02d}"
    plist_path = os.path.join(LAUNCH_AGENTS_DIR, f"{label}.plist")

    plist_data = {
        "Label": label,
        "ProgramArguments": [
            "/bin/bash", "-c",
            f'source "$HOME/.zshrc" 2>/dev/null; cd {PROJECT_DIR} && python3 scripts/publisher.py --date {date_str} post --account {account} --slot {slot} >> logs/launchd_publish_{date_str}.log 2>&1'
        ],
        "StartCalendarInterval": {
            "Month": jst_dt.month,
            "Day": jst_dt.day,
            "Hour": jst_dt.hour,
            "Minute": jst_dt.minute,
        },
        "StandardOutPath": os.path.join(PROJECT_DIR, "logs", f"launchd_publish_{date_str}.log"),
        "StandardErrorPath": os.path.join(PROJECT_DIR, "logs", f"launchd_publish_{date_str}.log"),
        "EnvironmentVariables": {
            "HOME": os.path.expanduser("~"),
            "TZ": "Asia/Tokyo",
        },
    }

    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)

    # Load the agent
    subprocess.run(["launchctl", "load", plist_path], capture_output=True)
    return plist_path


def main():
    parser = argparse.ArgumentParser(description="Schedule per-slot LaunchAgent entries for approved posts")
    parser.add_argument("--account", required=True, help="Account: EN or JP")
    parser.add_argument("--date", default=None, help="Date YYYYMMDD (default: today JST)")
    args = parser.parse_args()

    account = args.account.upper()
    date_str = args.date or datetime.now(JST).strftime("%Y%m%d")

    plan = load_content_plan(account, date_str)
    if plan is None:
        print(f"No content plan found for {account} on {date_str}")
        sys.exit(1)

    now_utc = datetime.now(UTC)

    # Minimum gap between posts to avoid ghost tweets (X removes rapid posts from new accounts)
    MIN_GAP_MINUTES = 30

    # Categorize approved posts: future (schedule normally) vs past (post soon with stagger)
    future_slots = []
    past_slots = []
    skipped = []
    for post in plan.get("posts", []):
        if post.get("status") != "approved":
            continue
        slot = post.get("slot")
        time_str = post.get("scheduled_time", "")
        utc_dt = parse_scheduled_time(time_str, date_str)
        if utc_dt is None:
            skipped.append((slot, time_str, "could not parse time"))
            continue
        if utc_dt <= now_utc:
            past_slots.append((slot, utc_dt, time_str))
        else:
            future_slots.append((slot, utc_dt, time_str))

    # For past slots: reschedule with staggered times starting from now + 5 min
    # Each subsequent past slot gets an additional MIN_GAP_MINUTES gap
    rescheduled = []
    if past_slots:
        # Sort by original slot number to maintain order
        past_slots.sort(key=lambda x: x[0])
        next_time = now_utc + timedelta(minutes=5)

        # Check if any future slots exist — ensure past slots don't collide with them
        future_times = [utc_dt for _, utc_dt, _ in future_slots]

        for slot, orig_utc, orig_time in past_slots:
            # Ensure we don't schedule too close to a future slot
            for ft in future_times:
                if abs((next_time - ft).total_seconds()) < MIN_GAP_MINUTES * 60:
                    next_time = ft + timedelta(minutes=MIN_GAP_MINUTES)

            rescheduled.append((slot, next_time, orig_time))
            next_time = next_time + timedelta(minutes=MIN_GAP_MINUTES)

    # Clean slate: remove all existing slot agents
    removed = remove_slot_agents()

    # Create LaunchAgents for future slots (at original time)
    for slot, utc_dt, orig_time in future_slots:
        create_slot_agent(account, slot, utc_dt, date_str)

    # Create LaunchAgents for rescheduled past slots (at staggered times)
    for slot, utc_dt, orig_time in rescheduled:
        create_slot_agent(account, slot, utc_dt, date_str)

    # Print summary for Telegram
    lines = []
    if removed:
        lines.append(f"Cleared {removed} previous slot schedule(s)")

    if future_slots:
        lines.append(f"Scheduled {len(future_slots)} slot(s) at original times:")
        for slot, utc_dt, orig_time in sorted(future_slots):
            jst_dt = utc_dt.astimezone(JST)
            lines.append(f"  Slot {slot}: {orig_time} ({jst_dt.strftime('%H:%M JST')})")

    if rescheduled:
        lines.append(f"Rescheduled {len(rescheduled)} past slot(s) with 30min gaps:")
        for slot, utc_dt, orig_time in rescheduled:
            jst_dt = utc_dt.astimezone(JST)
            lines.append(f"  Slot {slot}: was {orig_time}, now {jst_dt.strftime('%H:%M JST')} (rescheduled)")

    if not future_slots and not rescheduled:
        lines.append(f"No slots to schedule for {account}")

    if skipped:
        for slot, time_str, reason in skipped:
            lines.append(f"  Skipped slot {slot} ({time_str}): {reason}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
