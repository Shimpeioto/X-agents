"""X API v2 wrapper using tweepy. Used by Scout (Phase 1), Publisher (Phase 3), and Analyst."""

import tweepy
import time
import logging
import os
import json

logger = logging.getLogger(__name__)

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MAX_RETRIES = 3
RETRY_WAIT = 5  # seconds
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB per global rules

USER_FIELDS = ["public_metrics", "description", "profile_image_url"]
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

    def get_tweets_batch(self, tweet_ids: list[str]) -> list[dict]:
        """Batch lookup tweets by IDs (up to 100 per request).

        Args:
            tweet_ids: List of tweet ID strings

        Returns:
            List of normalized tweet dicts. Deleted/not-found tweets are skipped.
        """
        results = []
        for i in range(0, len(tweet_ids), 100):
            batch = tweet_ids[i : i + 100]
            response = self._api_call_with_retry(
                self.client.get_tweets,
                ids=batch,
                tweet_fields=TWEET_FIELDS,
            )
            if response and response.data:
                for tweet in response.data:
                    normalized = self._normalize_tweet(tweet)
                    if normalized:
                        results.append(normalized)
        return results

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
            "profile_image_url": getattr(user, "profile_image_url", None),
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


def load_account_credentials(account: str) -> dict:
    """Load OAuth 1.0a credentials for a specific account (EN or JP).

    Returns dict with keys: consumer_key, consumer_secret, access_token,
    access_token_secret, user_id, handle.
    """
    config_path = os.path.join(PROJECT, "config/accounts.json")
    with open(config_path) as f:
        config = json.load(f)
    x_api = config["x_api"]
    acct = x_api["accounts"][account]
    return {
        "consumer_key": x_api["consumer_key"],
        "consumer_secret": x_api["consumer_secret"],
        "access_token": acct["access_token"],
        "access_token_secret": acct["access_token_secret"],
        "user_id": acct.get("user_id"),
        "handle": acct.get("handle"),
    }


class XApiWriteClient:
    """X API write client using OAuth 1.0a user context for posting, likes, follows."""

    def __init__(self, account: str):
        """Initialize with OAuth 1.0a credentials for the given account.

        Args:
            account: "EN" or "JP"
        """
        self.account = account
        creds = load_account_credentials(account)
        self._configured_user_id = creds.get("user_id")
        self._cached_user_id = None

        # tweepy.Client for v2 endpoints (post, like, follow)
        self.client = tweepy.Client(
            consumer_key=creds["consumer_key"],
            consumer_secret=creds["consumer_secret"],
            access_token=creds["access_token"],
            access_token_secret=creds["access_token_secret"],
            wait_on_rate_limit=False,
        )

        # tweepy.API for v1.1 media upload
        auth = tweepy.OAuth1UserHandler(
            consumer_key=creds["consumer_key"],
            consumer_secret=creds["consumer_secret"],
            access_token=creds["access_token"],
            access_token_secret=creds["access_token_secret"],
        )
        self.api_v1 = tweepy.API(auth)

    def get_own_user_id(self) -> str:
        """Get the authenticated user's ID (cached after first call)."""
        if self._cached_user_id:
            return self._cached_user_id
        if self._configured_user_id:
            self._cached_user_id = self._configured_user_id
            return self._cached_user_id
        response = self._call_with_retry(self.client.get_me)
        if response and response.data:
            self._cached_user_id = str(response.data.id)
            return self._cached_user_id
        raise RuntimeError(f"Failed to get user ID for {self.account}")

    def upload_media(self, file_path: str) -> str:
        """Upload media file via v1.1 API. Returns media_id string.

        Args:
            file_path: Path to image file (must be <2MB per global rules)

        Raises:
            ValueError: If file exceeds 2MB
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Media file not found: {file_path}")
        file_size = os.path.getsize(file_path)
        if file_size > MAX_IMAGE_SIZE:
            raise ValueError(f"Image {file_path} is {file_size} bytes, max is {MAX_IMAGE_SIZE} (2MB)")
        media = self._call_with_retry(self.api_v1.media_upload, filename=file_path)
        if media is None:
            raise RuntimeError(f"Failed to upload media: {file_path}")
        return str(media.media_id)

    def create_post(self, text: str, media_ids: list[str] | None = None,
                    reply_to_tweet_id: str | None = None) -> dict:
        """Create a tweet. Returns {"tweet_id": str, "text": str}.

        Args:
            text: Tweet text
            media_ids: Optional list of media_id strings from upload_media()
            reply_to_tweet_id: Optional tweet ID to reply to
        """
        kwargs = {"text": text}
        if media_ids:
            kwargs["media_ids"] = media_ids
        if reply_to_tweet_id:
            kwargs["in_reply_to_tweet_id"] = reply_to_tweet_id
        response = self._call_with_retry(self.client.create_tweet, **kwargs)
        if response is None or response.data is None:
            raise RuntimeError(f"Failed to create tweet for {self.account}")
        tweet_id = str(response.data["id"])
        return {"tweet_id": tweet_id, "text": text}

    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet. Returns True on success."""
        user_id = self.get_own_user_id()
        response = self._call_with_retry(self.client.like, tweet_id=tweet_id, user_auth=True)
        return response is not None

    def reply_to_tweet(self, tweet_id: str, text: str) -> dict | None:
        """Reply to a tweet. Returns {"tweet_id": str, "text": str} or None."""
        try:
            result = self.create_post(text=text, reply_to_tweet_id=tweet_id)
            return result
        except RuntimeError:
            return None

    def follow_user(self, target_user_id: str) -> bool:
        """Follow a user. Returns True on success."""
        user_id = self.get_own_user_id()
        response = self._call_with_retry(self.client.follow_user, target_user_id=target_user_id, user_auth=True)
        return response is not None

    def _call_with_retry(self, func, *args, **kwargs):
        """Execute an API call with retry logic (same pattern as XApiClient)."""
        for attempt in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except tweepy.TooManyRequests as e:
                reset_time = int(e.response.headers.get("x-rate-limit-reset", 0))
                wait = max(reset_time - int(time.time()), RETRY_WAIT)
                logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
            except tweepy.NotFound:
                logger.warning("Not found (404)")
                return None
            except tweepy.Forbidden as e:
                logger.warning(f"Forbidden (403): {e}")
                return None
            except tweepy.Unauthorized:
                logger.error(f"Unauthorized (401) — check OAuth creds for {self.account}")
                return None
            except Exception as e:
                logger.error(f"API error: {e} (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_WAIT)
        logger.error(f"All {MAX_RETRIES} retries exhausted")
        return None
