"""Schedule per-slot cron entries for approved posts.

Called by telegram_bot.py after /approve, or manually:
    python3 scripts/schedule_slots.py --account EN [--date YYYYMMDD]

Creates date-specific cron entries that fire once at each slot's scheduled_time,
executing: publisher.py post --account {account} --slot {slot}

All existing X-AGENTS-PUBLISH-SLOT entries are removed first (clean slate).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

from zoneinfo import ZoneInfo

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
CRON_TAG = "# X-AGENTS-PUBLISH-SLOT"

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


def get_current_crontab() -> str:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout


def set_crontab(content: str) -> None:
    proc = subprocess.run(["crontab", "-"], input=content, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"ERROR: Failed to set crontab: {proc.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def remove_slot_entries(crontab: str) -> str:
    """Remove all lines containing the CRON_TAG."""
    lines = crontab.splitlines()
    filtered = [line for line in lines if CRON_TAG not in line]
    return "\n".join(filtered) + "\n" if filtered else ""


def main():
    parser = argparse.ArgumentParser(description="Schedule per-slot cron entries for approved posts")
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

    # Collect approved posts with future scheduled times
    scheduled = []
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
            skipped.append((slot, time_str, "time already passed"))
            continue
        scheduled.append((slot, utc_dt, time_str))

    # Build cron entries
    cron_lines = []
    for slot, utc_dt, orig_time in scheduled:
        line = (
            f"{utc_dt.minute} {utc_dt.hour} {utc_dt.day} {utc_dt.month} * "
            f"cd {PROJECT_DIR} && python3 scripts/publisher.py post --account {account} --slot {slot} "
            f">> logs/cron_publish_{date_str}.log 2>&1 {CRON_TAG}"
        )
        cron_lines.append(line)

    # Update crontab: remove old slot entries, add new ones
    current = get_current_crontab()
    cleaned = remove_slot_entries(current)
    if cron_lines:
        new_crontab = cleaned.rstrip("\n") + "\n" + "\n".join(cron_lines) + "\n"
    else:
        new_crontab = cleaned
    set_crontab(new_crontab)

    # Print summary for Telegram
    lines = []
    if scheduled:
        lines.append(f"Scheduled {len(scheduled)} slot(s) for {account}:")
        for slot, utc_dt, orig_time in sorted(scheduled):
            jst_dt = utc_dt.astimezone(JST)
            lines.append(f"  Slot {slot}: {orig_time} ({jst_dt.strftime('%H:%M JST')})")
    else:
        lines.append(f"No slots to schedule for {account}")

    if skipped:
        for slot, time_str, reason in skipped:
            lines.append(f"  Skipped slot {slot} ({time_str}): {reason}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
