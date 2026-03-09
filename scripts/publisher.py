"""Publisher agent — Posts approved content to X and runs outbound engagement.

Usage:
    python3 scripts/publisher.py post --account EN          # Post all approved
    python3 scripts/publisher.py post --account EN --slot 1 # Post specific slot
    python3 scripts/publisher.py outbound --account EN      # Run outbound engagement (legacy)
    python3 scripts/publisher.py smart-outbound --account EN --plan data/outbound_plan_20260305_EN.json
    python3 scripts/publisher.py --dry-run post --account EN # Log only, no API calls

Exit codes: 0=success, 1=error, 2=usage error
"""

import argparse
import glob
import json
import logging
import os
import random
import shutil
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Add project root to path
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

from x_api import XApiClient, XApiWriteClient, load_bearer_token

JST = ZoneInfo("Asia/Tokyo")
DATA_DIR = os.path.join(PROJECT, "data")
MEDIA_PENDING = os.path.join(PROJECT, "media", "pending")
MEDIA_POSTED = os.path.join(PROJECT, "media", "posted")

# Rate limits per account per day (per global rules)
RATE_LIMITS = {
    "posts": 5,
    "likes": 30,
    "replies": 10,
    "follows": 5,
}

# Outbound delay range (seconds) between operations
OUTBOUND_DELAY_MIN = 30
OUTBOUND_DELAY_MAX = 120

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [PUBLISHER] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def today_str() -> str:
    return datetime.now(JST).strftime("%Y%m%d")


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


def load_rate_limits(date: str) -> dict:
    """Load or initialize rate limits for today."""
    path = os.path.join(DATA_DIR, f"rate_limits_{date}.json")
    data = load_json(path)
    if data:
        return data
    # Initialize
    return {
        "date": f"{date[:4]}-{date[4:6]}-{date[6:8]}",
        "EN": {k: {"used": 0, "limit": v} for k, v in RATE_LIMITS.items()},
        "JP": {k: {"used": 0, "limit": v} for k, v in RATE_LIMITS.items()},
    }


def save_rate_limits(date: str, limits: dict) -> None:
    path = os.path.join(DATA_DIR, f"rate_limits_{date}.json")
    save_json(path, limits)


def check_rate_limit(limits: dict, account: str, action: str) -> bool:
    """Check if we're within rate limits. Returns True if OK."""
    section = limits.get(account, {}).get(action, {})
    used = section.get("used", 0)
    limit = section.get("limit", 0)
    if used >= limit:
        logger.warning(f"Rate limit reached for {account} {action}: {used}/{limit}")
        return False
    return True


def increment_rate_limit(limits: dict, account: str, action: str) -> None:
    limits[account][action]["used"] += 1


def find_media(post_id: str) -> str | None:
    """Find media file for a post in media/pending/."""
    for ext in ["png", "jpg", "jpeg", "webp"]:
        path = os.path.join(MEDIA_PENDING, f"{post_id}.{ext}")
        if os.path.exists(path):
            return path
    # Also check glob for case-insensitive
    pattern = os.path.join(MEDIA_PENDING, f"{post_id}.*")
    matches = glob.glob(pattern)
    for m in matches:
        if m.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return m
    return None


def move_media_to_posted(media_path: str) -> None:
    """Move media file from pending to posted."""
    os.makedirs(MEDIA_POSTED, exist_ok=True)
    dest = os.path.join(MEDIA_POSTED, os.path.basename(media_path))
    shutil.move(media_path, dest)
    logger.info(f"Moved media to {dest}")


def post_url(account_handle: str, tweet_id: str) -> str:
    """Construct the post URL."""
    handle = account_handle.lstrip("@")
    return f"https://x.com/{handle}/status/{tweet_id}"


# --- Post Subcommand ---

def run_post(account: str, slot: int | None, dry_run: bool) -> int:
    """Post approved content for an account. Returns 0 on success, 1 on error."""
    date = today_str()
    plan_path = os.path.join(DATA_DIR, f"content_plan_{date}_{account}.json")
    plan = load_json(plan_path)
    if plan is None:
        logger.error(f"No content plan found: {plan_path}")
        return 1

    limits = load_rate_limits(date)

    # Filter to approved posts
    posts = plan.get("posts", [])
    targets = []
    for p in posts:
        if p.get("status") != "approved":
            continue
        if slot is not None and p.get("slot") != slot:
            continue
        targets.append(p)

    if not targets:
        logger.warning(f"No approved posts found for {account}" +
                       (f" slot {slot}" if slot else ""))
        return 0

    logger.info(f"Publishing {len(targets)} post(s) for {account}" +
                (f" (slot {slot})" if slot else ""))

    if dry_run:
        write_client = None
        account_handle = f"@{account}_handle"
    else:
        try:
            write_client = XApiWriteClient(account)
            # Load handle from config for URL construction
            from x_api import load_account_credentials
            creds = load_account_credentials(account)
            account_handle = creds.get("handle", f"@{account}")
        except Exception as e:
            logger.error(f"Failed to initialize write client for {account}: {e}")
            return 1

    posted = 0
    failed = 0

    for p in targets:
        post_id = p["id"]

        if not check_rate_limit(limits, account, "posts"):
            logger.warning(f"Skipping {post_id} — post rate limit reached")
            break

        # Check for media
        media_path = find_media(post_id)
        media_ids = None

        if dry_run:
            logger.info(f"[DRY-RUN] Would post {post_id}: {p['text'][:80]}...")
            if media_path:
                logger.info(f"[DRY-RUN] Would upload media: {media_path}")
            p["status"] = "posted"
            p["tweet_id"] = "dry_run_" + post_id
            p["post_url"] = f"https://x.com/dry_run/status/dry_run_{post_id}"
            p["posted_at"] = now_iso()
            increment_rate_limit(limits, account, "posts")
            posted += 1
            continue

        try:
            # Upload media if found
            if media_path:
                logger.info(f"Uploading media for {post_id}: {media_path}")
                media_id = write_client.upload_media(media_path)
                media_ids = [media_id]
                logger.info(f"Media uploaded: media_id={media_id}")

            # Create tweet
            logger.info(f"Posting {post_id}...")
            result = write_client.create_post(text=p["text"], media_ids=media_ids)
            tweet_id = result["tweet_id"]
            url = post_url(account_handle, tweet_id)

            p["status"] = "posted"
            p["tweet_id"] = tweet_id
            p["post_url"] = url
            p["posted_at"] = now_iso()
            increment_rate_limit(limits, account, "posts")
            posted += 1

            logger.info(f"Posted {post_id} -> {url}")

            # Move media to posted
            if media_path:
                move_media_to_posted(media_path)

        except Exception as e:
            logger.error(f"Failed to post {post_id}: {e}")
            p["status"] = "failed"
            p["error"] = str(e)
            p["failed_at"] = now_iso()
            failed += 1

    # Save updated plan and rate limits
    save_json(plan_path, plan)
    save_rate_limits(date, limits)

    logger.info(f"Post results for {account}: {posted} posted, {failed} failed")
    return 1 if failed > 0 and posted == 0 else 0


# --- Outbound Subcommand ---

def _sqlite_log_outbound(date_iso: str, account: str, action_type: str,
                         target_handle: str, target_tweet_id: str,
                         success: bool, api_response_code: int | None = None):
    """Best-effort dual-write to SQLite. Logs warning on failure."""
    try:
        import db_manager
        db_manager.init()
        db_manager.insert_outbound_log(
            date=date_iso, account=account, action_type=action_type,
            target_handle=target_handle, target_tweet_id=target_tweet_id,
            success=1 if success else 0, api_response_code=api_response_code,
            timestamp=now_iso(),
        )
    except Exception as e:
        logger.warning(f"SQLite outbound log failed (continuing): {e}")


def run_outbound(account: str, dry_run: bool) -> int:
    """Run outbound engagement for an account. Returns 0 on success, 1 on error."""
    date = today_str()

    # Load strategy for outbound config
    strategy_path = os.path.join(DATA_DIR, f"strategy_{date}.json")
    strategy = load_json(strategy_path)
    if strategy is None:
        # Try current strategy
        strategy_path = os.path.join(DATA_DIR, "strategy_current.json")
        strategy = load_json(strategy_path)
    if strategy is None:
        logger.error("No strategy found for outbound engagement")
        return 1

    if account not in strategy:
        logger.error(f"No {account} section in strategy")
        return 1

    outbound_cfg = strategy[account].get("outbound_strategy", {})
    target_accounts = outbound_cfg.get("target_accounts", [])
    daily_likes = outbound_cfg.get("daily_likes", 0)
    daily_replies = outbound_cfg.get("daily_replies", 0)
    daily_follows = outbound_cfg.get("daily_follows", 0)
    reply_style = outbound_cfg.get("reply_style", "")

    # Load reply templates from content plan
    plan_path = os.path.join(DATA_DIR, f"content_plan_{date}_{account}.json")
    plan = load_json(plan_path)
    reply_templates = plan.get("reply_templates", []) if plan else []

    limits = load_rate_limits(date)

    # Initialize outbound log
    outbound_log_path = os.path.join(DATA_DIR, f"outbound_log_{date}.json")
    outbound_log = load_json(outbound_log_path) or {"date": f"{date[:4]}-{date[4:6]}-{date[6:8]}", "actions": []}

    if not target_accounts:
        logger.warning(f"No target accounts for {account} outbound")
        return 0

    logger.info(f"Outbound engagement for {account}: {len(target_accounts)} targets, "
                f"likes={daily_likes}, replies={daily_replies}, follows={daily_follows}")

    if dry_run:
        read_client = None
        write_client = None
    else:
        try:
            bearer = load_bearer_token()
            read_client = XApiClient(bearer)
            write_client = XApiWriteClient(account)
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
            return 1

    for target in target_accounts:
        handle = target.lstrip("@")
        logger.info(f"Processing target: @{handle}")

        # Resolve user
        if dry_run:
            target_user_id = f"dry_run_{handle}"
            recent_tweets = [{"tweet_id": f"dry_{i}", "text": f"Sample tweet {i}"} for i in range(3)]
        else:
            user_info = read_client.resolve_user_id(handle)
            if user_info is None:
                logger.warning(f"Could not resolve @{handle}, skipping")
                continue
            target_user_id = user_info["user_id"]

            # Fetch recent tweets
            recent_tweets = read_client.get_user_timeline(target_user_id, max_results=5)
            if not recent_tweets:
                logger.warning(f"No recent tweets from @{handle}")

        # Like recent tweets
        for tweet in recent_tweets:
            if not check_rate_limit(limits, account, "likes"):
                break
            tweet_id = tweet["tweet_id"]

            if dry_run:
                logger.info(f"[DRY-RUN] Would like tweet {tweet_id} from @{handle}")
            else:
                _delay_random()
                success = write_client.like_tweet(tweet_id)
                if success:
                    logger.info(f"Liked tweet {tweet_id} from @{handle}")
                else:
                    logger.warning(f"Failed to like tweet {tweet_id}")
                    continue

            increment_rate_limit(limits, account, "likes")
            outbound_log["actions"].append({
                "type": "like",
                "account": account,
                "target": f"@{handle}",
                "tweet_id": tweet_id,
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "like", f"@{handle}", tweet_id, True)

        # Reply to one tweet (if templates available and within limits)
        if recent_tweets and reply_templates and check_rate_limit(limits, account, "replies"):
            tweet = recent_tweets[0]
            reply_text = random.choice(reply_templates)

            if dry_run:
                logger.info(f"[DRY-RUN] Would reply to {tweet['tweet_id']}: {reply_text[:60]}...")
            else:
                _delay_random()
                result = write_client.reply_to_tweet(tweet["tweet_id"], reply_text)
                if result:
                    logger.info(f"Replied to {tweet['tweet_id']} from @{handle}")
                else:
                    logger.warning(f"Failed to reply to {tweet['tweet_id']}")

            increment_rate_limit(limits, account, "replies")
            outbound_log["actions"].append({
                "type": "reply",
                "account": account,
                "target": f"@{handle}",
                "tweet_id": tweet["tweet_id"],
                "reply_text": reply_text,
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "reply", f"@{handle}", tweet["tweet_id"], True)

        # Follow target (if within limits)
        if check_rate_limit(limits, account, "follows"):
            if dry_run:
                logger.info(f"[DRY-RUN] Would follow @{handle}")
            else:
                _delay_random()
                success = write_client.follow_user(target_user_id)
                if success:
                    logger.info(f"Followed @{handle}")
                else:
                    logger.warning(f"Failed to follow @{handle}")

            increment_rate_limit(limits, account, "follows")
            outbound_log["actions"].append({
                "type": "follow",
                "account": account,
                "target": f"@{handle}",
                "target_user_id": target_user_id,
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "follow", f"@{handle}", None, True)

    # Save rate limits and outbound log
    save_rate_limits(date, limits)
    save_json(outbound_log_path, outbound_log)

    acct_limits = limits.get(account, {})
    logger.info(f"Outbound complete for {account}. "
                f"Likes: {acct_limits.get('likes', {}).get('used', 0)}/{daily_likes}, "
                f"Replies: {acct_limits.get('replies', {}).get('used', 0)}/{daily_replies}, "
                f"Follows: {acct_limits.get('follows', {}).get('used', 0)}/{daily_follows}")
    return 0


def _delay_random():
    """Random delay between outbound operations."""
    delay = random.uniform(OUTBOUND_DELAY_MIN, OUTBOUND_DELAY_MAX)
    logger.info(f"Waiting {delay:.0f}s before next operation...")
    time.sleep(delay)


# --- Smart Outbound Subcommand ---

def run_smart_outbound(account: str, plan_path: str, dry_run: bool) -> int:
    """Execute a Claude-generated outbound engagement plan.

    Reads a pre-computed plan JSON and executes each action
    (like, reply, follow) with the same rate limiting and delays
    as the legacy outbound command.

    Args:
        account: "EN" or "JP"
        plan_path: Path to outbound_plan_{date}_{account}.json
        dry_run: If True, log actions without making API calls

    Returns:
        0 on success, 1 on error
    """
    date = today_str()

    # 1. Load the outbound plan
    plan = load_json(plan_path)
    if not plan:
        logger.error(f"Failed to load outbound plan: {plan_path}")
        return 1

    # 2. Load rate limits for today
    limits = load_rate_limits(date)

    # Initialize outbound log
    outbound_log_path = os.path.join(DATA_DIR, f"outbound_log_{date}.json")
    outbound_log = load_json(outbound_log_path) or {
        "date": f"{date[:4]}-{date[4:6]}-{date[6:8]}", "actions": []
    }

    if dry_run:
        write_client = None
    else:
        try:
            write_client = XApiWriteClient(account)
        except Exception as e:
            logger.error(f"Failed to initialize write client for {account}: {e}")
            return 1

    targets = plan.get("targets", [])
    logger.info(f"Smart outbound for {account}: {len(targets)} targets from plan")

    # 3. Execute each target's actions
    for target in targets:
        handle = target.get("handle", "unknown").lstrip("@")

        if target.get("skip"):
            logger.info(f"Skipping @{handle}: {target.get('skip_reason', 'no reason')}")
            continue

        # Use user_id from plan (already resolved by publisher_outbound_data.py)
        user_id = target.get("user_id")
        if not user_id:
            logger.warning(f"No user_id in plan for @{handle}, skipping")
            continue

        # Like selected tweets
        for tweet_id in target.get("tweets_to_like", []):
            if not check_rate_limit(limits, account, "likes"):
                logger.warning("Daily like limit reached")
                break

            if dry_run:
                logger.info(f"[DRY-RUN] Would like tweet {tweet_id} from @{handle}")
            else:
                _delay_random()
                success = write_client.like_tweet(tweet_id)
                if success:
                    logger.info(f"Liked tweet {tweet_id} from @{handle}")
                else:
                    logger.warning(f"Failed to like tweet {tweet_id}")
                    continue

            increment_rate_limit(limits, account, "likes")
            outbound_log["actions"].append({
                "type": "like",
                "account": account,
                "target": f"@{handle}",
                "tweet_id": tweet_id,
                "source": "smart_outbound",
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "like", f"@{handle}", tweet_id, True)

        # Reply to selected tweet
        reply_info = target.get("reply_to")
        if reply_info and check_rate_limit(limits, account, "replies"):
            reply_tweet_id = reply_info.get("tweet_id")
            reply_text = f"@{handle} {reply_info.get('reply_text', '')}"
            reply_success = True

            if dry_run:
                logger.info(f"[DRY-RUN] Would reply to {reply_tweet_id}: {reply_text[:80]}...")
            else:
                _delay_random()
                result = write_client.reply_to_tweet(reply_tweet_id, reply_text)
                if result:
                    logger.info(f"Replied to {reply_tweet_id} from @{handle}")
                else:
                    logger.warning(f"Failed to reply to {reply_tweet_id}")
                    reply_success = False
                    # Track for human escalation
                    if "failed_replies" not in outbound_log:
                        outbound_log["failed_replies"] = []
                    outbound_log["failed_replies"].append({
                        "target": f"@{handle}",
                        "tweet_id": reply_tweet_id,
                        "tweet_url": f"https://x.com/{handle}/status/{reply_tweet_id}",
                        "reply_text": reply_info.get("reply_text", ""),
                        "reason": "API 403 — reply restricted (account not mentioned/engaged by author)",
                    })

            increment_rate_limit(limits, account, "replies")
            outbound_log["actions"].append({
                "type": "reply",
                "account": account,
                "target": f"@{handle}",
                "tweet_id": reply_tweet_id,
                "reply_text": reply_text,
                "success": reply_success,
                "source": "smart_outbound",
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "reply", f"@{handle}", reply_tweet_id, True)

        # Follow
        if target.get("follow", False) and check_rate_limit(limits, account, "follows"):
            if dry_run:
                logger.info(f"[DRY-RUN] Would follow @{handle}")
            else:
                _delay_random()
                success = write_client.follow_user(user_id)
                if success:
                    logger.info(f"Followed @{handle}")
                else:
                    logger.warning(f"Failed to follow @{handle}")

            increment_rate_limit(limits, account, "follows")
            outbound_log["actions"].append({
                "type": "follow",
                "account": account,
                "target": f"@{handle}",
                "target_user_id": user_id,
                "source": "smart_outbound",
                "timestamp": now_iso(),
                "dry_run": dry_run,
            })
            date_iso = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            _sqlite_log_outbound(date_iso, account, "follow", f"@{handle}", None, True)

    # 4. Save rate limits and outbound log
    save_rate_limits(date, limits)
    save_json(outbound_log_path, outbound_log)

    acct_limits = limits.get(account, {})
    logger.info(f"Smart outbound complete for {account}. "
                f"Likes: {acct_limits.get('likes', {}).get('used', 0)}/30, "
                f"Replies: {acct_limits.get('replies', {}).get('used', 0)}/10, "
                f"Follows: {acct_limits.get('follows', {}).get('used', 0)}/5")
    return 0


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Publisher agent — post and outbound engagement")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without making API calls")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # post subcommand
    post_parser = subparsers.add_parser("post", help="Post approved content to X")
    post_parser.add_argument("--account", required=True, choices=["EN", "JP"], help="Account to post for")
    post_parser.add_argument("--slot", type=int, default=None, help="Post specific slot only")

    # outbound subcommand
    outbound_parser = subparsers.add_parser("outbound", help="Run outbound engagement")
    outbound_parser.add_argument("--account", required=True, choices=["EN", "JP"], help="Account to engage for")

    # smart-outbound subcommand
    smart_parser = subparsers.add_parser("smart-outbound", help="Execute Claude-generated outbound plan")
    smart_parser.add_argument("--account", required=True, choices=["EN", "JP"], help="Account to engage for")
    smart_parser.add_argument("--plan", required=True, help="Path to outbound plan JSON")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(2)

    if args.dry_run:
        logger.info("[DRY-RUN MODE] No API calls will be made")

    if args.command == "post":
        exit_code = run_post(args.account, args.slot, args.dry_run)
    elif args.command == "outbound":
        exit_code = run_outbound(args.account, args.dry_run)
    elif args.command == "smart-outbound":
        exit_code = run_smart_outbound(args.account, args.plan, args.dry_run)
    else:
        parser.print_help()
        sys.exit(2)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
