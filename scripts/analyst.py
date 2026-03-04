"""Analyst agent — Collects post metrics, account snapshots, and imports manual data.

Usage:
    python3 scripts/analyst.py collect [--account EN|JP]
    python3 scripts/analyst.py summary --account EN|JP
    python3 scripts/analyst.py import --file path.csv|json
    python3 scripts/analyst.py --dry-run collect

Exit codes: 0=success, 1=error, 2=usage error
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

import db_manager
from x_api import XApiClient, load_bearer_token

JST = ZoneInfo("Asia/Tokyo")
DATA_DIR = os.path.join(PROJECT, "data")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ANALYST] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def today_str() -> str:
    return datetime.now(JST).strftime("%Y%m%d")


def today_iso() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(JST).isoformat()


def load_json(path: str) -> dict | None:
    try:
        with open(path) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load {path}: {e}")
        return None


def save_json(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {path}")


class Analyst:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.date = today_str()
        self.date_iso = today_iso()

        if not dry_run:
            bearer = load_bearer_token()
            self.read_client = XApiClient(bearer)
        else:
            self.read_client = None

        db_manager.init()

    def collect_post_metrics(self, account: str) -> int:
        """Collect metrics for all posted tweets of an account. Returns count collected."""
        plan_path = os.path.join(DATA_DIR, f"content_plan_{self.date}_{account}.json")
        plan = load_json(plan_path)
        if plan is None:
            logger.error(f"No content plan found: {plan_path}")
            return -1

        # Filter to posted tweets with tweet_ids
        posted = [p for p in plan.get("posts", []) if p.get("status") == "posted" and p.get("tweet_id")]
        if not posted:
            logger.info(f"No posted tweets found for {account}")
            return 0

        tweet_ids = [p["tweet_id"] for p in posted]
        tweet_id_to_post = {p["tweet_id"]: p for p in posted}

        logger.info(f"Collecting metrics for {len(tweet_ids)} posted tweets ({account})")

        if self.dry_run:
            # Mock data
            for p in posted:
                logger.info(f"[DRY-RUN] Would collect metrics for {p['id']} (tweet {p['tweet_id']})")
            return len(posted)

        # Batch fetch tweet metrics
        tweets = self.read_client.get_tweets_batch(tweet_ids)
        tweet_data = {t["tweet_id"]: t for t in tweets}

        measured_at = now_iso()
        collected = 0

        for tweet_id, post in tweet_id_to_post.items():
            if tweet_id not in tweet_data:
                logger.warning(f"Tweet {tweet_id} ({post['id']}) not found — may be deleted")
                continue

            tweet = tweet_data[tweet_id]
            metrics = tweet.get("public_metrics", {})

            # Calculate hours_after_post
            posted_at_str = post.get("posted_at", "")
            hours_after = 0
            if posted_at_str:
                try:
                    posted_at = datetime.fromisoformat(posted_at_str)
                    now_jst = datetime.now(JST)
                    hours_after = round((now_jst - posted_at).total_seconds() / 3600)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse posted_at for {post['id']}: {posted_at_str}")

            likes = metrics.get("like_count", 0)
            retweets = metrics.get("retweet_count", 0)
            replies = metrics.get("reply_count", 0)
            quotes = metrics.get("quote_count", 0)
            bookmarks = metrics.get("bookmark_count", 0)

            db_manager.insert_post_metrics(
                post_id=post["id"],
                tweet_id=tweet_id,
                account=account,
                measured_at=measured_at,
                hours_after_post=hours_after,
                likes=likes,
                retweets=retweets,
                replies=replies,
                quotes=quotes,
                bookmarks=bookmarks,
                impressions=None,
                engagement_rate=None,
                source="api",
            )
            collected += 1
            logger.info(f"Collected {post['id']}: {likes} likes, {retweets} RTs, {replies} replies")

        return collected

    def collect_account_metrics(self, account: str) -> bool:
        """Collect account snapshot (followers, following, etc.). Returns True on success."""
        # Load account config for user_id
        config_path = os.path.join(PROJECT, "config/accounts.json")
        try:
            with open(config_path) as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load accounts config: {e}")
            return False

        acct_config = config.get("x_api", {}).get("accounts", {}).get(account, {})
        user_id = acct_config.get("user_id")
        handle = acct_config.get("handle", "").lstrip("@")

        if not user_id and not handle:
            logger.error(f"No user_id or handle configured for {account}")
            return False

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would collect account metrics for {account}")
            return True

        # Fetch user info
        if user_id:
            users = self.read_client.get_user_info_batch([user_id])
            user_info = users[0] if users else None
        else:
            user_info = self.read_client.resolve_user_id(handle)

        if not user_info:
            logger.error(f"Could not fetch user info for {account}")
            return False

        pm = user_info.get("public_metrics", {})
        followers = pm.get("followers_count", 0)
        following = pm.get("following_count", 0)
        total_posts = pm.get("tweet_count", 0)

        # Calculate followers_change
        yesterday = db_manager.get_yesterday_followers(account)
        followers_change = (followers - yesterday) if yesterday is not None else None

        db_manager.insert_account_metrics(
            account=account,
            date=self.date_iso,
            followers=followers,
            following=following,
            total_posts=total_posts,
            followers_change=followers_change,
        )

        change_str = f" ({followers_change:+d})" if followers_change is not None else " (first day)"
        logger.info(f"{account}: {followers} followers{change_str}, {following} following, {total_posts} posts")
        return True

    def generate_summary(self, account: str) -> bool:
        """Generate daily summary JSON for an account. Returns True on success."""
        summary = db_manager.get_daily_summary(account, self.date_iso)

        # Enrich with content plan metadata
        plan_path = os.path.join(DATA_DIR, f"content_plan_{self.date}_{account}.json")
        plan = load_json(plan_path)
        if plan:
            post_lookup = {p["id"]: p for p in plan.get("posts", [])}
            for pm in summary.get("post_metrics", []):
                post_info = post_lookup.get(pm.get("post_id"), {})
                pm["category"] = post_info.get("category")
                pm["scheduled_time"] = post_info.get("scheduled_time")
                pm["text_preview"] = (post_info.get("text", ""))[:80]

        # Add generation metadata
        summary["generated_at"] = now_iso()
        summary["post_count"] = len(summary.get("post_metrics", []))

        output_path = os.path.join(DATA_DIR, f"metrics_{self.date}_{account}.json")
        save_json(output_path, summary)
        logger.info(f"Summary generated: {output_path} ({summary['post_count']} posts)")
        return True

    def import_manual_metrics(self, file_path: str) -> int:
        """Import manual metrics from CSV or JSON file. Returns count imported."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return -1

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            return self._import_csv(file_path)
        elif ext == ".json":
            return self._import_json(file_path)
        else:
            logger.error(f"Unsupported file format: {ext}. Use .csv or .json")
            return -1

    def _import_csv(self, file_path: str) -> int:
        """Import metrics from CSV. Expected columns: post_id, impressions, [likes, retweets, ...]."""
        count = 0
        try:
            with open(file_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    post_id = row.get("post_id", "").strip()
                    if not post_id:
                        logger.warning(f"Skipping row with empty post_id")
                        continue

                    measured_at = row.get("measured_at", now_iso())
                    tweet_id = row.get("tweet_id", "manual")
                    account = row.get("account", post_id.split("_")[0] if "_" in post_id else "EN")

                    impressions = _safe_int(row.get("impressions"))
                    likes = _safe_int(row.get("likes"))
                    retweets = _safe_int(row.get("retweets"))
                    replies = _safe_int(row.get("replies"))
                    quotes = _safe_int(row.get("quotes"))
                    bookmarks = _safe_int(row.get("bookmarks"))

                    # Calculate engagement_rate if impressions available
                    engagement_rate = None
                    if impressions and impressions > 0:
                        total_eng = (likes or 0) + (retweets or 0) + (replies or 0) + (quotes or 0)
                        engagement_rate = total_eng / impressions

                    hours_after = _safe_int(row.get("hours_after_post")) or 0

                    db_manager.insert_post_metrics(
                        post_id=post_id, tweet_id=tweet_id, account=account,
                        measured_at=measured_at, hours_after_post=hours_after,
                        likes=likes, retweets=retweets, replies=replies,
                        quotes=quotes, bookmarks=bookmarks, impressions=impressions,
                        engagement_rate=engagement_rate, source="manual_csv",
                    )
                    count += 1
                    logger.info(f"Imported {post_id}: impressions={impressions}")
        except Exception as e:
            logger.error(f"CSV import error: {e}")
            return -1

        logger.info(f"CSV import complete: {count} rows imported from {file_path}")
        return count

    def _import_json(self, file_path: str) -> int:
        """Import metrics from JSON. Expects list of objects with post_id + metric fields."""
        data = load_json(file_path)
        if data is None:
            return -1

        # Accept both {"metrics": [...]} and bare [...]
        if isinstance(data, dict):
            entries = data.get("metrics", data.get("data", []))
        elif isinstance(data, list):
            entries = data
        else:
            logger.error("JSON must be an array or object with 'metrics' array")
            return -1

        count = 0
        for entry in entries:
            post_id = entry.get("post_id", "").strip()
            if not post_id:
                logger.warning("Skipping entry with empty post_id")
                continue

            measured_at = entry.get("measured_at", now_iso())
            tweet_id = entry.get("tweet_id", "manual")
            account = entry.get("account", post_id.split("_")[0] if "_" in post_id else "EN")

            impressions = entry.get("impressions")
            likes = entry.get("likes")
            retweets = entry.get("retweets")
            replies = entry.get("replies")
            quotes = entry.get("quotes")
            bookmarks = entry.get("bookmarks")

            engagement_rate = None
            if impressions and impressions > 0:
                total_eng = (likes or 0) + (retweets or 0) + (replies or 0) + (quotes or 0)
                engagement_rate = total_eng / impressions

            hours_after = entry.get("hours_after_post", 0)

            db_manager.insert_post_metrics(
                post_id=post_id, tweet_id=tweet_id, account=account,
                measured_at=measured_at, hours_after_post=hours_after,
                likes=likes, retweets=retweets, replies=replies,
                quotes=quotes, bookmarks=bookmarks, impressions=impressions,
                engagement_rate=engagement_rate, source="manual_json",
            )
            count += 1
            logger.info(f"Imported {post_id}: impressions={impressions}")

        logger.info(f"JSON import complete: {count} entries imported from {file_path}")
        return count


def _safe_int(val):
    """Convert to int, return None if empty or invalid."""
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Analyst agent — metrics collection and import")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without API calls or DB writes")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # collect subcommand
    collect_parser = subparsers.add_parser("collect", help="Collect post metrics and account snapshot")
    collect_parser.add_argument("--account", choices=["EN", "JP"], default=None,
                                help="Collect for specific account (default: both)")

    # summary subcommand
    summary_parser = subparsers.add_parser("summary", help="Generate daily summary JSON")
    summary_parser.add_argument("--account", required=True, choices=["EN", "JP"],
                                help="Account to generate summary for")

    # import subcommand
    import_parser = subparsers.add_parser("import", help="Import manual metrics from CSV/JSON")
    import_parser.add_argument("--file", required=True, help="Path to CSV or JSON file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(2)

    analyst = Analyst(dry_run=args.dry_run)

    if args.dry_run:
        logger.info("[DRY-RUN MODE] No API calls or DB writes")

    if args.command == "collect":
        accounts = [args.account] if args.account else ["EN", "JP"]
        errors = 0
        for account in accounts:
            logger.info(f"Collecting post metrics for {account}...")
            post_count = analyst.collect_post_metrics(account)
            if post_count < 0:
                errors += 1
            else:
                logger.info(f"Collected metrics for {post_count} posts ({account})")

            logger.info(f"Collecting account metrics for {account}...")
            if not analyst.collect_account_metrics(account):
                errors += 1

        sys.exit(1 if errors > 0 else 0)

    elif args.command == "summary":
        if analyst.generate_summary(args.account):
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.command == "import":
        count = analyst.import_manual_metrics(args.file)
        sys.exit(0 if count >= 0 else 1)

    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
