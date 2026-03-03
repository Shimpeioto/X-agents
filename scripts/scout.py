"""Scout Agent — Competitor research via X API v2.

Usage:
    python3 scripts/scout.py                       # full run (all competitors)
    python3 scripts/scout.py --max-competitors 1   # limited run
    python3 scripts/scout.py --max-competitors 5   # limited run
    python3 scripts/scout.py --dry-run             # mock data, no API calls
    python3 scripts/scout.py --force-resolve       # re-resolve all user_ids
"""

import argparse
import json
import logging
import os
import random
import sys
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

# Ensure project root is importable
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from scripts.x_api import XApiClient, load_bearer_token

logger = logging.getLogger("scout")
JST = ZoneInfo("Asia/Tokyo")


class Scout:
    """Competitor research agent."""

    def __init__(self, config_path: str, dry_run: bool = False):
        """Load competitors.json and initialize X API client."""
        self.config_path = config_path
        self.dry_run = dry_run

        with open(config_path) as f:
            self.config = json.load(f)

        self.competitors = self.config["competitors"]
        self.tracked_keywords = self.config.get("tracked_keywords", [])

        if not dry_run:
            bearer_token = load_bearer_token()
            self.api = XApiClient(bearer_token)
        else:
            self.api = None

    def resolve_user_ids(self, force: bool = False) -> int:
        """Resolve empty user_ids in competitors.json.

        Returns number of newly resolved IDs.
        Writes updated IDs back to competitors.json.
        """
        if self.dry_run:
            logger.info("[DRY RUN] Skipping user_id resolution")
            return 0

        resolved_count = 0
        for comp in self.competitors:
            if comp["user_id"] and not force:
                continue

            handle = comp["handle"].lstrip("@")
            logger.info(f"Resolving user_id for @{handle}...")
            user_data = self.api.resolve_user_id(handle)

            if user_data:
                comp["user_id"] = user_data["user_id"]
                resolved_count += 1
                logger.info(f"  -> {user_data['user_id']} ({user_data['name']})")
            else:
                logger.warning(f"  -> Could not resolve @{handle}")

        # Write back to competitors.json
        if resolved_count > 0:
            self.config["competitors"] = self.competitors
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Resolved {resolved_count} user_ids, saved to {self.config_path}")

        return resolved_count

    def fetch_all_competitors(self, max_competitors: int | None = None) -> tuple[list[dict], list[dict]]:
        """Fetch data for all (or max_competitors) competitors.

        Returns (fetched_competitors, skipped_competitors).
        """
        fetched = []
        skipped = []
        targets = self.competitors[:max_competitors] if max_competitors else self.competitors

        for i, comp in enumerate(targets):
            handle = comp["handle"].lstrip("@")
            logger.info(f"[{i + 1}/{len(targets)}] Fetching @{handle}...")

            if not comp.get("user_id"):
                logger.warning(f"  Skipping @{handle} — no user_id")
                skipped.append({
                    "handle": handle,
                    "status": "no_user_id",
                    "reason": "user_id not resolved",
                })
                continue

            result = self.fetch_competitor(comp)
            if result["status"] == "ok":
                fetched.append(result)
            else:
                skipped.append({
                    "handle": handle,
                    "status": result["status"],
                    "reason": result.get("reason", "Unknown error"),
                })

        return fetched, skipped

    def fetch_competitor(self, competitor: dict) -> dict:
        """Fetch data for a single competitor.

        Returns enriched competitor dict with recent_posts, metrics, etc.
        """
        handle = competitor["handle"].lstrip("@")
        user_id = competitor["user_id"]
        market = competitor.get("market", "EN")
        category = competitor.get("category", "ai_beauty")

        # Get fresh user info
        user_data = self.api.resolve_user_id(handle)
        if user_data is None:
            return {
                "handle": handle,
                "user_id": user_id,
                "status": "not_found",
                "reason": "Account not found or suspended",
                "market": market,
            }

        metrics = user_data.get("public_metrics", {})
        followers = metrics.get("followers_count", 0)
        following = metrics.get("following_count", 0)
        tweet_count = metrics.get("tweet_count", 0)

        # Get recent tweets
        tweets = self.api.get_user_timeline(user_id, max_results=10)

        # Calculate engagement rates per tweet
        for tweet in tweets:
            pm = tweet.get("public_metrics", {})
            likes = pm.get("like_count", 0)
            rts = pm.get("retweet_count", 0)
            replies = pm.get("reply_count", 0)
            quotes = pm.get("quote_count", 0)
            total_engagement = likes + rts + replies + quotes
            tweet["engagement_rate"] = round(total_engagement / followers, 6) if followers > 0 else 0.0

        # Average engagement rate
        if tweets:
            avg_engagement = sum(t["engagement_rate"] for t in tweets) / len(tweets)
        else:
            avg_engagement = 0.0

        # Top 3 posts by engagement rate
        sorted_tweets = sorted(tweets, key=lambda t: t["engagement_rate"], reverse=True)
        top_posts = [
            {
                "tweet_id": t["tweet_id"],
                "engagement_rate": t["engagement_rate"],
                "like_count": t.get("public_metrics", {}).get("like_count", 0),
            }
            for t in sorted_tweets[:3]
        ]

        # Posting frequency (posts per day)
        posting_frequency = 0.0
        if len(tweets) >= 2:
            dates = [t["created_at"] for t in tweets if t.get("created_at")]
            if len(dates) >= 2:
                from datetime import datetime as dt

                try:
                    first = dt.fromisoformat(dates[-1].replace("Z", "+00:00"))
                    last = dt.fromisoformat(dates[0].replace("Z", "+00:00"))
                    days_span = max((last - first).total_seconds() / 86400, 1)
                    posting_frequency = round(len(tweets) / days_span, 1)
                except (ValueError, TypeError):
                    posting_frequency = 0.0

        # Hashtags used
        hashtag_counter = Counter()
        for tweet in tweets:
            for tag in tweet.get("hashtags", []):
                hashtag_counter[tag] += 1

        return {
            "handle": handle,
            "user_id": user_id,
            "display_name": user_data.get("name", ""),
            "status": "ok",
            "market": market,
            "category": category,
            "followers": followers,
            "following": following,
            "tweet_count": tweet_count,
            "description": user_data.get("description", ""),
            "recent_posts": tweets,
            "avg_engagement_rate": round(avg_engagement, 6),
            "posting_frequency": posting_frequency,
            "top_posts": top_posts,
            "hashtags_used": dict(hashtag_counter),
        }

    def search_keywords(self) -> dict:
        """Search tracked keywords for trending content.

        Returns {trending_topics, trending_posts, new_accounts_discovered}.
        """
        if self.dry_run:
            return self._mock_keyword_data()

        known_handles = {c["handle"].lstrip("@").lower() for c in self.competitors}
        trending_topics = []
        all_trending_tweets = []
        new_accounts = []

        for keyword in self.tracked_keywords:
            logger.info(f"Searching keyword: {keyword}")
            tweets = self.api.search_recent(keyword, max_results=10)

            sample_tweets = []
            for tweet in tweets:
                author = tweet.get("author", {})
                author_handle = author.get("username", "unknown")
                pm = tweet.get("public_metrics", {})
                like_count = pm.get("like_count", 0)

                sample_tweets.append({
                    "tweet_id": tweet["tweet_id"],
                    "text": tweet["text"][:280],
                    "author": author_handle,
                    "like_count": like_count,
                })

                # Check for new accounts
                if author_handle.lower() not in known_handles and author_handle != "unknown":
                    author_followers = author.get("public_metrics", {}).get("followers_count", 0)
                    if not any(na["handle"] == author_handle for na in new_accounts):
                        new_accounts.append({
                            "handle": author_handle,
                            "followers": author_followers,
                            "source": f"keyword_search:{keyword}",
                        })

                # Track high-engagement tweets for trending_posts
                if like_count >= 100:
                    followers = author.get("public_metrics", {}).get("followers_count", 1)
                    all_trending_tweets.append({
                        "tweet_id": tweet["tweet_id"],
                        "text": tweet["text"][:280],
                        "author": author_handle,
                        "like_count": like_count,
                        "engagement_rate": round(like_count / max(followers, 1), 4),
                    })

            trending_topics.append({
                "keyword": keyword,
                "sample_tweets": sample_tweets[:5],
            })

        # Sort trending posts by likes, top 10
        trending_posts = sorted(all_trending_tweets, key=lambda t: t["like_count"], reverse=True)[:10]

        return {
            "trending_topics": trending_topics,
            "trending_posts": trending_posts,
            "new_accounts_discovered": new_accounts,
        }

    def analyze(self, competitors: list[dict], keyword_data: dict) -> dict:
        """Combine all data into the final scout report."""
        now = datetime.now(JST)

        # Hashtag frequency across all competitors
        hashtag_freq = Counter()
        hashtag_by_market = {"EN": Counter(), "JP": Counter()}
        for comp in competitors:
            market = comp.get("market", "EN")
            for tag, count in comp.get("hashtags_used", {}).items():
                hashtag_freq[tag] += count
                if market == "both":
                    hashtag_by_market["EN"][tag] += count
                    hashtag_by_market["JP"][tag] += count
                elif market in hashtag_by_market:
                    hashtag_by_market[market][tag] += count

        # Market comparison
        market_groups = {"EN": [], "JP": []}
        for comp in competitors:
            market = comp.get("market", "EN")
            if market == "both":
                market_groups["EN"].append(comp)
                market_groups["JP"].append(comp)
            elif market in market_groups:
                market_groups[market].append(comp)

        market_comparison = {}
        for market, group in market_groups.items():
            if not group:
                market_comparison[market] = {
                    "competitor_count": 0,
                    "avg_followers": 0,
                    "avg_engagement_rate": 0.0,
                    "avg_posting_frequency": 0.0,
                    "top_hashtags": [],
                }
                continue

            avg_followers = int(sum(c.get("followers", 0) for c in group) / len(group))
            avg_engagement = round(sum(c.get("avg_engagement_rate", 0) for c in group) / len(group), 6)
            avg_posting_freq = round(sum(c.get("posting_frequency", 0) for c in group) / len(group), 1)

            # Top hashtags for this market
            market_tags = hashtag_by_market.get(market, Counter())
            top_hashtags = [tag for tag, _ in market_tags.most_common(5)]

            market_comparison[market] = {
                "competitor_count": len(group),
                "avg_followers": avg_followers,
                "avg_engagement_rate": avg_engagement,
                "avg_posting_frequency": avg_posting_freq,
                "top_hashtags": top_hashtags,
            }

        return {
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.isoformat(),
            "competitors_total": len(self.competitors),
            "competitors_fetched": len(competitors),
            "competitors_skipped": len(self.competitors) - len(competitors),
            "competitors": competitors,
            "skipped_competitors": [],  # filled by caller
            "hashtag_frequency": dict(hashtag_freq.most_common(50)),
            "hashtag_by_market": {
                market: dict(counts.most_common(20))
                for market, counts in hashtag_by_market.items()
            },
            "market_comparison": market_comparison,
            "trending_topics": keyword_data.get("trending_topics", []),
            "trending_posts": keyword_data.get("trending_posts", []),
            "new_accounts_discovered": keyword_data.get("new_accounts_discovered", []),
        }

    def run(self, max_competitors: int | None = None, force_resolve: bool = False) -> str:
        """Full scout run. Returns path to output file."""
        logger.info("=" * 60)
        logger.info(f"Scout run started — {datetime.now(JST).isoformat()}")
        logger.info(f"  Competitors in config: {len(self.competitors)}")
        logger.info(f"  Max competitors: {max_competitors or 'all'}")
        logger.info(f"  Dry run: {self.dry_run}")
        logger.info("=" * 60)

        # Step 1: Resolve user_ids
        if self.dry_run:
            logger.info("[DRY RUN] Using mock data")
            fetched, skipped = self._mock_competitors()
            keyword_data = self._mock_keyword_data()
        else:
            resolved = self.resolve_user_ids(force=force_resolve)
            logger.info(f"Resolved {resolved} new user_ids")

            # Step 2: Fetch competitor data
            fetched, skipped = self.fetch_all_competitors(max_competitors)
            logger.info(f"Fetched: {len(fetched)}, Skipped: {len(skipped)}")

            # Step 3: Search keywords
            keyword_data = self.search_keywords()
            logger.info(f"Keywords searched: {len(self.tracked_keywords)}")
            logger.info(f"New accounts discovered: {len(keyword_data.get('new_accounts_discovered', []))}")

        # Step 4: Analyze
        report = self.analyze(fetched, keyword_data)
        report["skipped_competitors"] = skipped
        report["competitors_skipped"] = len(skipped)

        # Step 5: Save
        output_path = self.save_report(report)

        logger.info("=" * 60)
        logger.info(f"Scout run completed — {datetime.now(JST).isoformat()}")
        logger.info(f"  Fetched: {len(fetched)} competitors")
        logger.info(f"  Skipped: {len(skipped)} competitors")
        logger.info(f"  Report: {output_path}")
        logger.info("=" * 60)

        return output_path

    def save_report(self, report: dict) -> str:
        """Save report to data/scout_report_{YYYYMMDD}.json. Returns file path."""
        date_str = datetime.now(JST).strftime("%Y%m%d")
        filename = f"scout_report_{date_str}.json"
        output_path = os.path.join(PROJECT, "data", filename)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_path

    # ── Dry-run mock data generators ─────────────────────────────

    def _mock_competitors(self) -> tuple[list[dict], list[dict]]:
        """Generate synthetic competitor data for dry-run mode."""
        mock_fetched = []
        mock_handles_en = [
            ("mock_en_1", "1001", "MockCreator EN 1", "EN"),
            ("mock_en_2", "1002", "MockCreator EN 2", "EN"),
            ("mock_en_3", "1003", "MockCreator EN 3", "EN"),
            ("mock_en_4", "1004", "MockCreator EN 4", "EN"),
            ("mock_en_5", "1005", "MockCreator EN 5", "EN"),
        ]
        mock_handles_jp = [
            ("mock_jp_1", "2001", "MockCreator JP 1", "JP"),
            ("mock_jp_2", "2002", "MockCreator JP 2", "JP"),
            ("mock_jp_3", "2003", "MockCreator JP 3", "JP"),
        ]

        for handle, uid, name, market in mock_handles_en + mock_handles_jp:
            followers = random.randint(5000, 50000)
            tweets = []
            for j in range(10):
                likes = random.randint(50, 2000)
                rts = random.randint(5, 200)
                replies = random.randint(2, 50)
                quotes = random.randint(0, 20)
                eng_rate = round((likes + rts + replies + quotes) / max(followers, 1), 6)
                tags = random.sample(
                    ["#AIart", "#AIbeauty", "#AIgirl", "#midjourney", "#stablediffusion", "#aiイラスト", "#AI美女"],
                    k=random.randint(1, 3),
                )
                tweets.append({
                    "tweet_id": f"mock_{uid}_{j}",
                    "text": f"Mock tweet {j} from @{handle} {' '.join(tags)}",
                    "created_at": f"2026-03-0{min(j+1,9)}T{10+j}:00:00+00:00",
                    "public_metrics": {
                        "like_count": likes,
                        "retweet_count": rts,
                        "reply_count": replies,
                        "quote_count": quotes,
                        "bookmark_count": random.randint(0, 30),
                    },
                    "entities": {},
                    "hashtags": tags,
                    "engagement_rate": eng_rate,
                })

            avg_eng = round(sum(t["engagement_rate"] for t in tweets) / len(tweets), 6)
            sorted_tweets = sorted(tweets, key=lambda t: t["engagement_rate"], reverse=True)

            hashtag_counter = Counter()
            for t in tweets:
                for tag in t["hashtags"]:
                    hashtag_counter[tag] += 1

            mock_fetched.append({
                "handle": handle,
                "user_id": uid,
                "display_name": name,
                "status": "ok",
                "market": market,
                "category": "ai_beauty",
                "followers": followers,
                "following": random.randint(100, 2000),
                "tweet_count": random.randint(500, 5000),
                "description": f"Mock AI beauty account ({market})",
                "recent_posts": tweets,
                "avg_engagement_rate": avg_eng,
                "posting_frequency": round(random.uniform(1.5, 5.0), 1),
                "top_posts": [
                    {
                        "tweet_id": t["tweet_id"],
                        "engagement_rate": t["engagement_rate"],
                        "like_count": t["public_metrics"]["like_count"],
                    }
                    for t in sorted_tweets[:3]
                ],
                "hashtags_used": dict(hashtag_counter),
            })

        skipped = [{
            "handle": "mock_suspended",
            "status": "suspended",
            "reason": "Account suspended (mock)",
        }]
        return mock_fetched, skipped

    def _mock_keyword_data(self) -> dict:
        """Generate synthetic keyword search data for dry-run mode."""
        trending_topics = []
        for kw in self.tracked_keywords[:4]:
            trending_topics.append({
                "keyword": kw,
                "sample_tweets": [
                    {
                        "tweet_id": f"mock_trend_{kw}_{i}",
                        "text": f"Trending tweet about {kw} #{kw.lstrip('#')}",
                        "author": f"trend_author_{i}",
                        "like_count": random.randint(100, 5000),
                    }
                    for i in range(3)
                ],
            })

        return {
            "trending_topics": trending_topics,
            "trending_posts": [
                {
                    "tweet_id": "mock_viral_1",
                    "text": "This AI beauty post went viral! #AIbeauty #AIart",
                    "author": "viral_creator",
                    "like_count": 10000,
                    "engagement_rate": 0.12,
                }
            ],
            "new_accounts_discovered": [
                {
                    "handle": "new_ai_creator_mock",
                    "followers": 8500,
                    "source": "keyword_search:#AIbeauty",
                }
            ],
        }


def main():
    parser = argparse.ArgumentParser(description="Scout Agent — Competitor Research")
    parser.add_argument("--max-competitors", type=int, default=None, help="Limit number of competitors to fetch")
    parser.add_argument("--dry-run", action="store_true", help="Generate mock data without API calls")
    parser.add_argument("--force-resolve", action="store_true", help="Re-resolve all user_ids")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [SCOUT] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    config_path = os.path.join(PROJECT, "config", "competitors.json")
    scout = Scout(config_path, dry_run=args.dry_run)
    output_path = scout.run(max_competitors=args.max_competitors, force_resolve=args.force_resolve)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
