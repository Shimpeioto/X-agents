"""Unified validation script for Scout, Strategist, Creator, and cross-validation.

Usage:
    python3 scripts/validate.py scout data/scout_report_20260303.json
    python3 scripts/validate.py strategist data/strategy_20260303.json
    python3 scripts/validate.py cross data/scout_report_20260303.json data/strategy_20260303.json
    python3 scripts/validate.py creator data/content_plan_20260304_EN.json
    python3 scripts/validate.py creator_cross data/content_plan_20260304_EN.json data/strategy_20260304.json

Exit codes: 0=pass, 1=fail, 2=usage error
"""

import json
import re
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


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/validate.py {scout|strategist|cross} <file1> [<file2>]", file=sys.stderr)
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

    else:
        print(f"Unknown mode: {mode}. Use 'scout', 'strategist', 'cross', 'creator', or 'creator_cross'.", file=sys.stderr)
        sys.exit(2)

    # Determine total checks from mode
    check_counts = {"scout": 8, "strategist": 14, "cross": 4, "creator": 12, "creator_cross": 3}
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
