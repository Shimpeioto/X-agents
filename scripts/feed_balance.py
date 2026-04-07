"""Feed balance + reference pool management for v5 Meruru agent.

Pure Python module — no LLM calls. Three primary functions:
  - compute_feed_balance(account, days=14) → dict
  - get_unused_references(account, count=12) → list
  - mark_references_used(plan) → None

Data sources:
  - data/content/content_plan_*.json (recent plans for balance computation)
  - data/content/reference_catalog.json (full reference pool)
  - data/content/reference_usage.json (usage tracking)

CLI usage (for testing):
  python3 scripts/feed_balance.py balance EN
  python3 scripts/feed_balance.py unused EN [count]
  python3 scripts/feed_balance.py mark <plan_path>
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(PROJECT, "data", "content")
REFERENCE_CATALOG = os.path.join(CONTENT_DIR, "reference_catalog.json")
REFERENCE_USAGE = os.path.join(CONTENT_DIR, "reference_usage.json")

JST = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [FEED_BALANCE] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Categorization buckets
# ---------------------------------------------------------------------------

# Each bucket maps category → list of substrings to match (lowercase)
FRAMING_BUCKETS = {
    "close-up": ["close-up", "close up", "closeup", "tight", "head and shoulders", "portrait close"],
    "medium": ["medium", "three-quarter", "three quarter", "waist-up", "waist up", "half body"],
    "full-body": ["full-body", "full body", "wide", "full shot", "full length"],
}

POSE_BUCKETS = {
    "standing": ["standing", "stand", "upright", "leaning"],
    "seated": ["seated", "sitting", "sit ", "sits"],
    "reclined": ["reclined", "lying", "lounging", "reclining", "laying"],
    "prone": ["prone", "on stomach", "face down"],
    "kneeling": ["kneeling", "kneel"],
    "squatting": ["squat", "crouch"],
}

ANGLE_BUCKETS = {
    "eye-level": ["eye-level", "eye level", "straight on"],
    "low-angle": ["low-angle", "low angle", "from below", "upward"],
    "high-angle": ["high-angle", "high angle", "from above", "overhead", "downward"],
}

SCENE_BUCKETS = {
    "bedroom": ["bedroom", "bed ", "on bed", "headboard"],
    "bathroom": ["bathroom", "powder room", "shower", "marble counter", "tub"],
    "kitchen": ["kitchen", "counter", "fridge", "stove"],
    "living-room": ["living room", "sofa", "couch", "armchair"],
    "studio": ["studio", "backdrop", "circular", "spotlight", "plain wall"],
    "hallway": ["hallway", "corridor"],
    "outdoor": ["outdoor", "street", "park", "rooftop", "balcony", "garden"],
    "beach-pool": ["beach", "pool", "shoreline", "sand"],
    "gym": ["gym", "weights", "fitness", "yoga"],
    "cafe": ["cafe", "coffee shop", "restaurant"],
    "car": ["car interior", "passenger seat", "driver seat", "backseat"],
    "industrial": ["industrial", "warehouse", "garage door", "concrete"],
    "window": ["window", "frosted glass", "near window"],
}

OUTFIT_COVERAGE_BUCKETS = {
    "minimal": ["lingerie", "bikini", "swimwear", "bodysuit", "monokini", "lace bra", "thong", "harness"],
    "casual": ["crop top", "tank", "tee", "t-shirt", "loungewear", "boy shorts", "shorts"],
    "styled": ["dress", "skirt", "blouse", "knit top", "cosplay", "uniform", "pvc"],
    "outerwear": ["jacket", "coat", "shrug", "bolero", "cardigan"],
}

COLOR_BUCKETS = {
    "dark": ["black", "charcoal", "dark", "deep red", "navy"],
    "warm-neutral": ["cream", "ivory", "beige", "marble", "warm white", "tan"],
    "bright": ["white", "pastel", "powder blue", "light pink", "bright"],
    "accent-red": ["red", "crimson", "scarlet", "cherry"],
    "accent-other": ["blue", "green", "yellow", "purple", "orange"],
}

MOOD_BUCKETS = {
    "sexy-confident": ["sexy", "confident", "sultry", "alluring", "magnetic"],
    "cute-soft": ["cute", "soft", "playful", "cozy", "tender", "sweet"],
    "moody-intimate": ["moody", "intimate", "private", "nocturnal", "after-hours", "still"],
    "bright-airy": ["bright", "airy", "fresh", "morning", "daylight", "clean"],
}

LIGHTING_BUCKETS = {
    "warm-glow": ["warm", "ambient", "lamp", "recessed", "golden", "ivory"],
    "hard-dramatic": ["hard", "dramatic", "spotlight", "harsh", "single source", "deep shadow"],
    "natural-window": ["natural", "window", "daylight", "diffused", "soft daylight"],
    "studio-flash": ["flash", "strobe", "studio light"],
}


def _categorize(value: str, buckets: dict[str, list[str]]) -> str | None:
    """Match a free-text value against bucket keywords, return bucket name or None."""
    if not value:
        return None
    value_lower = value.lower()
    for bucket, keywords in buckets.items():
        for kw in keywords:
            if kw in value_lower:
                return bucket
    return None


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s: %s", path, e)
        return None


def _save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _today_str() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def _list_recent_plans(account: str, days: int) -> list[str]:
    """Return paths to content plans for the given account from the last N days."""
    pattern = os.path.join(CONTENT_DIR, f"content_plan_*_{account}.json")
    plans = sorted(glob.glob(pattern))
    if days <= 0:
        return plans
    cutoff = datetime.now(JST) - timedelta(days=days)
    recent = []
    for path in plans:
        # extract date from filename: content_plan_YYYYMMDD_EN.json
        basename = os.path.basename(path)
        try:
            date_str = basename.split("_")[2]
            plan_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=JST)
            if plan_date >= cutoff:
                recent.append(path)
        except (IndexError, ValueError):
            continue
    return recent


# ---------------------------------------------------------------------------
# 1. compute_feed_balance
# ---------------------------------------------------------------------------

def compute_feed_balance(account: str = "EN", days: int = 14) -> dict:
    """Analyze recent feed across multiple dimensions.

    Returns a dict with structured counts and a human-readable summary.
    Note: Only counts system-generated content plans, not operator's manual posts.
    """
    plans_paths = _list_recent_plans(account, days)
    posts: list[dict] = []
    for path in plans_paths:
        plan = _load_json(path)
        if not plan or not isinstance(plan.get("posts"), list):
            continue
        posts.extend(plan["posts"])

    counters = {
        "framings": Counter(),
        "poses": Counter(),
        "angles": Counter(),
        "scenes": Counter(),
        "outfit_coverage": Counter(),
        "colors": Counter(),
        "moods": Counter(),
        "lighting": Counter(),
    }

    for post in posts:
        ip = post.get("image_prompt") or {}
        if not isinstance(ip, dict):
            continue

        # Framing — from camera.framing
        framing_val = (ip.get("camera") or {}).get("framing", "")
        cat = _categorize(framing_val, FRAMING_BUCKETS)
        if cat:
            counters["framings"][cat] += 1

        # Pose — from pose.position
        pose_val = (ip.get("pose") or {}).get("position", "")
        cat = _categorize(pose_val, POSE_BUCKETS)
        if cat:
            counters["poses"][cat] += 1

        # Angle — from camera.angle
        angle_val = (ip.get("camera") or {}).get("angle", "")
        cat = _categorize(angle_val, ANGLE_BUCKETS)
        if cat:
            counters["angles"][cat] += 1

        # Scene — from scene.location
        scene_val = (ip.get("scene") or {}).get("location", "")
        cat = _categorize(scene_val, SCENE_BUCKETS)
        if cat:
            counters["scenes"][cat] += 1

        # Outfit coverage — from outfit.top.type
        outfit_top = (ip.get("outfit") or {}).get("top", {})
        outfit_val = outfit_top.get("type", "") if isinstance(outfit_top, dict) else str(outfit_top)
        cat = _categorize(outfit_val, OUTFIT_COVERAGE_BUCKETS)
        if cat:
            counters["outfit_coverage"][cat] += 1

        # Color palette — from mood.color_palette
        color_val = (ip.get("mood") or {}).get("color_palette", "")
        cat = _categorize(color_val, COLOR_BUCKETS)
        if cat:
            counters["colors"][cat] += 1

        # Mood — from mood.energy or mood.aesthetic
        mood_val = " ".join([
            str((ip.get("mood") or {}).get("energy", "")),
            str((ip.get("mood") or {}).get("aesthetic", "")),
        ])
        cat = _categorize(mood_val, MOOD_BUCKETS)
        if cat:
            counters["moods"][cat] += 1

        # Lighting — from lighting.type
        lighting_val = (ip.get("lighting") or {}).get("type", "")
        cat = _categorize(lighting_val, LIGHTING_BUCKETS)
        if cat:
            counters["lighting"][cat] += 1

    summary_lines = _build_summary(counters, len(posts), days, account)

    return {
        "account": account,
        "days_window": days,
        "plans_analyzed": len(plans_paths),
        "posts_analyzed": len(posts),
        "counts": {k: dict(v) for k, v in counters.items()},
        "summary": "\n".join(summary_lines),
        "note": "Approximate — only counts system-generated plans, not operator's manual posts.",
    }


def _build_summary(counters: dict[str, Counter], total_posts: int, days: int, account: str) -> list[str]:
    """Build a human-readable summary of what's over/under-represented."""
    lines = [
        f"Feed balance for {account} (last {days} days, {total_posts} posts analyzed):",
        "",
    ]

    if total_posts == 0:
        lines.append("No posts found in window. Feed is empty or plans are missing.")
        return lines

    def _fmt_dimension(name: str, counter: Counter, all_buckets: dict) -> str:
        if not counter:
            return f"  {name}: no data extracted"
        total = sum(counter.values())
        parts = []
        for bucket in all_buckets:
            count = counter.get(bucket, 0)
            pct = (count / total * 100) if total else 0
            parts.append(f"{bucket}={count} ({pct:.0f}%)")
        return f"  {name}: " + ", ".join(parts)

    lines.append(_fmt_dimension("framings", counters["framings"], FRAMING_BUCKETS))
    lines.append(_fmt_dimension("poses", counters["poses"], POSE_BUCKETS))
    lines.append(_fmt_dimension("angles", counters["angles"], ANGLE_BUCKETS))
    lines.append(_fmt_dimension("scenes", counters["scenes"], SCENE_BUCKETS))
    lines.append(_fmt_dimension("outfit_coverage", counters["outfit_coverage"], OUTFIT_COVERAGE_BUCKETS))
    lines.append(_fmt_dimension("colors", counters["colors"], COLOR_BUCKETS))
    lines.append(_fmt_dimension("moods", counters["moods"], MOOD_BUCKETS))
    lines.append(_fmt_dimension("lighting", counters["lighting"], LIGHTING_BUCKETS))

    # Identify gaps (buckets with 0 across known dimensions)
    lines.append("")
    lines.append("What's missing or under-represented:")
    gaps = []
    dim_pairs = [
        ("scenes", SCENE_BUCKETS, "scene"),
        ("poses", POSE_BUCKETS, "pose"),
        ("framings", FRAMING_BUCKETS, "framing"),
        ("moods", MOOD_BUCKETS, "mood"),
        ("colors", COLOR_BUCKETS, "color"),
    ]
    for cnt_key, buckets, label in dim_pairs:
        counter = counters[cnt_key]
        for bucket in buckets:
            if counter.get(bucket, 0) == 0:
                gaps.append(f"  - No {label} '{bucket}' in last {days} days")
    if gaps:
        lines.extend(gaps[:15])  # cap to 15 to avoid noise
    else:
        lines.append("  (none — feed has good coverage across known buckets)")

    return lines


# ---------------------------------------------------------------------------
# 2. get_unused_references
# ---------------------------------------------------------------------------

def get_unused_references(account: str = "EN", count: int = 12) -> list[dict]:
    """Return up to `count` unused reference image descriptions for the account.

    Reads reference_catalog.json (full pool) and reference_usage.json (used set).
    Returns a list of dicts with: filename, scene, pose, outfit, mood, one_line.
    """
    catalog = _load_json(REFERENCE_CATALOG) or {}
    images = catalog.get("images", {}) if isinstance(catalog, dict) else {}

    usage = _load_json(REFERENCE_USAGE) or {"EN": [], "JP": []}
    used_filenames = {entry.get("filename") for entry in usage.get(account, []) if isinstance(entry, dict)}

    unused: list[dict] = []
    for filename, image_data in images.items():
        if filename in used_filenames:
            continue
        analysis = image_data.get("analysis", {}) if isinstance(image_data, dict) else {}
        unused.append({
            "filename": filename,
            "scene": analysis.get("scene", ""),
            "pose": analysis.get("pose", ""),
            "outfit": analysis.get("outfit", ""),
            "lighting": analysis.get("lighting", ""),
            "mood": analysis.get("mood", ""),
            "color_palette": analysis.get("color_palette", ""),
            "one_line": analysis.get("one_line", ""),
        })

    total_unused = len(unused)
    total_pool = len(images)

    if total_unused < 30:
        logger.warning(
            "Reference pool running low: %d unused / %d total. Add new references to media/reference/ and re-run analyze_references.py",
            total_unused, total_pool,
        )

    # Return first `count` unused (deterministic order from catalog)
    return unused[:count]


# ---------------------------------------------------------------------------
# 3. mark_references_used
# ---------------------------------------------------------------------------

def mark_references_used(plan: dict) -> None:
    """Update reference_usage.json with references adopted in the plan.

    Reads `posts[].reference_filename` from reference_based posts only.
    Skips creative posts (no reference).
    """
    if not isinstance(plan, dict):
        return

    account = plan.get("account", "EN")
    posts = plan.get("posts", [])
    plan_date = plan.get("date") or _today_str()
    plan_filename = f"content_plan_{plan_date.replace('-', '')}_{account}.json"

    usage = _load_json(REFERENCE_USAGE) or {"EN": [], "JP": []}
    if account not in usage:
        usage[account] = []

    existing_filenames = {entry.get("filename") for entry in usage[account] if isinstance(entry, dict)}

    new_entries = 0
    for post in posts:
        if not isinstance(post, dict):
            continue
        if post.get("type") != "reference_based":
            continue
        ref_filename = post.get("reference_filename")
        if not ref_filename:
            continue
        if ref_filename in existing_filenames:
            logger.warning("Reference %s already used; skipping.", ref_filename)
            continue
        usage[account].append({
            "filename": ref_filename,
            "used_at": plan_date,
            "plan": plan_filename,
            "post_id": post.get("id", ""),
        })
        existing_filenames.add(ref_filename)
        new_entries += 1

    if new_entries > 0:
        _save_json(REFERENCE_USAGE, usage)
        logger.info("Marked %d references as used for %s.", new_entries, account)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> int:
    parser = argparse.ArgumentParser(description="Feed balance + reference pool tools (Meruru v5)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_balance = sub.add_parser("balance", help="Compute feed balance")
    p_balance.add_argument("account", default="EN", nargs="?")
    p_balance.add_argument("--days", type=int, default=14)

    p_unused = sub.add_parser("unused", help="Get unused references")
    p_unused.add_argument("account", default="EN", nargs="?")
    p_unused.add_argument("count", type=int, default=12, nargs="?")

    p_mark = sub.add_parser("mark", help="Mark references used from a plan file")
    p_mark.add_argument("plan_path")

    args = parser.parse_args()

    if args.cmd == "balance":
        result = compute_feed_balance(args.account, args.days)
        print(result["summary"])
        print()
        print(f"[note] {result['note']}")
        return 0

    if args.cmd == "unused":
        refs = get_unused_references(args.account, args.count)
        print(f"Unused references for {args.account}: {len(refs)} returned")
        for i, ref in enumerate(refs, 1):
            one_line = ref.get("one_line", "").strip()[:120]
            print(f"  {i}. {ref['filename']}")
            if one_line:
                print(f"     {one_line}")
        return 0

    if args.cmd == "mark":
        plan = _load_json(args.plan_path)
        if not plan:
            logger.error("Could not load plan: %s", args.plan_path)
            return 1
        mark_references_used(plan)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(_cli())
