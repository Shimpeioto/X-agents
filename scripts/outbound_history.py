#!/usr/bin/env python3
"""Outbound history query tool for the Outbound agent.

Queries SQLite outbound_log and JSON fallback files to provide
engagement history, cooldown status, and budget usage.

Usage:
    python3 scripts/outbound_history.py --account EN --days 7
    python3 scripts/outbound_history.py --account EN --target @sessypuuh
    python3 scripts/outbound_history.py --account EN --check-tweets "id1,id2,id3"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

JST = ZoneInfo("Asia/Tokyo")


def load_outbound_rules():
    """Load safety margins from config/outbound_rules.json."""
    path = os.path.join(PROJECT, "config", "outbound_rules.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def query_db(account, start_date, end_date):
    """Query outbound_log from SQLite. Returns list of dicts."""
    try:
        import db_manager
        db_manager.init()
    except Exception:
        return []

    rows = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        try:
            day_rows = db_manager.get_outbound_log(account, date_str)
            rows.extend(day_rows)
        except Exception:
            pass
        current += timedelta(days=1)
    return rows


def load_json_logs(account, start_date, end_date):
    """Load outbound logs from JSON files as fallback."""
    rows = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        path = os.path.join(PROJECT, "data", f"outbound_log_{date_str}.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                # Handle both array format and object-with-actions format
                actions = data if isinstance(data, list) else data.get("actions", [])
                for action in actions:
                    # Normalize to common format
                    row = {
                        "date": current.strftime("%Y-%m-%d"),
                        "account": action.get("account", account),
                        "action_type": action.get("action_type", action.get("type", "")),
                        "target_handle": action.get("target_handle", action.get("target", "")),
                        "target_tweet_id": action.get("target_tweet_id", action.get("tweet_id", "")),
                        "success": action.get("success", True),
                        "timestamp": action.get("timestamp", ""),
                    }
                    if row["account"] == account:
                        rows.append(row)
            except (json.JSONDecodeError, KeyError):
                pass
        current += timedelta(days=1)
    return rows


def merge_rows(db_rows, json_rows):
    """Merge DB and JSON rows, deduplicating by (date, action_type, target_handle, target_tweet_id)."""
    seen = set()
    merged = []
    for row in db_rows:
        key = (row.get("date"), row.get("action_type"), row.get("target_handle"), row.get("target_tweet_id"))
        if key not in seen:
            seen.add(key)
            merged.append(row)
    for row in json_rows:
        key = (row.get("date"), row.get("action_type"), row.get("target_handle"), row.get("target_tweet_id"))
        if key not in seen:
            seen.add(key)
            merged.append(row)
    return merged


def build_summary(rows, account, days, rules):
    """Build human-readable summary from merged rows."""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")

    # Per-target aggregation
    targets = defaultdict(lambda: {
        "likes": 0, "replies": 0, "follows": 0,
        "liked_tweet_ids": [], "last_engaged": None,
        "followed": False, "last_follow_date": None,
        "last_reply_date": None, "last_like_date": None,
    })

    total_likes = 0
    total_replies = 0
    total_follows = 0
    today_likes = 0
    today_replies = 0
    today_follows = 0

    for row in rows:
        handle = row.get("target_handle", "unknown")
        action = row.get("action_type", "")
        date = row.get("date", "")
        tweet_id = row.get("target_tweet_id", "")

        t = targets[handle]

        # Track last engagement date
        if t["last_engaged"] is None or date > t["last_engaged"]:
            t["last_engaged"] = date

        if action == "like":
            t["likes"] += 1
            total_likes += 1
            if tweet_id:
                t["liked_tweet_ids"].append(tweet_id)
            if t["last_like_date"] is None or date > t["last_like_date"]:
                t["last_like_date"] = date
            if date == today_str:
                today_likes += 1
        elif action == "reply":
            t["replies"] += 1
            total_replies += 1
            if t["last_reply_date"] is None or date > t["last_reply_date"]:
                t["last_reply_date"] = date
            if date == today_str:
                today_replies += 1
        elif action == "follow":
            t["follows"] += 1
            t["followed"] = True
            t["last_follow_date"] = date
            total_follows += 1
            if date == today_str:
                today_follows += 1

    # Get safety margins
    margins = {}
    if rules:
        margins = rules.get("safety_margins", {}).get(account, {})

    max_likes = margins.get("max_likes_per_day", 20)
    max_replies = margins.get("max_replies_per_day", 5)
    max_follows = margins.get("max_follows_per_day", 3)

    # Build output
    lines = []
    lines.append(f"=== Outbound History: {account} (last {days} days) ===")
    lines.append(f"Total actions: {total_likes + total_replies + total_follows} "
                 f"(likes: {total_likes}, replies: {total_replies}, follows: {total_follows})")
    lines.append("")

    if targets:
        lines.append("Per-target summary:")
        for handle in sorted(targets.keys()):
            t = targets[handle]
            last = t["last_engaged"] or "never"
            if t["last_engaged"]:
                try:
                    last_date = datetime.strptime(t["last_engaged"], "%Y-%m-%d").replace(tzinfo=JST)
                    days_ago = (now - last_date).days
                    last = f"{t['last_engaged']} ({days_ago} days ago)"
                except ValueError:
                    pass

            follow_status = " (FOLLOWED)" if t["followed"] else ""
            lines.append(f"  {handle} — last engaged: {last}")
            lines.append(f"    likes: {t['likes']}, replies: {t['replies']}, follows: {t['follows']}{follow_status}")
            if t["liked_tweet_ids"]:
                ids_str = ", ".join(t["liked_tweet_ids"][:5])
                if len(t["liked_tweet_ids"]) > 5:
                    ids_str += f", ... (+{len(t['liked_tweet_ids']) - 5} more)"
                lines.append(f"    liked tweet IDs: {ids_str}")
        lines.append("")

    # Already followed
    followed_handles = [h for h, t in targets.items() if t["followed"]]
    if followed_handles:
        lines.append("Accounts already followed (do NOT re-follow):")
        lines.append(f"  {', '.join(sorted(followed_handles))}")
        lines.append("")

    # Today's usage
    lines.append("Today's usage so far:")
    lines.append(f"  likes: {today_likes}/{max_likes}, "
                 f"replies: {today_replies}/{max_replies}, "
                 f"follows: {today_follows}/{max_follows}")

    return "\n".join(lines)


def check_tweets(rows, tweet_ids):
    """Check which tweet IDs have already been liked."""
    liked = set()
    for row in rows:
        if row.get("action_type") == "like" and row.get("target_tweet_id"):
            liked.add(row["target_tweet_id"])

    lines = ["=== Tweet Deduplication Check ==="]
    for tid in tweet_ids:
        status = "ALREADY LIKED" if tid in liked else "not liked"
        lines.append(f"  {tid}: {status}")
    return "\n".join(lines)


def filter_target(rows, target_handle):
    """Filter rows for a specific target handle."""
    # Normalize handle (add @ if missing)
    if not target_handle.startswith("@"):
        target_handle = "@" + target_handle
    return [r for r in rows if r.get("target_handle") == target_handle]


def main():
    parser = argparse.ArgumentParser(description="Query outbound engagement history")
    parser.add_argument("--account", required=True, choices=["EN", "JP"],
                        help="Account to query (EN or JP)")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of days to look back (default: 7)")
    parser.add_argument("--target", type=str, default=None,
                        help="Filter to a specific target handle")
    parser.add_argument("--check-tweets", type=str, default=None,
                        help="Comma-separated tweet IDs to check for duplicates")

    args = parser.parse_args()

    now = datetime.now(JST)
    end_date = now
    start_date = now - timedelta(days=args.days)

    rules = load_outbound_rules()

    # Collect data from both sources
    db_rows = query_db(args.account, start_date, end_date)
    json_rows = load_json_logs(args.account, start_date, end_date)
    all_rows = merge_rows(db_rows, json_rows)

    if not all_rows:
        print(f"No outbound history found for {args.account} in the last {args.days} days.")
        print("First run — all targets are fresh.")
        print()
        margins = {}
        if rules:
            margins = rules.get("safety_margins", {}).get(args.account, {})
        max_likes = margins.get("max_likes_per_day", 20)
        max_replies = margins.get("max_replies_per_day", 5)
        max_follows = margins.get("max_follows_per_day", 3)
        print("Today's usage so far:")
        print(f"  likes: 0/{max_likes}, replies: 0/{max_replies}, follows: 0/{max_follows}")
        return

    # Filter by target if specified
    if args.target:
        all_rows = filter_target(all_rows, args.target)
        if not all_rows:
            print(f"No outbound history found for target {args.target}.")
            return

    # Check tweets mode
    if args.check_tweets:
        tweet_ids = [tid.strip() for tid in args.check_tweets.split(",")]
        print(check_tweets(all_rows, tweet_ids))
        return

    # Default: full summary
    print(build_summary(all_rows, args.account, args.days, rules))


if __name__ == "__main__":
    main()
