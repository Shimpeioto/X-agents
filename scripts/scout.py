"""Scout Agent — Competitor research via X API v2.

Usage:
    python3 scripts/scout.py                       # full run (all competitors)
    python3 scripts/scout.py --max-competitors 1   # limited run
    python3 scripts/scout.py --max-competitors 5   # limited run
    python3 scripts/scout.py --dry-run             # mock data, no API calls
    python3 scripts/scout.py --force-resolve       # re-resolve all user_ids
    python3 scripts/scout.py --raw                 # write to scout_raw_{date}.json
    python3 scripts/scout.py --compact             # additionally write scout_compact_{date}.json
    python3 scripts/scout.py --raw --compact       # both raw + compact (for Claude Intelligence Mode)
"""

import argparse
import copy
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

    def run(self, max_competitors: int | None = None, force_resolve: bool = False,
            raw: bool = False, compact: bool = False) -> str:
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
        output_path = self.save_report(report, raw=raw, compact=compact)

        logger.info("=" * 60)
        logger.info(f"Scout run completed — {datetime.now(JST).isoformat()}")
        logger.info(f"  Fetched: {len(fetched)} competitors")
        logger.info(f"  Skipped: {len(skipped)} competitors")
        logger.info(f"  Report: {output_path}")
        logger.info("=" * 60)

        return output_path

    def save_report(self, report: dict, raw: bool = False, compact: bool = False) -> str:
        """Save report to appropriate file(s) based on flags.

        --raw: writes to scout_raw_{date}.json instead of scout_report_{date}.json
        --compact: additionally writes scout_compact_{date}.json with _pre_analysis
        No flags: writes to scout_report_{date}.json (original behavior)

        Returns path to the primary output file.
        """
        date_str = datetime.now(JST).strftime("%Y%m%d")
        data_dir = os.path.join(PROJECT, "data")

        # --raw: write full file to scout_raw_{date}.json
        if raw:
            raw_path = os.path.join(data_dir, f"scout_raw_{date_str}.json")
            with open(raw_path, "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"  Raw report: {raw_path}")
            output_path = raw_path
        else:
            # Default: write to scout_report_{date}.json
            output_path = os.path.join(data_dir, f"scout_report_{date_str}.json")
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        # --compact: additionally write compact file
        if compact:
            compact_data = compact_report(report)
            compact_path = os.path.join(data_dir, f"scout_compact_{date_str}.json")
            with open(compact_path, "w") as f:
                json.dump(compact_data, f, indent=2, ensure_ascii=False)
            logger.info(f"  Compact report: {compact_path}")

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


def compute_pre_analysis(report: dict) -> dict:
    """Compute statistics from full data before compaction.

    Analyzes the full recent_posts arrays to produce pre-compaction
    statistics that Claude can use without needing the raw tweet data.
    This solves the problem of Claude needing analytical results from
    data too large to fit in its context window.

    Args:
        report: Full scout report dict with all recent_posts

    Returns:
        Dict with reply_contamination, impression_engagement,
        trending, and hashtag_usage statistics
    """
    all_tweets = []
    per_competitor = []

    for comp in report.get("competitors", []):
        posts = comp.get("recent_posts", [])
        reply_count = sum(1 for p in posts if p.get("text", "").startswith("@"))
        total = len(posts)

        # Reply-filtered engagement rate
        non_reply_posts = [p for p in posts if not p.get("text", "").startswith("@")]
        followers = comp.get("followers", 0)
        if non_reply_posts and followers > 0:
            eng_sum = sum(
                (p.get("public_metrics", {}).get("like_count", 0) +
                 p.get("public_metrics", {}).get("retweet_count", 0) +
                 p.get("public_metrics", {}).get("reply_count", 0) +
                 p.get("public_metrics", {}).get("quote_count", 0))
                for p in non_reply_posts
            )
            eng_rate_excl_replies = eng_sum / (len(non_reply_posts) * followers)
        else:
            eng_rate_excl_replies = 0.0

        # Impression-based engagement (where available)
        imp_posts = [p for p in posts
                     if p.get("public_metrics", {}).get("impression_count", 0) > 0]
        if imp_posts:
            imp_eng = sum(
                (p.get("public_metrics", {}).get("like_count", 0) +
                 p.get("public_metrics", {}).get("retweet_count", 0) +
                 p.get("public_metrics", {}).get("reply_count", 0) +
                 p.get("public_metrics", {}).get("quote_count", 0))
                / p["public_metrics"]["impression_count"]
                for p in imp_posts
            ) / len(imp_posts)
        else:
            imp_eng = None

        per_competitor.append({
            "handle": comp.get("handle"),
            "market": comp.get("market"),
            "reply_rate": reply_count / total if total > 0 else 0.0,
            "reply_count": reply_count,
            "total_sampled": total,
            "engagement_rate_excl_replies": round(eng_rate_excl_replies, 6),
            "impression_based_rate": round(imp_eng, 6) if imp_eng else None,
        })

        all_tweets.extend(posts)

    # Dynamic trending threshold
    all_likes = [t.get("public_metrics", {}).get("like_count", 0) for t in all_tweets]
    if all_likes:
        mean_likes = sum(all_likes) / len(all_likes)
        variance = sum((x - mean_likes) ** 2 for x in all_likes) / len(all_likes)
        stddev_likes = variance ** 0.5
        trending_threshold = mean_likes + 2 * stddev_likes
    else:
        trending_threshold = 0

    trending_posts = [
        {"tweet_id": t.get("tweet_id", ""), "handle": t.get("author_handle", ""),
         "likes": t.get("public_metrics", {}).get("like_count", 0),
         "text_preview": t.get("text", "")[:80]}
        for t in all_tweets
        if t.get("public_metrics", {}).get("like_count", 0) >= trending_threshold
    ]

    # Overall contamination
    total_replies = sum(c["reply_count"] for c in per_competitor)
    total_sampled = sum(c["total_sampled"] for c in per_competitor)

    # Hashtag usage
    competitors_list = report.get("competitors", [])
    comps_with_zero = sum(1 for c in competitors_list
                          if len(c.get("hashtags_used", {})) == 0)

    return {
        "reply_contamination": {
            "overall_rate": round(total_replies / total_sampled, 3) if total_sampled > 0 else 0,
            "total_replies": total_replies,
            "total_sampled": total_sampled,
            "per_competitor": per_competitor,
        },
        "impression_engagement": {
            "per_competitor": [
                {"handle": c["handle"], "rate": c["impression_based_rate"]}
                for c in per_competitor if c["impression_based_rate"] is not None
            ]
        },
        "trending": {
            "threshold": round(trending_threshold, 1),
            "method": "mean + 2*stddev of all sampled tweet likes",
            "posts": trending_posts[:20],
        },
        "hashtag_usage": {
            "competitors_with_zero": comps_with_zero,
            "competitors_with_zero_pct": round(
                comps_with_zero / max(len(competitors_list), 1) * 100, 1),
        }
    }


def compact_report(report: dict) -> dict:
    """Strip large arrays and add pre-analysis stats for Claude.

    1. Computes pre-analysis statistics from full recent_posts data
    2. Strips recent_posts arrays (~10 tweets per competitor)
    3. Strips full tweet text from trending_posts
    4. Trims new_accounts_discovered to summary fields
    5. Adds _pre_analysis section with computed stats

    Reduces ~457KB to ~30KB for Claude context window compatibility.

    Args:
        report: Full scout report dict

    Returns:
        Compact report dict with _pre_analysis section
    """
    # Compute stats BEFORE stripping data
    pre_analysis = compute_pre_analysis(report)

    compact = copy.deepcopy(report)
    for competitor in compact.get("competitors", []):
        competitor.pop("recent_posts", None)
    for topic in compact.get("trending_posts", []):
        topic.pop("full_text", None)
    # Trim new_accounts_discovered to essential fields
    compact["new_accounts_discovered"] = [
        {k: v for k, v in acc.items()
         if k in ("handle", "followers", "engagement_rate", "source", "tweet_count")}
        for acc in compact.get("new_accounts_discovered", [])
    ]

    compact["_pre_analysis"] = pre_analysis
    return compact


def main():
    parser = argparse.ArgumentParser(description="Scout Agent — Competitor Research")
    parser.add_argument("--max-competitors", type=int, default=None, help="Limit number of competitors to fetch")
    parser.add_argument("--dry-run", action="store_true", help="Generate mock data without API calls")
    parser.add_argument("--force-resolve", action="store_true", help="Re-resolve all user_ids")
    parser.add_argument("--raw", action="store_true",
                        help="Write to scout_raw_{date}.json instead of scout_report_{date}.json")
    parser.add_argument("--compact", action="store_true",
                        help="Additionally write scout_compact_{date}.json with pre-analysis stats")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [SCOUT] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    config_path = os.path.join(PROJECT, "config", "competitors.json")
    scout = Scout(config_path, dry_run=args.dry_run)
    output_path = scout.run(
        max_competitors=args.max_competitors,
        force_resolve=args.force_resolve,
        raw=args.raw,
        compact=args.compact,
    )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
