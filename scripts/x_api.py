"""X API v2 wrapper using tweepy. Used by Scout (Phase 1) and later Publisher/Analyst."""

import tweepy
import time
import logging
import os
import json

logger = logging.getLogger(__name__)

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_RETRIES = 3
RETRY_WAIT = 5  # seconds

USER_FIELDS = ["public_metrics", "description"]
TWEET_FIELDS = ["public_metrics", "created_at", "entities"]


def load_bearer_token() -> str:
    """Load bearer token from config/accounts.json."""
    config_path = os.path.join(PROJECT, "config/accounts.json")
    with open(config_path) as f:
        config = json.load(f)
    return config["x_api"]["bearer_token"]


class XApiClient:
    """X API v2 wrapper using tweepy."""

    def __init__(self, bearer_token: str):
        """Initialize with bearer token for read-only access."""
        self.client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)

    def resolve_user_id(self, handle: str) -> dict | None:
        """Resolve a handle to user_id + public_metrics.

        Args:
            handle: X handle (with or without @ prefix)

        Returns:
            {"user_id": str, "username": str, "name": str,
             "description": str, "public_metrics": dict} or None if not found
        """
        handle = handle.lstrip("@")
        response = self._api_call_with_retry(
            self.client.get_user,
            username=handle,
            user_fields=USER_FIELDS,
        )
        if response is None or response.data is None:
            return None
        return self._normalize_user(response.data)

    def get_user_info_batch(self, user_ids: list[str]) -> list[dict]:
        """Batch lookup of user info by user_ids (up to 100 per request).

        Returns list of user data dicts with public_metrics.
        """
        results = []
        # Process in batches of 100
        for i in range(0, len(user_ids), 100):
            batch = user_ids[i : i + 100]
            response = self._api_call_with_retry(
                self.client.get_users,
                ids=batch,
                user_fields=USER_FIELDS,
            )
            if response and response.data:
                for user in response.data:
                    normalized = self._normalize_user(user)
                    if normalized:
                        results.append(normalized)
        return results

    def get_user_timeline(self, user_id: str, max_results: int = 10) -> list[dict]:
        """Fetch recent tweets for a user.

        Args:
            user_id: The user's numeric ID
            max_results: Number of tweets to fetch (5-100)

        Returns:
            List of tweet dicts with text, public_metrics, created_at, entities
        """
        response = self._api_call_with_retry(
            self.client.get_users_tweets,
            id=user_id,
            max_results=max(5, min(max_results, 100)),
            tweet_fields=TWEET_FIELDS,
        )
        if response is None or response.data is None:
            return []
        return [self._normalize_tweet(t) for t in response.data if t is not None]

    def search_recent(self, query: str, max_results: int = 10) -> list[dict]:
        """Search recent tweets by keyword.

        Args:
            query: Search query string
            max_results: Number of results (10-100)

        Returns:
            List of tweet dicts with author info
        """
        response = self._api_call_with_retry(
            self.client.search_recent_tweets,
            query=query,
            max_results=max(10, min(max_results, 100)),
            tweet_fields=TWEET_FIELDS,
            expansions=["author_id"],
            user_fields=USER_FIELDS,
        )
        if response is None or response.data is None:
            return []

        # Build author lookup from includes
        authors = {}
        if response.includes and "users" in response.includes:
            for user in response.includes["users"]:
                authors[str(user.id)] = self._normalize_user(user)

        tweets = []
        for tweet in response.data:
            normalized = self._normalize_tweet(tweet)
            if normalized:
                author_id = str(tweet.author_id) if tweet.author_id else None
                normalized["author"] = authors.get(author_id, {})
                tweets.append(normalized)
        return tweets

    def _normalize_user(self, user) -> dict | None:
        """Convert tweepy User object to plain dict."""
        if user is None:
            return None
        return {
            "user_id": str(user.id),
            "username": user.username,
            "name": user.name,
            "description": user.description or "",
            "public_metrics": dict(user.public_metrics) if user.public_metrics else {},
        }

    def _normalize_tweet(self, tweet) -> dict | None:
        """Convert tweepy Tweet object to plain dict."""
        if tweet is None:
            return None
        entities = tweet.entities if hasattr(tweet, "entities") and tweet.entities else {}
        hashtags = []
        if "hashtags" in entities:
            hashtags = [f"#{h['tag']}" for h in entities["hashtags"]]
        return {
            "tweet_id": str(tweet.id),
            "text": tweet.text,
            "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
            "public_metrics": dict(tweet.public_metrics) if tweet.public_metrics else {},
            "entities": entities,
            "hashtags": hashtags,
        }

    def _api_call_with_retry(self, func, *args, **kwargs):
        """Execute an API call with retry logic.

        Handles: TooManyRequests (429), NotFound (404), Forbidden (401/403).
        Returns None on permanent failures.
        """
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except tweepy.TooManyRequests as e:
                reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
                wait = max(reset_time - int(time.time()), RETRY_WAIT)
                logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
            except tweepy.NotFound:
                logger.warning(f"Not found (404)")
                return None
            except tweepy.Forbidden:
                logger.warning(f"Forbidden — suspended or protected (401/403)")
                return None
            except tweepy.Unauthorized:
                logger.error("Unauthorized (401) — check bearer token in config/accounts.json")
                return None
            except Exception as e:
                logger.error(f"API error: {e} (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_WAIT)
        logger.error(f"All {MAX_RETRIES} retries exhausted")
        return None
