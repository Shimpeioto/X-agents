#!/usr/bin/env python3
"""Fetch all recent tweets from own account, identify untracked posts, and collect metrics.

Solves the blind spot where manual posts (reposts, quote tweets) are not tracked
by the pipeline. Cross-references timeline against all content plans to find
untracked tweets and optionally stores their metrics in SQLite.

Usage:
    python3 scripts/fetch_account_tweets.py --account EN
    python3 scripts/fetch_account_tweets.py --account EN --max-results 100
    python3 scripts/fetch_account_tweets.py --account EN --collect-metrics
"""

import argparse
import glob
import json
import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

from x_api import XApiClient, load_bearer_token
from data_paths import CONTENT_DIR, METRICS_DIR

JST = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [TRACKER] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


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


def get_known_tweet_ids(account: str) -> set[str]:
    """Scan all content plans for this account and collect known tweet_ids."""
    pattern = os.path.join(CONTENT_DIR, f"content_plan_*_{account}.json")
    known = set()
    for plan_path in glob.glob(pattern):
        plan = load_json(plan_path)
        if not plan:
            continue
        for post in plan.get("posts", []):
            tweet_id = post.get("tweet_id")
            if tweet_id:
                known.add(str(tweet_id))
            # Also check ghost_tweet_id (ghost tweets that were removed)
            ghost_id = post.get("ghost_tweet_id")
            if ghost_id:
                known.add(str(ghost_id))
    return known


def classify_tweet(tweet: dict) -> str:
    """Determine tweet type from referenced_tweets field."""
    refs = tweet.get("referenced_tweets")
    if not refs:
        return "original"
    for ref in refs:
        ref_type = ref.get("type", "")
        if ref_type == "retweeted":
            return "retweet"
        elif ref_type == "quoted":
            return "quote"
        elif ref_type == "replied_to":
            return "reply"
    return "original"


def get_referenced_id(tweet: dict) -> str | None:
    """Get the ID of the referenced tweet (if any)."""
    refs = tweet.get("referenced_tweets")
    if refs:
        return str(refs[0].get("id", ""))
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch account tweets and identify untracked posts")
    parser.add_argument("--account", required=True, choices=["EN", "JP"], help="Account to fetch")
    parser.add_argument("--max-results", type=int, default=50, help="Number of tweets to fetch (5-100)")
    parser.add_argument("--collect-metrics", action="store_true",
                        help="Store untracked tweet metrics in SQLite")
    args = parser.parse_args()

    # Load account config
    config_path = os.path.join(PROJECT, "config/accounts.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load accounts config: {e}")
        sys.exit(1)

    acct_config = config.get("x_api", {}).get("accounts", {}).get(args.account, {})
    user_id = acct_config.get("user_id")
    handle = acct_config.get("handle", "unknown")

    if not user_id:
        logger.error(f"No user_id configured for {args.account}")
        sys.exit(1)

    # Fetch timeline
    bearer = load_bearer_token()
    client = XApiClient(bearer)

    logger.info(f"Fetching last {args.max_results} tweets for {handle} ({args.account})...")
    timeline = client.get_user_timeline(user_id, max_results=args.max_results)
    logger.info(f"Fetched {len(timeline)} tweets from timeline")

    # Get known tweet IDs from content plans
    known_ids = get_known_tweet_ids(args.account)
    logger.info(f"Found {len(known_ids)} known tweet IDs across all content plans")

    # Partition into tracked vs untracked
    tracked = []
    untracked = []

    for tweet in timeline:
        tweet_id = tweet.get("tweet_id", "")
        if tweet_id in known_ids:
            tracked.append(tweet_id)
        else:
            tweet_type = classify_tweet(tweet)
            ref_id = get_referenced_id(tweet)
            metrics = tweet.get("public_metrics", {})

            untracked.append({
                "tweet_id": tweet_id,
                "text": tweet.get("text", "")[:280],
                "created_at": tweet.get("created_at"),
                "type": tweet_type,
                "referenced_tweet_id": ref_id,
                "public_metrics": {
                    "like_count": metrics.get("like_count", 0),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "bookmark_count": metrics.get("bookmark_count", 0),
                },
                "hashtags": tweet.get("hashtags", []),
                "post_id_assigned": f"{args.account}_MANUAL_{len(untracked) + 1:03d}",
            })

    logger.info(f"Tracked: {len(tracked)}, Untracked: {len(untracked)}")

    # Build output
    now = datetime.now(JST)
    date_str = now.strftime("%Y%m%d")

    output = {
        "date": now.strftime("%Y-%m-%d"),
        "account": args.account,
        "generated_at": now.isoformat(),
        "user_id": user_id,
        "handle": handle,
        "timeline_fetched": len(timeline),
        "tracked_count": len(tracked),
        "untracked_count": len(untracked),
        "untracked_tweets": untracked,
        "tracked_tweet_ids": tracked,
        "type_breakdown": {
            "original": sum(1 for t in untracked if t["type"] == "original"),
            "retweet": sum(1 for t in untracked if t["type"] == "retweet"),
            "quote": sum(1 for t in untracked if t["type"] == "quote"),
            "reply": sum(1 for t in untracked if t["type"] == "reply"),
        },
    }

    output_path = os.path.join(METRICS_DIR, f"untracked_tweets_{date_str}_{args.account}.json")
    os.makedirs(METRICS_DIR, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"Output written to {output_path}")

    # Print summary
    print(f"\n=== Tweet Tracker Summary ({args.account}) ===")
    print(f"Timeline tweets fetched: {len(timeline)}")
    print(f"Tracked (in content plans): {len(tracked)}")
    print(f"Untracked (manual posts): {len(untracked)}")
    print(f"  - Original: {output['type_breakdown']['original']}")
    print(f"  - Retweets: {output['type_breakdown']['retweet']}")
    print(f"  - Quote tweets: {output['type_breakdown']['quote']}")
    print(f"  - Replies: {output['type_breakdown']['reply']}")

    if untracked:
        print(f"\nTop untracked tweets:")
        # Sort by total engagement
        sorted_untracked = sorted(
            untracked,
            key=lambda t: sum(t["public_metrics"].values()),
            reverse=True,
        )
        for t in sorted_untracked[:10]:
            m = t["public_metrics"]
            total = sum(m.values())
            print(f"  [{t['type']:>8}] {t['tweet_id']} | {total} eng | {t['text'][:60]}...")

    # Optionally collect metrics into SQLite
    if args.collect_metrics and untracked:
        import db_manager
        db_manager.init()

        measured_at = now.isoformat()
        count = 0
        for t in untracked:
            m = t["public_metrics"]
            total_eng = m["like_count"] + m["retweet_count"] + m["reply_count"] + m["quote_count"]

            # Calculate hours since posting
            hours_after = 0
            if t.get("created_at"):
                try:
                    created = datetime.fromisoformat(t["created_at"])
                    hours_after = round((now - created).total_seconds() / 3600)
                except (ValueError, TypeError):
                    pass

            db_manager.insert_post_metrics(
                post_id=t["post_id_assigned"],
                tweet_id=t["tweet_id"],
                account=args.account,
                measured_at=measured_at,
                hours_after_post=hours_after,
                likes=m["like_count"],
                retweets=m["retweet_count"],
                replies=m["reply_count"],
                quotes=m["quote_count"],
                bookmarks=m["bookmark_count"],
                impressions=None,
                engagement_rate=None,
                source="timeline_scan",
            )
            count += 1

        logger.info(f"Stored metrics for {count} untracked tweets in SQLite")
        print(f"\nStored {count} untracked tweet metrics in SQLite")

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
