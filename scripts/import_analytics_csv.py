"""Import X Analytics CSV into daily_analytics table.

Usage:
    python3 scripts/import_analytics_csv.py <csv_path> --account EN
    python3 scripts/import_analytics_csv.py x/account_overview_analytics.csv --account EN --dry-run
"""

import argparse
import csv
import os
import sys
from datetime import datetime

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))
import db_manager


def parse_date(date_str: str) -> str:
    """Parse 'Tue, Mar 17, 2026' -> '2026-03-17'."""
    dt = datetime.strptime(date_str.strip(), "%a, %b %d, %Y")
    return dt.strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(description="Import X Analytics CSV into SQLite")
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument("--account", required=True, help="Account name (EN or JP)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without writing")
    args = parser.parse_args()

    csv_path = os.path.join(PROJECT, args.csv_path) if not os.path.isabs(args.csv_path) else args.csv_path
    if not os.path.exists(csv_path):
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    # Ensure table exists
    if not args.dry_run:
        db_manager.init()

    imported = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = parse_date(row["Date"])
            impressions = int(row.get("Impressions", 0))
            likes = int(row.get("Likes", 0))
            engagements = int(row.get("Engagements", 0))
            bookmarks = int(row.get("Bookmarks", 0))
            shares = int(row.get("Shares", 0))
            new_follows = int(row.get("New follows", 0))
            unfollows = int(row.get("Unfollows", 0))
            replies = int(row.get("Replies", 0))
            reposts = int(row.get("Reposts", 0))
            profile_visits = int(row.get("Profile visits", 0))
            posts_created = int(row.get("Create Post", 0))
            video_views = int(row.get("Video views", 0))
            media_views = int(row.get("Media views", 0))

            if args.dry_run:
                print(f"  [DRY-RUN] {args.account} {date}: {impressions:,} impressions, "
                      f"{likes} likes, {engagements} engagements, {profile_visits} profile visits, "
                      f"+{new_follows} follows, -{unfollows} unfollows")
            else:
                db_manager.insert_daily_analytics(
                    account=args.account, date=date,
                    impressions=impressions, likes=likes, engagements=engagements,
                    bookmarks=bookmarks, shares=shares, new_follows=new_follows,
                    unfollows=unfollows, replies=replies, reposts=reposts,
                    profile_visits=profile_visits, posts_created=posts_created,
                    video_views=video_views, media_views=media_views,
                    source="csv_import"
                )
                print(f"  [IMPORTED] {args.account} {date}: {impressions:,} impressions, "
                      f"{likes} likes, {engagements} engagements, +{new_follows} follows")
            imported += 1

    action = "Would import" if args.dry_run else "Imported"
    print(f"\n{action} {imported} rows for {args.account}. Skipped {skipped}.")


if __name__ == "__main__":
    main()
