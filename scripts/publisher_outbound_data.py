#!/usr/bin/env python3
"""Fetch target account data for Claude Publisher smart outbound planning.

Usage:
    python3 scripts/publisher_outbound_data.py --account EN --targets "@handle1,@handle2"

Output: JSON printed to stdout with target account info and recent tweets.
"""

import argparse
import json
import logging
import os
import sys

# Ensure project root is importable
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

from x_api import XApiClient, load_bearer_token

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [PUBLISHER_DATA] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,  # Log to stderr so stdout is clean JSON
)
logger = logging.getLogger(__name__)


class OutboundDataFetcher:
    """Fetches target account info and recent tweets for Claude analysis."""

    def __init__(self):
        """Initialize with read-only X API client.

        Uses the shared bearer token (read-only access) — same as
        scout.py and analyst.py. Account parameter is not needed for
        read-only operations; the bearer token works across all accounts.
        """
        bearer = load_bearer_token()
        self.client = XApiClient(bearer)

    def fetch_target(self, handle: str) -> dict:
        """Fetch one target account's info and recent tweets.

        Steps:
        1. Resolve handle to user_id
        2. Fetch user info (followers, bio)
        3. Fetch 5 most recent tweets with full text and public_metrics

        Args:
            handle: X handle (with or without @)

        Returns:
            Dict with handle, user_id, followers, bio, recent_tweets[]
        """
        handle = handle.lstrip("@")
        logger.info(f"Fetching target: @{handle}")

        # Resolve user
        user_info = self.client.resolve_user_id(handle)
        if not user_info:
            logger.warning(f"Could not resolve @{handle}")
            return {"handle": f"@{handle}", "error": "not_found"}

        user_id = user_info["user_id"]
        public_metrics = user_info.get("public_metrics", {})

        # Fetch recent tweets
        tweets = self.client.get_user_timeline(
            user_id=user_id,
            max_results=5,
        )

        return {
            "handle": f"@{handle}",
            "user_id": user_id,
            "followers": public_metrics.get("followers_count", 0),
            "bio": user_info.get("description", ""),
            "recent_tweets": [
                {
                    "tweet_id": t["tweet_id"],
                    "text": t["text"],
                    "likes": t.get("public_metrics", {}).get("like_count", 0),
                    "retweets": t.get("public_metrics", {}).get("retweet_count", 0),
                    "replies": t.get("public_metrics", {}).get("reply_count", 0),
                    "created_at": t.get("created_at", ""),
                }
                for t in tweets
            ],
        }

    def fetch_all(self, targets: list[str]) -> dict:
        """Fetch data for all target accounts.

        Args:
            targets: List of X handles

        Returns:
            Dict with targets[] array
        """
        results = []
        for handle in targets:
            data = self.fetch_target(handle)
            results.append(data)
        return {"targets": results}


def main():
    parser = argparse.ArgumentParser(
        description="Fetch target account data for smart outbound planning"
    )
    parser.add_argument("--account", required=True, choices=["EN", "JP"],
                        help="Account context (EN or JP)")
    parser.add_argument("--targets", required=True,
                        help="Comma-separated handles (e.g., '@handle1,@handle2')")
    args = parser.parse_args()

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    if not targets:
        logger.error("No targets provided")
        sys.exit(1)

    fetcher = OutboundDataFetcher()
    result = fetcher.fetch_all(targets)

    # Print JSON to stdout (logs go to stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
