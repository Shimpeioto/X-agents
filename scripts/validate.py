"""Unified validation script for Scout, Strategist, Creator, Analyst, and cross-validation.

Usage:
    python3 scripts/validate.py scout data/scout_report_20260303.json
    python3 scripts/validate.py strategist data/strategy_20260303.json
    python3 scripts/validate.py cross data/scout_report_20260303.json data/strategy_20260303.json
    python3 scripts/validate.py creator data/content_plan_20260304_EN.json
    python3 scripts/validate.py creator_cross data/content_plan_20260304_EN.json data/strategy_20260304.json
    python3 scripts/validate.py analyst data/metrics_20260304_EN.json
    python3 scripts/validate.py analyst_metrics data/metrics_history.db

Exit codes: 0=pass, 1=fail, 2=usage error
"""

import json
import os
import re
import sqlite3
import sys


def validate_scout(report_path: str) -> tuple[bool, list[str]]:
    """Validate Scout output. Returns (passed, list_of_issues)."""
    issues = []
    total_checks = 0

    # Check 1: File exists and is non-empty
    total_checks += 1
    try:
        with open(report_path) as f:
            content = f.read()
        if not content.strip():
            issues.append("file_empty: Scout report file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {report_path} does not exist")
        return False, issues

    # Check 2: Valid JSON
    total_checks += 1
    try:
        report = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 3: Has competitors array
    total_checks += 1
    if "competitors" not in report or not isinstance(report["competitors"], list):
        issues.append("missing_competitors: 'competitors' array not found in report")

    # Check 4: competitors_fetched >= 1
    total_checks += 1
    competitors = report.get("competitors", [])
    if len(competitors) < 1:
        issues.append(f"no_competitors: competitors array has {len(competitors)} entries, expected >= 1")

    # Check 5: Each competitor has required fields
    total_checks += 1
    required_fields = ["handle", "user_id", "status", "market"]
    for i, comp in enumerate(competitors):
        for field in required_fields:
            if field not in comp:
                issues.append(f"missing_field: competitor[{i}] ({comp.get('handle', '?')}) missing '{field}'")
                break  # one issue per competitor is enough

    # Check 6: market_comparison present
    total_checks += 1
    if "market_comparison" not in report or not isinstance(report.get("market_comparison"), dict):
        issues.append("missing_market_comparison: 'market_comparison' section not found")

    # Check 7: hashtag_frequency present
    total_checks += 1
    if "hashtag_frequency" not in report or not isinstance(report.get("hashtag_frequency"), dict):
        issues.append("missing_hashtag_frequency: 'hashtag_frequency' section not found")

    # Check 8 (bonus): engagement_rate >= 0 for all competitors
    total_checks += 1
    for comp in competitors:
        eng_rate = comp.get("avg_engagement_rate", 0)
        if isinstance(eng_rate, (int, float)) and eng_rate < 0:
            issues.append(f"negative_engagement: {comp.get('handle', '?')} has engagement_rate {eng_rate}")

    passed = len(issues) == 0
    return passed, issues


def validate_strategist(strategy_path: str) -> tuple[bool, list[str]]:
    """Validate Strategist output. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is non-empty
    try:
        with open(strategy_path) as f:
            content = f.read()
        if not content.strip():
            issues.append("file_empty: Strategy file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {strategy_path} does not exist")
        return False, issues

    # Check 2: Valid JSON (strip code fences if present)
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        strategy = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 3: Both EN and JP top-level keys
    for account in ["EN", "JP"]:
        if account not in strategy:
            issues.append(f"missing_account: '{account}' top-level key not found")

    # If either account is missing, remaining checks can't proceed
    if any("missing_account" in i for i in issues):
        return False, issues

    for account in ["EN", "JP"]:
        section = strategy[account]

        # Check 4: posting_schedule has 3-5 slots
        schedule = section.get("posting_schedule", [])
        if not isinstance(schedule, list) or len(schedule) < 3 or len(schedule) > 5:
            issues.append(f"posting_schedule_slots: {account} has {len(schedule) if isinstance(schedule, list) else 0} slots, expected 3-5")

        # Check 5: content_mix sums to 100
        content_mix = section.get("content_mix", {})
        if isinstance(content_mix, dict):
            total = sum(v for v in content_mix.values() if isinstance(v, (int, float)))
            if total != 100:
                issues.append(f"content_mix_sum: {account} content_mix sums to {total}, expected 100")
        else:
            issues.append(f"content_mix_missing: {account} content_mix is not a dict")

        # Check 6: hashtag_strategy present with always_use
        hs = section.get("hashtag_strategy", {})
        if not isinstance(hs, dict):
            issues.append(f"hashtag_strategy_missing: {account} hashtag_strategy not found")
        else:
            always_use = hs.get("always_use", [])
            if not isinstance(always_use, list) or len(always_use) < 1:
                issues.append(f"always_use_empty: {account} hashtag_strategy.always_use has no entries")

        # Check 7: outbound_strategy within limits
        os_section = section.get("outbound_strategy", {})
        if isinstance(os_section, dict):
            likes = os_section.get("daily_likes", 0)
            replies = os_section.get("daily_replies", 0)
            follows = os_section.get("daily_follows", 0)
            if isinstance(likes, (int, float)) and likes > 30:
                issues.append(f"outbound_likes: {account} daily_likes={likes}, max is 30")
            if isinstance(replies, (int, float)) and replies > 10:
                issues.append(f"outbound_replies: {account} daily_replies={replies}, max is 10")
            if isinstance(follows, (int, float)) and follows > 5:
                issues.append(f"outbound_follows: {account} daily_follows={follows}, max is 5")
        else:
            issues.append(f"outbound_missing: {account} outbound_strategy not found")

        # Check 8: ab_test present
        if "ab_test" not in section or not isinstance(section.get("ab_test"), dict):
            issues.append(f"ab_test_missing: {account} ab_test section not found")

        # Check 9: key_insights >= 3
        insights = section.get("key_insights", [])
        if not isinstance(insights, list) or len(insights) < 3:
            issues.append(f"key_insights_count: {account} has {len(insights) if isinstance(insights, list) else 0} insights, expected >= 3")

    passed = len(issues) == 0
    return passed, issues


def cross_validate(scout_path: str, strategy_path: str) -> tuple[bool, list[str]]:
    """Cross-validate Scout and Strategist outputs. Returns (passed, list_of_issues)."""
    issues = []

    # Load both files
    try:
        with open(scout_path) as f:
            report = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"scout_load_error: {e}")
        return False, issues

    try:
        with open(strategy_path) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        strategy = json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"strategy_load_error: {e}")
        return False, issues

    # Check 1: Markets in strategy exist in scout data
    scout_markets = set()
    for comp in report.get("competitors", []):
        market = comp.get("market", "")
        if market == "both":
            scout_markets.add("EN")
            scout_markets.add("JP")
        elif market:
            scout_markets.add(market)

    for account in ["EN", "JP"]:
        if account in strategy and account not in scout_markets:
            issues.append(f"market_mismatch: Strategy has {account} section but no {account} competitors in Scout data")

    # Check 2: Strategist's always_use hashtags appear in Scout's hashtag_frequency
    scout_hashtags = set(report.get("hashtag_frequency", {}).keys())
    for account in ["EN", "JP"]:
        if account not in strategy:
            continue
        hs = strategy[account].get("hashtag_strategy", {})
        always_use = hs.get("always_use", [])
        for tag in always_use:
            if tag not in scout_hashtags:
                # Warn but don't fail — Strategist may recommend new hashtags
                issues.append(f"hashtag_not_in_scout: {account} always_use '{tag}' not found in Scout's hashtag_frequency (warning)")

    # Check 3: Outbound target accounts exist in competitor list
    competitor_handles = set()
    for comp in report.get("competitors", []):
        h = comp.get("handle", "").lstrip("@").lower()
        if h:
            competitor_handles.add(h)

    for account in ["EN", "JP"]:
        if account not in strategy:
            continue
        os_section = strategy[account].get("outbound_strategy", {})
        targets = os_section.get("target_accounts", [])
        for target in targets:
            clean = target.lstrip("@").lower()
            if clean and clean not in competitor_handles:
                issues.append(f"target_not_competitor: {account} target '{target}' not in competitor list (warning)")

    # Check 4: Posting schedule times not all identical
    for account in ["EN", "JP"]:
        if account not in strategy:
            continue
        schedule = strategy[account].get("posting_schedule", [])
        times = [slot.get("time", "") for slot in schedule if isinstance(slot, dict)]
        if len(times) >= 2 and len(set(times)) == 1:
            issues.append(f"identical_times: {account} all posting_schedule times are identical ({times[0]})")

    passed = len(issues) == 0
    return passed, issues


def validate_creator(plan_path: str) -> tuple[bool, list[str]]:
    """Validate Creator content plan output. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is non-empty
    try:
        with open(plan_path) as f:
            content = f.read()
        if not content.strip():
            issues.append("file_empty: Content plan file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {plan_path} does not exist")
        return False, issues

    # Check 2: Valid JSON (strip code fences if present)
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 3: Required top-level fields
    required_top = ["date", "account", "posts", "reply_templates"]
    for field in required_top:
        if field not in plan:
            issues.append(f"missing_field: top-level '{field}' not found")

    if any("missing_field" in i for i in issues):
        return False, issues

    account = plan["account"]

    # Check 4: account is EN or JP
    if account not in ("EN", "JP"):
        issues.append(f"invalid_account: account is '{account}', expected 'EN' or 'JP'")

    # Check 5: posts is a non-empty array
    posts = plan.get("posts", [])
    if not isinstance(posts, list) or len(posts) < 1:
        issues.append(f"no_posts: posts array has {len(posts) if isinstance(posts, list) else 0} entries")

    # Check 6: Each post has required fields
    post_required = ["id", "slot", "scheduled_time", "category", "priority", "status", "text", "hashtags", "image_prompt"]
    for i, post in enumerate(posts):
        missing = [f for f in post_required if f not in post]
        if missing:
            issues.append(f"post_missing_fields: post[{i}] missing {missing}")

    # Check 7: Post IDs follow {account}_{YYYYMMDD}_{slot} convention
    id_pattern = re.compile(r"^(EN|JP)_\d{8}_\d{2}$")
    for i, post in enumerate(posts):
        pid = post.get("id", "")
        if not id_pattern.match(pid):
            issues.append(f"invalid_post_id: post[{i}] id '{pid}' doesn't match {{account}}_YYYYMMDD_{{slot}} format")
        elif not pid.startswith(account + "_"):
            issues.append(f"post_id_account_mismatch: post[{i}] id '{pid}' doesn't start with '{account}_'")

    # Check 8: All statuses are "draft"
    for i, post in enumerate(posts):
        if post.get("status") != "draft":
            issues.append(f"non_draft_status: post[{i}] status is '{post.get('status')}', expected 'draft'")

    # Check 9: No post text starts with @
    for i, post in enumerate(posts):
        text = post.get("text", "")
        if isinstance(text, str) and text.lstrip().startswith("@"):
            issues.append(f"text_starts_with_at: post[{i}] text starts with '@' (hidden from feeds)")

    # Check 10: Image prompts have tool + prompt + aspect_ratio
    for i, post in enumerate(posts):
        ip = post.get("image_prompt", {})
        if not isinstance(ip, dict):
            issues.append(f"invalid_image_prompt: post[{i}] image_prompt is not a dict")
        else:
            ip_required = ["tool", "prompt", "aspect_ratio"]
            ip_missing = [f for f in ip_required if f not in ip]
            if ip_missing:
                issues.append(f"image_prompt_missing: post[{i}] image_prompt missing {ip_missing}")

    # Check 11: 5-10 reply templates, no duplicates
    templates = plan.get("reply_templates", [])
    if not isinstance(templates, list):
        issues.append("reply_templates_not_array: reply_templates is not an array")
    else:
        if len(templates) < 5 or len(templates) > 10:
            issues.append(f"reply_template_count: {len(templates)} templates, expected 5-10")
        if len(set(templates)) != len(templates):
            issues.append("reply_template_duplicates: duplicate reply templates found")

    # Check 12: No reply template starts with @
    if isinstance(templates, list):
        for i, tmpl in enumerate(templates):
            if isinstance(tmpl, str) and tmpl.lstrip().startswith("@"):
                issues.append(f"reply_starts_with_at: reply_template[{i}] starts with '@'")

    passed = len(issues) == 0
    return passed, issues


def creator_cross_validate(plan_path: str, strategy_path: str) -> tuple[bool, list[str]]:
    """Cross-validate Creator plan against Strategy. Returns (passed, list_of_issues)."""
    issues = []

    # Load content plan
    try:
        with open(plan_path) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        plan = json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"plan_load_error: {e}")
        return False, issues

    # Load strategy
    try:
        with open(strategy_path) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        strategy = json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        issues.append(f"strategy_load_error: {e}")
        return False, issues

    account = plan.get("account", "")
    if account not in strategy:
        issues.append(f"account_not_in_strategy: '{account}' section not found in strategy")
        return False, issues

    strat_section = strategy[account]

    # Check 1: Post count matches strategy's posting_schedule slot count
    schedule = strat_section.get("posting_schedule", [])
    posts = plan.get("posts", [])
    if len(posts) != len(schedule):
        issues.append(f"post_count_mismatch: plan has {len(posts)} posts, strategy has {len(schedule)} slots")

    # Check 2: Post categories match strategy schedule categories
    for i, slot in enumerate(schedule):
        expected_cat = slot.get("category", "")
        if i < len(posts):
            actual_cat = posts[i].get("category", "")
            if expected_cat and actual_cat and expected_cat.lower() != actual_cat.lower():
                issues.append(f"category_mismatch: slot {i+1} expected '{expected_cat}', got '{actual_cat}'")

    # Check 3: always_use hashtags appear in posts
    hs = strat_section.get("hashtag_strategy", {})
    always_use = hs.get("always_use", [])
    for i, post in enumerate(posts):
        post_tags = [t.lower() for t in post.get("hashtags", [])]
        for tag in always_use:
            if tag.lower() not in post_tags:
                issues.append(f"missing_always_use_hashtag: post[{i}] missing always_use hashtag '{tag}'")

    passed = len(issues) == 0
    return passed, issues


def validate_publisher(plan_path: str) -> tuple[bool, list[str]]:
    """Validate Publisher output (content plan after posting). Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is valid JSON
    try:
        with open(plan_path) as f:
            content = f.read().strip()
        if not content:
            issues.append("file_empty: Content plan file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {plan_path} does not exist")
        return False, issues

    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 2: At least 1 post has status "posted"
    posts = plan.get("posts", [])
    posted_count = sum(1 for p in posts if p.get("status") == "posted")
    if posted_count < 1:
        issues.append(f"no_posted: {posted_count} posts have status 'posted', expected >= 1")

    # Check 3: All "posted" posts have tweet_id, post_url, posted_at
    for i, p in enumerate(posts):
        if p.get("status") != "posted":
            continue
        for field in ["tweet_id", "post_url", "posted_at"]:
            if not p.get(field):
                issues.append(f"missing_posted_field: post[{i}] ({p.get('id', '?')}) status is 'posted' but missing '{field}'")

    # Check 4: No post text starts with @
    for i, p in enumerate(posts):
        text = p.get("text", "")
        if isinstance(text, str) and text.lstrip().startswith("@"):
            issues.append(f"text_starts_with_at: post[{i}] text starts with '@'")

    # Check 5: No duplicate tweet_ids among posted posts
    tweet_ids = [p.get("tweet_id") for p in posts if p.get("status") == "posted" and p.get("tweet_id")]
    if len(tweet_ids) != len(set(tweet_ids)):
        dupes = [tid for tid in tweet_ids if tweet_ids.count(tid) > 1]
        issues.append(f"duplicate_tweet_ids: duplicate tweet_id(s) found: {set(dupes)}")

    # Check 6: post_url format (basic check)
    for i, p in enumerate(posts):
        if p.get("status") != "posted":
            continue
        url = p.get("post_url", "")
        if url and not url.startswith("https://x.com/"):
            issues.append(f"invalid_post_url: post[{i}] post_url doesn't start with 'https://x.com/'")

    # Check 7: No "posted" post has a "failed" status (sanity)
    for i, p in enumerate(posts):
        if p.get("status") == "posted" and p.get("error"):
            issues.append(f"posted_with_error: post[{i}] has status 'posted' but also has error field")

    # Check 8: account field is present and valid
    account = plan.get("account")
    if account not in ("EN", "JP"):
        issues.append(f"invalid_account: account is '{account}', expected 'EN' or 'JP'")

    passed = len(issues) == 0
    return passed, issues


def validate_publisher_rate_limits(limits_path: str) -> tuple[bool, list[str]]:
    """Validate Publisher rate limits file. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is valid JSON
    try:
        with open(limits_path) as f:
            content = f.read().strip()
        if not content:
            issues.append("file_empty: Rate limits file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {limits_path} does not exist")
        return False, issues

    try:
        limits = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 2: date field present
    if "date" not in limits:
        issues.append("missing_date: 'date' field not found")

    # Check 3: EN and JP sections present
    for account in ["EN", "JP"]:
        if account not in limits:
            issues.append(f"missing_account: '{account}' section not found")

    if any("missing_account" in i for i in issues):
        return False, issues

    # Check 4: All counters have used/limit fields
    expected_actions = ["posts", "likes", "replies", "follows"]
    for account in ["EN", "JP"]:
        section = limits[account]
        for action in expected_actions:
            if action not in section:
                issues.append(f"missing_action: {account}.{action} not found")
                continue
            entry = section[action]
            if "used" not in entry:
                issues.append(f"missing_used: {account}.{action} missing 'used'")
            if "limit" not in entry:
                issues.append(f"missing_limit: {account}.{action} missing 'limit'")

    # Check 5: No used > limit
    for account in ["EN", "JP"]:
        section = limits.get(account, {})
        for action in expected_actions:
            entry = section.get(action, {})
            used = entry.get("used", 0)
            limit = entry.get("limit", 0)
            if isinstance(used, (int, float)) and isinstance(limit, (int, float)) and used > limit:
                issues.append(f"limit_exceeded: {account}.{action} used={used} > limit={limit}")

    passed = len(issues) == 0
    return passed, issues


def validate_analyst(summary_path: str) -> tuple[bool, list[str]]:
    """Validate Analyst summary JSON output. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: File exists and is non-empty
    try:
        with open(summary_path) as f:
            content = f.read()
        if not content.strip():
            issues.append("file_empty: Analyst summary file is empty")
            return False, issues
    except FileNotFoundError:
        issues.append(f"file_not_found: {summary_path} does not exist")
        return False, issues

    # Check 2: Valid JSON
    try:
        summary = json.loads(content)
    except json.JSONDecodeError as e:
        issues.append(f"invalid_json: {e}")
        return False, issues

    # Check 3: Required top-level fields
    required = ["account", "date", "generated_at", "post_count"]
    for field in required:
        if field not in summary:
            issues.append(f"missing_field: top-level '{field}' not found")

    # Check 4: account is EN or JP
    account = summary.get("account", "")
    if account not in ("EN", "JP"):
        issues.append(f"invalid_account: account is '{account}', expected 'EN' or 'JP'")

    # Check 5: date is valid ISO date format
    date = summary.get("date", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date)):
        issues.append(f"invalid_date: date '{date}' doesn't match YYYY-MM-DD format")

    # Check 6: post_metrics is an array
    post_metrics = summary.get("post_metrics", None)
    if post_metrics is not None and not isinstance(post_metrics, list):
        issues.append("post_metrics_not_array: post_metrics is not an array")

    # Check 7: totals section present with expected fields
    totals = summary.get("totals", None)
    if totals is None:
        issues.append("missing_totals: 'totals' section not found")
    elif isinstance(totals, dict):
        for field in ["likes", "retweets", "replies"]:
            if field not in totals:
                issues.append(f"missing_total_field: totals.{field} not found")

    # Check 8: post_count matches post_metrics length
    if isinstance(post_metrics, list):
        declared = summary.get("post_count", -1)
        actual = len(post_metrics)
        if declared != actual:
            issues.append(f"post_count_mismatch: post_count={declared} but post_metrics has {actual} entries")

    passed = len(issues) == 0
    return passed, issues


def validate_analyst_metrics(db_path: str) -> tuple[bool, list[str]]:
    """Validate Analyst SQLite database integrity. Returns (passed, list_of_issues)."""
    issues = []

    # Check 1: Database file exists
    if not os.path.exists(db_path):
        issues.append(f"db_not_found: {db_path} does not exist")
        return False, issues

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
    except sqlite3.Error as e:
        issues.append(f"db_open_error: {e}")
        return False, issues

    # Check 2: Required tables exist
    tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for table in ["post_metrics", "account_metrics", "outbound_log", "error_log"]:
        if table not in tables:
            issues.append(f"missing_table: '{table}' table not found")

    if any("missing_table" in i for i in issues):
        conn.close()
        return False, issues

    # Check 3: post_metrics has expected columns
    pm_cols = [row[1] for row in c.execute("PRAGMA table_info(post_metrics)").fetchall()]
    for col in ["post_id", "tweet_id", "account", "measured_at", "likes", "retweets", "source"]:
        if col not in pm_cols:
            issues.append(f"missing_column: post_metrics.{col} not found")

    # Check 4: account_metrics has expected columns
    am_cols = [row[1] for row in c.execute("PRAGMA table_info(account_metrics)").fetchall()]
    for col in ["account", "date", "followers", "followers_change"]:
        if col not in am_cols:
            issues.append(f"missing_column: account_metrics.{col} not found")

    # Check 5: outbound_log has timestamp column (migration check)
    ol_cols = [row[1] for row in c.execute("PRAGMA table_info(outbound_log)").fetchall()]
    if "timestamp" not in ol_cols:
        issues.append("missing_column: outbound_log.timestamp not found (migration needed)")

    # Check 6: No negative metric values in post_metrics
    neg_rows = c.execute(
        """SELECT post_id, likes, retweets, replies, quotes, bookmarks
           FROM post_metrics
           WHERE likes < 0 OR retweets < 0 OR replies < 0 OR quotes < 0 OR bookmarks < 0"""
    ).fetchall()
    if neg_rows:
        issues.append(f"negative_metrics: {len(neg_rows)} rows have negative metric values")

    conn.close()

    passed = len(issues) == 0
    return passed, issues


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/validate.py {scout|strategist|cross|creator|creator_cross|publisher|publisher_rate_limits|analyst|analyst_metrics} <file1> [<file2>]", file=sys.stderr)
        sys.exit(2)

    mode = sys.argv[1]

    if mode == "scout":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py scout <scout_report.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_scout(sys.argv[2])

    elif mode == "strategist":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py strategist <strategy.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_strategist(sys.argv[2])

    elif mode == "cross":
        if len(sys.argv) < 4:
            print("Usage: python3 scripts/validate.py cross <scout_report.json> <strategy.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = cross_validate(sys.argv[2], sys.argv[3])

    elif mode == "creator":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py creator <content_plan.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_creator(sys.argv[2])

    elif mode == "creator_cross":
        if len(sys.argv) < 4:
            print("Usage: python3 scripts/validate.py creator_cross <content_plan.json> <strategy.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = creator_cross_validate(sys.argv[2], sys.argv[3])

    elif mode == "publisher":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py publisher <content_plan.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_publisher(sys.argv[2])

    elif mode == "publisher_rate_limits":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py publisher_rate_limits <rate_limits.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_publisher_rate_limits(sys.argv[2])

    elif mode == "analyst":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py analyst <metrics_summary.json>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_analyst(sys.argv[2])

    elif mode == "analyst_metrics":
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/validate.py analyst_metrics <metrics_history.db>", file=sys.stderr)
            sys.exit(2)
        passed, issues = validate_analyst_metrics(sys.argv[2])

    else:
        print(f"Unknown mode: {mode}. Use 'scout', 'strategist', 'cross', 'creator', 'creator_cross', 'publisher', 'publisher_rate_limits', 'analyst', or 'analyst_metrics'.", file=sys.stderr)
        sys.exit(2)

    # Determine total checks from mode
    check_counts = {"scout": 8, "strategist": 14, "cross": 4, "creator": 12, "creator_cross": 3, "publisher": 8, "publisher_rate_limits": 5, "analyst": 8, "analyst_metrics": 6}
    total_checks = check_counts.get(mode, len(issues) + 1)

    if passed:
        print(f"PASS: All {total_checks} checks passed.")
        sys.exit(0)
    else:
        print(f"FAIL: {len(issues)} of {total_checks} checks failed.")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
