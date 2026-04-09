"""Python orchestrator — sequences scripts, invokes claude -p for LLM reasoning,
validates outputs. v5 (Session 49) collapsed the multi-agent pipeline into a
single Meruru creative agent.

v5 commands (primary):
    python3 scripts/orchestrator.py create [--account EN] [--context "..."]
    python3 scripts/orchestrator.py balance [--account EN]

Legacy v4 commands (kept as fallback for ~2 weeks):
    python3 scripts/orchestrator.py pipeline    # Strategist + Creator + Marc Review

Removed in v5:
    warroom (operator never reviewed outputs — feedback loop amplified wrong signal)
    outbound (X API too expensive)
"""

import argparse
import glob
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

JST = ZoneInfo("Asia/Tokyo")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ORCHESTRATOR] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def today_str() -> str:
    return datetime.now(JST).strftime("%Y%m%d")


def today_iso() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


def yesterday_str() -> str:
    return (datetime.now(JST) - timedelta(days=1)).strftime("%Y%m%d")


def yesterday_iso() -> str:
    return (datetime.now(JST) - timedelta(days=1)).strftime("%Y-%m-%d")


def load_json(path: str) -> dict | None:
    try:
        with open(os.path.join(PROJECT, path)) as f:
            content = f.read().strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load {path}: {e}")
        return None


def save_json(path: str, data: dict) -> None:
    full_path = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {path}")


def get_active_accounts() -> list[str]:
    from x_api import get_active_accounts as _get
    return _get()


def run_script(cmd: str, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run a shell command from the project directory."""
    logger.info(f"Running: {cmd}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        timeout=timeout, cwd=PROJECT,
    )
    if result.returncode != 0:
        logger.error(f"Command failed (exit {result.returncode}): {result.stderr[:500]}")
    else:
        logger.info(f"Command succeeded: {cmd.split()[0]}")
    return result


def get_account_metrics_summary(account: str, days: int = 7) -> str:
    """Query SQLite for recent daily + post analytics. Returns formatted text for LLM context."""
    db_path = os.path.join(PROJECT, "data", "metrics", "metrics_history.db")
    if not os.path.exists(db_path):
        return "(no metrics database found)"

    import sqlite3
    conn = sqlite3.connect(db_path)
    lines = [f"=== Account Metrics Summary: {account} (last {days} days) ===\n"]

    # Daily analytics
    rows = conn.execute(
        "SELECT date, impressions, likes, engagements, new_follows, unfollows, "
        "posts_created, profile_visits FROM daily_analytics "
        "WHERE account=? ORDER BY date DESC LIMIT ?",
        (account, days)
    ).fetchall()
    if rows:
        total_follows = sum(r[4] for r in rows)
        total_unfollows = sum(r[5] for r in rows)
        total_impressions = sum(r[1] for r in rows)
        total_posts = sum(r[6] for r in rows)
        lines.append("Daily overview:")
        for r in rows:
            lines.append(f"  {r[0]}: {r[1]:,} imp, {r[2]} likes, {r[3]} eng, "
                         f"+{r[4]} follows, -{r[5]} unfollows, {r[6]} posts created, {r[7]} profile visits")
        lines.append(f"  TOTALS: {total_impressions:,} imp, +{total_follows} follows, "
                     f"-{total_unfollows} unfollows, {total_posts} posts created\n")
    else:
        lines.append("Daily overview: (no data)\n")

    # Follower count from archive if available
    followers_path = os.path.join(PROJECT, "data", "outbound", f"followers_{account}.json")
    following_path = os.path.join(PROJECT, "data", "outbound", f"following_{account}.json")
    try:
        with open(followers_path) as f:
            fd = json.load(f)
            lines.append(f"Follower count: {fd.get('count', '?')} (source: {fd.get('source', '?')}, "
                         f"fetched: {fd.get('fetched_at', '?')[:10]})")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    try:
        with open(following_path) as f:
            fd = json.load(f)
            lines.append(f"Following count: {fd.get('count', '?')} (source: {fd.get('source', '?')}, "
                         f"fetched: {fd.get('fetched_at', '?')[:10]})")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Top posts (last 7 days)
    top_posts = conn.execute(
        "SELECT date, tweet_id, impressions, likes, engagements, post_text "
        "FROM post_analytics WHERE account=? AND date >= date('now', ?) "
        "ORDER BY impressions DESC LIMIT 5",
        (account, f"-{days} days")
    ).fetchall()
    if top_posts:
        lines.append(f"\nTop 5 posts by impressions:")
        for r in top_posts:
            preview = (r[5] or "")[:60]
            lines.append(f"  {r[0]} [{r[1]}]: {r[2]:,} imp, {r[3]} likes, {r[4]} eng | {preview}")

    conn.close()
    return "\n".join(lines)


def run_validate(mode: str, *paths: str) -> tuple[bool, str]:
    """Run validate.py and return (passed, output)."""
    full_paths = [os.path.join(PROJECT, p) if not p.startswith("/") else p for p in paths]
    cmd = f"python3 scripts/validate.py {mode} {' '.join(full_paths)}"
    result = run_script(cmd)
    passed = result.returncode == 0
    output = result.stdout.strip() + "\n" + result.stderr.strip()
    return passed, output.strip()


# ---------------------------------------------------------------------------
# Core LLM invocation
# ---------------------------------------------------------------------------

def run_claude_p(prompt: str, model: str = "sonnet", timeout: int = 300, max_retries: int = 2) -> str:
    """Invoke claude -p with focused prompt. Retries on transient failures (Bun crashes, etc.)."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)  # Prevent recursive Claude Code detection

    for attempt in range(max_retries + 1):
        logger.info(f"Invoking claude -p (model={model}, prompt_len={len(prompt)}, attempt={attempt + 1}/{max_retries + 1})")
        start = time.time()

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", model, "--no-session-persistence"],
                capture_output=True, text=True, timeout=timeout,
                env=env, cwd=PROJECT,
            )
        except subprocess.TimeoutExpired:
            logger.error(f"claude -p timed out after {timeout}s")
            raise RuntimeError(f"claude -p timed out after {timeout}s")

        elapsed = time.time() - start
        logger.info(f"claude -p completed in {elapsed:.1f}s (exit={result.returncode})")

        if result.returncode == 0:
            break

        # Retry on transient errors (Bun crashes, etc.)
        stderr = result.stderr or ""
        is_transient = "bun" in stderr.lower() or "avx" in stderr.lower() or "strange crashes" in stderr.lower()
        if is_transient and attempt < max_retries:
            logger.warning(f"claude -p transient failure (attempt {attempt + 1}), retrying in 5s...")
            time.sleep(5)
            continue

        logger.error(f"claude -p failed: {stderr[:500]}")
        raise RuntimeError(f"claude -p failed: {stderr[:300]}")

    output = result.stdout.strip()

    # Strip markdown code fences if present
    if output.startswith("```"):
        lines = output.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        output = "\n".join(lines).strip()

    return output


def build_prompt(template_name: str, **kwargs) -> str:
    """Load a prompt template and substitute variables.

    Looks first in `prompts/`, then falls back to `prompts/archive/` for
    legacy v4 templates (strategist.md, creator.md, marc_review.md, etc.).
    """
    primary_path = os.path.join(PROJECT, "prompts", template_name)
    archive_path = os.path.join(PROJECT, "prompts", "archive", template_name)

    if os.path.exists(primary_path):
        template_path = primary_path
    elif os.path.exists(archive_path):
        template_path = archive_path
        logger.info(f"Loading legacy prompt from archive: {template_name}")
    else:
        raise FileNotFoundError(f"Prompt template not found in prompts/ or prompts/archive/: {template_name}")

    with open(template_path) as f:
        template = f.read()

    # Substitute {{key}} placeholders
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    return template


def read_file_content(path: str, max_chars: int = 50000) -> str:
    """Read a file and return its content, truncated if needed."""
    full_path = os.path.join(PROJECT, path) if not path.startswith("/") else path
    try:
        with open(full_path) as f:
            content = f.read()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n... [truncated at {max_chars} chars]"
        return content
    except FileNotFoundError:
        return f"[File not found: {path}]"


def send_telegram(message: str) -> None:
    """Send a text message via Telegram.

    Uses subprocess.run with argument list (no shell) so messages with
    apostrophes, quotes, or special characters are passed safely.
    """
    logger.info(f"Sending Telegram message ({len(message)} chars)")
    result = subprocess.run(
        ["python3", "scripts/telegram_send.py", message],
        capture_output=True, text=True, timeout=60, cwd=PROJECT,
    )
    if result.returncode != 0:
        logger.error(f"telegram_send failed (exit {result.returncode}): {result.stderr[:500]}")


def send_telegram_document(path: str, caption: str) -> None:
    """Send a document via Telegram."""
    full_path = os.path.join(PROJECT, path) if not path.startswith("/") else path
    logger.info(f"Sending Telegram document: {full_path}")
    result = subprocess.run(
        ["python3", "scripts/telegram_send.py", "--document", full_path, caption],
        capture_output=True, text=True, timeout=60, cwd=PROJECT,
    )
    if result.returncode != 0:
        logger.error(f"telegram_send (document) failed (exit {result.returncode}): {result.stderr[:500]}")


# ---------------------------------------------------------------------------
# Extract JSON from LLM output
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """Extract JSON from LLM output, handling code fences and extra text.

    Looks for the LARGEST valid JSON object (by character count) to avoid
    grabbing a small nested fragment like an outfit block.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Strategy: find ALL top-level JSON objects, return the largest one.
    # This prevents grabbing a small outfit fragment when the full content plan
    # is later in the output.
    candidates = []
    i = 0
    while i < len(text):
        if text[i] == "{":
            # Find matching closing brace
            depth = 0
            in_string = False
            escape = False
            for j in range(i, len(text)):
                c = text[j]
                if escape:
                    escape = False
                    continue
                if c == "\\":
                    escape = True
                    continue
                if c == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[i:j + 1]
                        try:
                            parsed = json.loads(candidate)
                            candidates.append((len(candidate), parsed))
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
            else:
                i += 1
        else:
            i += 1

    if candidates:
        # Return the largest valid JSON object
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        # Sanity check: if "largest" looks like a single post fragment
        # (has "slot" or "image_prompt" but no "posts"), try to find a
        # proper content plan or strategy object instead
        if "slot" in best and "posts" not in best and len(candidates) > 1:
            for _, candidate in candidates:
                if "posts" in candidate or "EN" in candidate or "JP" in candidate:
                    logger.warning("extract_json: largest JSON was a post fragment, using plan/strategy object instead")
                    return candidate
            logger.warning("extract_json: largest JSON looks like a post fragment but no better candidate found")

        return best

    # Fallback: first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start:end + 1])

    raise ValueError(f"Could not extract valid JSON from output (len={len(text)})")


def _extract_recent_visual_history(account: str, max_plans: int = 3) -> str:
    """Extract visual fingerprints from recent content plans for dedup.

    Returns a concise text summary of scene/pose/framing/angle/outfit per post
    across the last 3 days (~12 posts) so Creator can avoid repeats.
    """
    plans_pattern = os.path.join(PROJECT, f"data/content/content_plan_*_{account}.json")
    plan_files = sorted(glob.glob(plans_pattern), reverse=True)[:max_plans]

    if not plan_files:
        return "[no recent plans found]"

    lines = []
    for pf in plan_files:
        try:
            with open(pf) as f:
                plan = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            continue

        plan_date = plan.get("date", os.path.basename(pf))
        for post in plan.get("posts", []):
            ip = post.get("image_prompt", {})
            if not isinstance(ip, dict):
                continue

            scene = ip.get("scene", {})
            pose = ip.get("pose", {})
            camera = ip.get("camera", {})
            outfit = ip.get("outfit", {})
            top = outfit.get("top", {}) if isinstance(outfit, dict) else {}

            location = scene.get("location", "?") if isinstance(scene, dict) else "?"
            position = pose.get("position", "?") if isinstance(pose, dict) else "?"
            framing = camera.get("framing", "?") if isinstance(camera, dict) else "?"
            angle = camera.get("angle", "?") if isinstance(camera, dict) else "?"
            top_type = top.get("type", "?") if isinstance(top, dict) else "?"
            caption = post.get("text", "")[:30]

            lines.append(
                f"  [{plan_date} slot {post.get('slot', '?')}] "
                f"scene={location} | pose={position} | framing={framing} | "
                f"angle={angle} | top={top_type} | caption=\"{caption}\""
            )

    if not lines:
        return "[no visual data in recent plans]"

    header = f"Last {len(plan_files)} plans ({len(lines)} posts) — DO NOT repeat these combinations:"
    return header + "\n" + "\n".join(lines)


def _reconstruct_plan(raw_output: str, date_iso: str, account: str, strategy_path: str) -> dict:
    """Reconstruct a full content plan from Creator output that has individual post objects.

    When Sonnet outputs posts individually instead of wrapped in the container JSON,
    this function finds ALL valid post objects (have 'slot' + 'image_prompt') and
    wraps them in the expected plan structure.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    # Find all JSON objects in the output
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    posts = []
    i = 0
    while i < len(text):
        if text[i] == "{":
            depth = 0
            in_string = False
            escape = False
            for j in range(i, len(text)):
                c = text[j]
                if escape:
                    escape = False
                    continue
                if c == "\\":
                    escape = True
                    continue
                if c == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[i:j + 1]
                        try:
                            obj = json.loads(candidate)
                            # Is this a post object? Must have slot + image_prompt
                            if isinstance(obj, dict) and "slot" in obj and "image_prompt" in obj:
                                posts.append(obj)
                            # Is this already a full plan? Return it directly.
                            elif isinstance(obj, dict) and "posts" in obj:
                                logger.info(f"Found full plan in output with {len(obj['posts'])} posts")
                                return obj
                        except json.JSONDecodeError:
                            pass
                        i = j + 1
                        break
            else:
                i += 1
        else:
            i += 1

    # Deduplicate by slot number (keep the last/most complete version)
    seen_slots = {}
    for post in posts:
        slot = post.get("slot")
        if slot is not None:
            seen_slots[slot] = post
    posts = sorted(seen_slots.values(), key=lambda p: p.get("slot", 0))

    logger.info(f"Reconstructed plan: {len(posts)} posts from {len(seen_slots)} unique slots")

    plan = {
        "date": date_iso,
        "account": account,
        "generated_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "strategy_used": strategy_path,
        "total_posts": len(posts),
        "posts": posts,
        "reply_templates": [],
    }
    return plan


def _extract_recent_captions(account: str, max_plans: int = 7) -> list[str]:
    """Extract all captions from recent content plans for blocklist injection."""
    plans_pattern = os.path.join(PROJECT, f"data/content/content_plan_*_{account}.json")
    plan_files = sorted(glob.glob(plans_pattern), reverse=True)[:max_plans]
    captions = []
    for pf in plan_files:
        try:
            with open(pf) as f:
                plan = json.load(f)
            for post in plan.get("posts", []):
                text = post.get("text", "").strip()
                if text and not text.startswith("hey @grok"):
                    captions.append(text)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return captions


# ---------------------------------------------------------------------------
# v5: Meruru unified creative agent flow (`/create`)
# ---------------------------------------------------------------------------

def _format_unused_references_for_prompt(refs: list[dict]) -> str:
    """Format unused references as a compact list for the Meruru prompt.

    References are for COSTUME + POSE adoption only. Scene, lighting, and mood
    come from Meruru's identity and the feed balance — not the reference. So we
    only inject one_line summary + outfit + pose per reference. Compact format.
    """
    if not refs:
        return "[No unused references available. Operator should add new images to media/reference/ and run analyze_references.py.]"
    lines = [
        f"You have {len(refs)} unused references to choose from. Pick 3 of them (one per reference-based post). Each is single-use.",
        "",
        "Adopt the COSTUME and POSE from each reference. The scene, lighting, and mood are YOUR choice — informed by the feed balance and your visual style. Do NOT just copy the reference's setting.",
        "",
    ]
    for i, ref in enumerate(refs, 1):
        # Compact format: filename + one_line + outfit + pose only
        lines.append(f"**[{i}] `{ref['filename']}`**")
        if ref.get("one_line"):
            lines.append(f"  • {ref['one_line'].strip()[:160]}")
        if ref.get("outfit"):
            lines.append(f"  • Outfit: {ref['outfit'].strip()[:200]}")
        if ref.get("pose"):
            lines.append(f"  • Pose: {ref['pose'].strip()[:200]}")
        lines.append("")
    return "\n".join(lines)


def _build_tier1_constraints() -> str:
    """Compact Tier 1 constraints block (extracted from image_prompt_guide essentials)."""
    return """**Character lock (every image, never breaks):**
- Age: early 20s Japanese woman
- Body: extreme hourglass — large full bust, ultra-slim waist, extra-wide hips, emphasized glutes, fit and toned
- Skin: light-medium neutral, smooth, dewy
- Hair: dark/jet-black or dark brown, long (style varies, color always dark)
- Makeup: minimal — natural brows, soft lip
- Expression: ONLY use these terms — "closed-mouth smile", "subtle smirk", "lips softly closed", "lips slightly parted", "neutral gaze", "soft pout". NEVER "bright smile" (image generators interpret it as teeth-showing).

**Camera (every image):**
- ALWAYS `iPhone 15 Pro Max` with `24mm wide` lens
- NEVER DSLR, Sony, Canon, or any pro camera

**Negative prompt (always include this exact block in `negative_prompt`):**
`blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile`

**Captions (EN):**
- 30-100 chars (aim 40-80)
- Lowercase, casual punctuation
- Personality sentence — never 3-word fragments
- Never start with "@" (X hides as reply)
- Never repeat past captions
- 1-2 emoji max per post, never 👀, max 1-2 posts in the batch with emoji

**Hashtags (EN):**
- ALWAYS empty array `[]`
- Never use "#" anywhere in caption text

**Image prompt:**
- `prompt` field: 120-180 words
- No text/letters/numbers in image content
- Aspect ratio: 9:16 or 4:5 vertical (never landscape)"""


def _build_image_prompt_format() -> str:
    """Compact Higgsfield-compatible image_prompt schema."""
    return """The `image_prompt` field must be an object with this structure:

```json
{
  "prompt": "<120-180 word natural-language scene description tying everything together>",
  "negative_prompt": "<the standard combined negative block from Tier 1>",
  "aspect_ratio": "9:16",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "<e.g. 'raw iphone selfie', 'casual mirror pic', 'candid phone photo'>"
  },
  "subject": {
    "hair": { "color": "<dark>", "style": "<long wavy / straight / etc.>" },
    "body_type": "extreme hourglass, large full bust, ultra-slim waist, extra-wide hips, emphasized glutes, fit and toned",
    "skin": "light-medium neutral, smooth, dewy",
    "expression": "<one of the allowed terms>",
    "makeup": "minimal natural — clean brows, soft lip"
  },
  "outfit": {
    "top": { "type": "<e.g. ribbed crop top, lace bralette, hotel towel>", "color": "<>", "fit": "<>" },
    "bottom": { "type": "<>", "color": "<>" },
    "accessories": [ "<optional>" ]
  },
  "pose": {
    "position": "<standing / seated / reclined / kneeling / etc.>",
    "stance": "<weight on one leg, hip-shifted, etc.>",
    "hands": "<where they are>",
    "head_gaze": "<direction & energy>",
    "vibe": "<one phrase>"
  },
  "scene": {
    "location": "<specific setting, e.g. 'luxury hotel bathroom'>",
    "time": "<morning / evening / late night>",
    "atmosphere": "<one phrase>",
    "background": "<2-3 specific elements>"
  },
  "camera": {
    "pov": "<mirror selfie / handheld / over-shoulder / etc.>",
    "angle": "<eye-level / low-angle / high-angle>",
    "framing": "<close-up / medium / full-body>"
  },
  "lighting": {
    "type": "<warm recessed / hard direct / soft natural window / etc.>",
    "effect": "<one phrase>"
  },
  "mood": {
    "energy": "<one phrase>",
    "color_palette": "<dominant colors>",
    "aesthetic": "<one phrase>"
  }
}
```

The `prompt` field is a single 120-180 word paragraph weaving together all the structured fields naturally — this is what Higgsfield actually reads. The structured fields above are for clarity and validation."""


def run_create(account: str = "EN", operator_context: str = ""):
    """v5 Meruru unified creative agent flow.

    Generates 6 candidate posts (3 reference-based + 3 creative) from a single
    Opus call. Replaces the v4 Strategist → Creator → Marc Review pipeline.
    """
    import feed_balance  # local import — feed_balance.py lives in scripts/

    date = today_str()
    date_iso = today_iso()
    account = account.upper()

    logger.info(f"=== CREATE START: {date_iso} account={account} ===")
    start_time = time.time()

    # Step 0: Analyze any new reference images (picks up daily additions)
    logger.info("Step 0: Analyze new reference images")
    try:
        ref_result = run_script("python3 scripts/analyze_references.py --timeout 240", timeout=300)
        if ref_result.returncode != 0:
            logger.warning(f"Reference analysis failed (non-fatal): {ref_result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        logger.warning("Reference analysis timed out (non-fatal) — continuing with existing catalog")

    # Step 1: Pre-compute feed balance (Python, instant, no LLM)
    logger.info("Step 1: Compute feed balance")
    balance = feed_balance.compute_feed_balance(account, days=14)
    feed_balance_text = balance["summary"] + "\n\n[note] " + balance["note"]

    # Step 2: Get unused reference pool (Python, instant)
    logger.info("Step 2: Get unused references")
    unused_refs = feed_balance.get_unused_references(account, count=12)
    unused_refs_text = _format_unused_references_for_prompt(unused_refs)

    # Step 3: Load identity document
    logger.info("Step 3: Load Meruru identity")
    identity = read_file_content("config/meruru_identity.md", max_chars=20000)

    # Step 4: Extract recent caption blocklist
    logger.info("Step 4: Extract recent captions blocklist")
    recent_captions_list = _extract_recent_captions(account, max_plans=7)
    if recent_captions_list:
        recent_captions_text = "\n".join(f"- {c}" for c in recent_captions_list[:50])
    else:
        recent_captions_text = "[No recent captions to avoid — fresh feed]"

    # Step 5: Build Meruru prompt
    logger.info("Step 5: Build Meruru prompt")
    prompt = build_prompt(
        "meruru.md",
        date=date_iso,
        account=account,
        identity=identity,
        feed_balance=feed_balance_text,
        unused_references=unused_refs_text,
        recent_captions=recent_captions_text,
        operator_context=operator_context.strip() or "[None — operator did not provide additional context.]",
        tier1_constraints=_build_tier1_constraints(),
        image_prompt_format=_build_image_prompt_format(),
    )
    logger.info(f"Meruru prompt size: {len(prompt)} chars")

    # Step 6: Opus call with retry on fragment output
    max_create_retries = 1
    raw_output = ""
    plan_json = {}

    for create_attempt in range(max_create_retries + 1):
        logger.info(f"Step 6: Invoke Meruru (Opus, attempt {create_attempt + 1}/{max_create_retries + 1})")
        raw_output = run_claude_p(prompt, model="opus", timeout=700)
        plan_json = extract_json(raw_output)

        # Check if we got a proper wrapper with posts array
        if isinstance(plan_json.get("posts"), list) and len(plan_json["posts"]) > 0:
            break  # Got a valid plan

        # Fragment detected — retry or reconstruct
        if "slot" in plan_json and "posts" not in plan_json:
            if create_attempt < max_create_retries:
                logger.warning(
                    f"Meruru output a post fragment (attempt {create_attempt + 1}) — retrying for proper wrapper"
                )
                continue
            else:
                logger.warning(
                    f"Meruru output fragments after {max_create_retries + 1} attempts — reconstructing from all JSON objects"
                )
                plan_json = _reconstruct_plan(raw_output, date_iso, account, "meruru_v5")
        else:
            # Some other unexpected output structure — try reconstruction as last resort
            logger.warning(f"Unexpected Meruru output structure (keys: {list(plan_json.keys())[:10]}) — attempting reconstruction")
            plan_json = _reconstruct_plan(raw_output, date_iso, account, "meruru_v5")

    # Defensive cleanup: strip "tool" field from image_prompt
    for post in plan_json.get("posts", []):
        ip = post.get("image_prompt", {})
        if isinstance(ip, dict):
            ip.pop("tool", None)

    # Ensure required top-level fields are present
    plan_json.setdefault("date", date_iso)
    plan_json.setdefault("account", account)
    plan_json.setdefault("generated_at", datetime.now(JST).isoformat())
    plan_json["total_posts"] = len(plan_json.get("posts", []))

    actual_posts = len(plan_json.get("posts", []))
    if actual_posts != 6:
        logger.warning(f"Meruru produced {actual_posts}/6 posts — accepting partial output")

    # Step 7: Validate (Tier 1 only — creator mode)
    plan_path = f"data/content/content_plan_{date}_{account}.json"
    save_json(plan_path, plan_json)
    logger.info(f"Step 7: Validate {plan_path}")
    passed, val_output = run_validate("creator", plan_path)
    if not passed:
        logger.warning(f"Meruru validation warnings: {val_output[:500]}")

    # Step 8: Mark used references
    logger.info("Step 8: Mark used references")
    try:
        feed_balance.mark_references_used(plan_json)
    except Exception as e:
        logger.warning(f"mark_references_used failed (non-fatal): {e}")

    # Step 9: Generate HTML report
    logger.info("Step 9: Generate HTML report")
    try:
        html_result = run_script(
            f"python3 scripts/generate_html_report.py content_plan {plan_path}",
            timeout=60,
        )
        if html_result.returncode != 0:
            logger.warning(f"HTML report generation failed: {html_result.stderr[:200]}")
    except Exception as e:
        logger.warning(f"HTML report generation error: {e}")

    # Step 10: Send to Telegram
    logger.info("Step 10: Send to Telegram")
    try:
        ref_based = sum(1 for p in plan_json.get("posts", []) if p.get("type") == "reference_based")
        creative = sum(1 for p in plan_json.get("posts", []) if p.get("type") == "creative")
        msg = (
            f"🎨 Meruru content plan ready — {date_iso} ({account})\n"
            f"{actual_posts} candidates generated: {ref_based} reference-based + {creative} creative\n"
            f"Plan: {plan_path}\n"
            f"Pick 4 from the 6 candidates to actually post."
        )
        send_telegram(msg)
        # Try to also send the HTML report as a document
        html_path = plan_path.replace(".json", ".html")
        if os.path.exists(os.path.join(PROJECT, html_path)):
            send_telegram_document(html_path, f"Meruru plan {date_iso} ({account})")
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")

    elapsed = time.time() - start_time
    logger.info(f"=== CREATE COMPLETE: {elapsed:.0f}s ({actual_posts} posts) ===")
    return plan_json


# ---------------------------------------------------------------------------
# v5: Meruru balance check flow (`/balance`)
# ---------------------------------------------------------------------------

def run_balance(account: str = "EN") -> str:
    """v5 Meruru balance check flow.

    Computes feed balance (Python) then asks Meruru to interpret it and
    recommend what to post next. Sends recommendation directly to Telegram.

    Returns the recommendation text for testing convenience.
    """
    import feed_balance  # local import — feed_balance.py lives in scripts/

    date_iso = today_iso()
    account = account.upper()

    logger.info(f"=== BALANCE START: {date_iso} account={account} ===")
    start_time = time.time()

    # Step 1: Compute feed balance
    logger.info("Step 1: Compute feed balance")
    balance = feed_balance.compute_feed_balance(account, days=14)
    feed_balance_text = balance["summary"] + "\n\n[note] " + balance["note"]

    # Step 2: Load identity
    logger.info("Step 2: Load Meruru identity")
    identity = read_file_content("config/meruru_identity.md", max_chars=20000)

    # Step 3: Build balance prompt
    logger.info("Step 3: Build balance prompt")
    prompt = build_prompt(
        "meruru_balance.md",
        date=date_iso,
        account=account,
        identity=identity,
        feed_balance=feed_balance_text,
    )
    logger.info(f"Balance prompt size: {len(prompt)} chars")

    # Step 4: Single Opus call (lighter than /create)
    logger.info("Step 4: Invoke Meruru balance (Opus)")
    recommendation = run_claude_p(prompt, model="opus", timeout=300)

    # Strip stray whitespace and any leading/trailing junk
    recommendation = recommendation.strip()

    # Step 5: Send to Telegram
    logger.info("Step 5: Send recommendation to Telegram")
    try:
        msg = f"🪞 Meruru feed check — {account}\n\n{recommendation}"
        send_telegram(msg)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")

    elapsed = time.time() - start_time
    logger.info(f"=== BALANCE COMPLETE: {elapsed:.0f}s ===")
    return recommendation


# ---------------------------------------------------------------------------
# Pipeline flow
# ---------------------------------------------------------------------------

def run_pipeline(accounts: list[str] | None = None):
    """**LEGACY v4 fallback** — Strategist + Creator + Marc Review.

    Superseded by `run_create()` in v5 (Session 49). Kept temporarily for
    fallback if v5 has issues. Will be removed after ~2 weeks of stable v5.

    Zero X API calls. Uses local data only:
    - Previous strategies and content plans
    - Standing directives
    - Operator-provided metrics (CSV imports, manual input)
    - Core strategy rules
    """
    date = today_str()
    date_iso = today_iso()
    accounts = accounts or get_active_accounts()

    logger.info(f"=== PIPELINE START: {date_iso} accounts={accounts} ===")
    start_time = time.time()

    # Step 0: Analyze any new reference images (picks up daily additions)
    # Script self-terminates at --timeout (saves partial progress). External timeout is generous safety net.
    logger.info("Step 0: Analyze new reference images")
    try:
        ref_result = run_script("python3 scripts/analyze_references.py --timeout 240", timeout=300)
        if ref_result.returncode != 0:
            logger.warning(f"Reference analysis failed (non-fatal): {ref_result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        logger.warning("Reference analysis timed out (non-fatal) — continuing with existing catalog")

    # Step 1: Strategist (1 LLM call)
    # No scout data — Strategist works from previous strategy, feedback,
    # operator-provided metrics, and standing directives.
    logger.info("Step 1: Strategist")
    strategy_path = f"data/strategy/strategy_{date}.json"

    # Build context for Strategist (all local files, zero API)
    feedback_path = f"data/strategy/strategy_feedback_{yesterday_str()}.json"
    feedback_data = read_file_content(feedback_path)
    briefing_path = f"data/metrics/morning_briefing_{date}.json"
    briefing_data = read_file_content(briefing_path)
    # Only include active directives to keep prompt lean (resolved ones add ~40K of noise)
    sd_raw = load_json("data/strategy/standing_directives.json")
    if sd_raw and sd_raw.get("directives"):
        active_directives = [d for d in sd_raw["directives"] if d.get("status") != "resolved"]
        directives_data = json.dumps({"directives": active_directives, "active_count": len(active_directives), "total_count": len(sd_raw["directives"])}, indent=2)
    else:
        directives_data = read_file_content("data/strategy/standing_directives.json")
    core_strategy = read_file_content("data/strategy/core_strategy.json")
    prev_strategy = read_file_content("data/strategy/strategy_current.json")

    # Read operator-provided metrics (from CSV imports or manual input)
    latest_metrics = {}
    for acct in accounts:
        metrics_pattern = os.path.join(PROJECT, f"data/metrics/metrics_*_{acct}.json")
        metrics_files = sorted(glob.glob(metrics_pattern), reverse=True)
        if metrics_files:
            latest_metrics[acct] = read_file_content(metrics_files[0])
        else:
            latest_metrics[acct] = "[no metrics available]"

    # Read latest daily report if available
    report_pattern = os.path.join(PROJECT, "data/metrics/daily_report_*.json")
    report_files = sorted(glob.glob(report_pattern), reverse=True)
    latest_report = read_file_content(report_files[0]) if report_files else "[no daily report available]"

    # Read last 3 content plans per account for variety
    recent_plans = {}
    for acct in accounts:
        plans_pattern = os.path.join(PROJECT, f"data/content/content_plan_*_{acct}.json")
        plan_files = sorted(glob.glob(plans_pattern), reverse=True)[:3]
        plans_content = []
        for pf in plan_files:
            try:
                with open(pf) as f:
                    plans_content.append(f.read()[:2000])
            except FileNotFoundError:
                pass
        recent_plans[acct] = "\n---\n".join(plans_content) if plans_content else "[No recent plans]"

    # Load reference catalog for Strategist creative brief inspiration
    # Cap at 30 random samples to keep prompt size manageable (full catalog can be 140K+)
    ref_catalog = load_json("data/content/reference_catalog.json")
    if ref_catalog and ref_catalog.get("images"):
        import random
        all_entries = [
            (fname, entry) for fname, entry in ref_catalog["images"].items()
            if entry.get("analysis")
        ]
        sampled = random.sample(all_entries, min(30, len(all_entries)))
        ref_one_liners = [
            f"- {fname}: {entry['analysis'].get('one_line', '')} (scene: {entry['analysis'].get('scene', '')}, mood: {entry['analysis'].get('mood', '')})"
            for fname, entry in sampled
        ]
        ref_summary = f"{len(all_entries)} reference images available ({len(sampled)} shown). Use these to inform post_purpose and visual_focus choices:\n" + "\n".join(ref_one_liners)
    else:
        ref_summary = "[No reference catalog. Run: python3 scripts/analyze_references.py]"

    # Build real account metrics from SQLite (CSV imports + archive)
    account_metrics = {}
    for acct in accounts:
        account_metrics[acct] = get_account_metrics_summary(acct, days=7)

    prompt = build_prompt(
        "strategist.md",
        date=date_iso,
        date_compact=date,
        accounts=", ".join(accounts),
        strategy_feedback=feedback_data,
        morning_briefing=briefing_data,
        standing_directives=directives_data,
        core_strategy=core_strategy,
        previous_strategy=prev_strategy,
        latest_report=latest_report,
        metrics_EN=latest_metrics.get("EN", "[not available]"),
        metrics_JP=latest_metrics.get("JP", "[not available]"),
        account_metrics_EN=account_metrics.get("EN", "[not available]"),
        account_metrics_JP=account_metrics.get("JP", "[not available]"),
        reference_images=ref_summary,
        recent_plans_EN=recent_plans.get("EN", "[none]"),
        recent_plans_JP=recent_plans.get("JP", "[none]"),
        output_path=strategy_path,
    )

    strategy_output = run_claude_p(prompt, model="opus", timeout=600)
    strategy_json = extract_json(strategy_output)
    save_json(strategy_path, strategy_json)

    # Validate strategy
    passed, val_output = run_validate("strategist", strategy_path)
    if not passed:
        logger.warning(f"Strategy validation failed: {val_output}")
        send_telegram(f"Strategy validation warning: {val_output[:300]}")

    # Update strategy_current.json
    save_json("data/strategy/strategy_current.json", strategy_json)

    # Step 2: Creator (1 LLM call per account)
    logger.info("Step 2: Creator")
    meruru_concept = read_file_content("config/meruru_concept.md")
    image_guide = read_file_content("config/image_prompt_guide.md", max_chars=15000)  # Cap at 15K (was 32K)
    global_rules = read_file_content("config/global_rules.md")

    # Extract only active directives for Creator (full list was 50K+, most resolved/irrelevant)
    sd_full = load_json("data/strategy/standing_directives.json") or {"directives": []}
    active_directives = [
        d for d in sd_full.get("directives", [])
        if d.get("status") == "active" and d.get("assigned_to") in ("creator", "all", "strategist")
    ]
    directives_for_creator = json.dumps({"directives": active_directives}, indent=2, ensure_ascii=False)
    logger.info(f"Directives for Creator: {len(active_directives)} active (was {len(sd_full.get('directives', []))} total, {len(directives_for_creator)/1024:.0f}K chars)")

    # Load reference image catalog (pre-analyzed visual inspiration)
    ref_catalog = load_json("data/content/reference_catalog.json")
    visual_direction_summary = "[No reference catalog — use your best judgment on visual direction]"
    if ref_catalog and ref_catalog.get("images"):
        from collections import Counter

        # Collect stats from ALL images for visual direction summary
        scenes = []
        outfits = []
        for entry in ref_catalog["images"].values():
            a = entry.get("analysis", {})
            if a.get("scene"):
                scenes.append(a["scene"])
            if a.get("outfit"):
                outfits.append(a["outfit"])

        scene_counts = Counter(scenes)
        outfit_counts = Counter(outfits)
        total_refs = len(ref_catalog["images"])
        top_scenes = [s for s, _ in scene_counts.most_common(5)]
        top_outfits = [o for o, _ in outfit_counts.most_common(5)]
        visual_direction_summary = (
            f"Based on {total_refs} reference images:\n"
            f"- DOMINANT SCENES: {', '.join(top_scenes)}\n"
            f"- DOMINANT OUTFITS: {', '.join(top_outfits)}\n"
            f"- YOUR CONTENT MUST MATCH THIS DIRECTION. At least 3 of 4 posts should use scenes and outfits "
            f"from these dominant categories. Do NOT invent unrelated scenes."
        )
        logger.info(f"Visual direction: scenes={top_scenes[:3]}, outfits={top_outfits[:3]}")

        # For Creator prompt: include only 20 most recent images with COMPACT descriptions
        # (Full catalog was 302KB — caused prompt to hit 342K chars and Sonnet to fail)
        sorted_images = sorted(
            ref_catalog["images"].items(),
            key=lambda x: x[1].get("analyzed_at", ""),
            reverse=True,
        )[:20]

        ref_lines = []
        for filename, entry in sorted_images:
            a = entry.get("analysis", {})
            ref_lines.append(
                f"- **{filename}**: {a.get('one_line', '')} "
                f"[scene: {a.get('scene', '')[:80]} | pose: {a.get('pose', '')[:60]} | "
                f"outfit: {a.get('outfit', '')[:60]}]"
            )

        reference_images_text = (
            f"{total_refs} reference images analyzed (showing 20 most recent). "
            f"Match their content type, settings, and outfit energy. "
            f"Adapt to Meruru's character — do NOT copy subjects.\n\n"
            + "\n".join(ref_lines)
        )
        logger.info(f"Reference text for Creator: {len(reference_images_text)} chars (was ~300KB, now compact)")
    else:
        reference_images_text = "[No reference catalog found. Run: python3 scripts/analyze_references.py]"

    for acct in accounts:
        plan_path = f"data/content/content_plan_{date}_{acct}.json"

        # Extract recent captions as explicit blocklist
        recent_captions = _extract_recent_captions(acct, max_plans=7)
        recent_captions_text = "\n".join(f"  - \"{c}\"" for c in recent_captions) if recent_captions else "[none found]"

        # Extract visual history from last 3 days for image prompt dedup
        recent_visual_history = _extract_recent_visual_history(acct, max_plans=3)

        # Extract only this account's strategy section (full strategy includes both EN+JP = 25K)
        acct_strategy = strategy_json.get(acct, {})
        acct_strategy_text = json.dumps(
            {"date": strategy_json.get("date"), acct: acct_strategy},
            indent=2, ensure_ascii=False
        )

        prompt = build_prompt(
            "creator.md",
            date=date_iso,
            date_compact=date,
            account=acct,
            strategy=acct_strategy_text,
            meruru_concept=meruru_concept,
            image_prompt_guide=image_guide,
            global_rules=global_rules,
            recent_plans=recent_plans.get(acct, "[none]"),
            recent_captions=recent_captions_text,
            recent_visual_history=recent_visual_history,
            standing_directives=directives_for_creator,
            reference_images=reference_images_text,
            visual_direction_summary=visual_direction_summary,
            output_path=plan_path,
        )

        # Retry loop: if Creator produces fewer posts than expected, retry up to 2 times
        expected_slots = len(strategy_json.get(acct, {}).get("posting_schedule", []))
        max_creator_retries = 2

        for creator_attempt in range(max_creator_retries + 1):
            creator_output = run_claude_p(prompt, model="sonnet", timeout=900)
            plan_json = extract_json(creator_output)

            # If Creator output individual posts instead of the wrapper, reconstruct
            if "slot" in plan_json and "posts" not in plan_json:
                logger.warning("Creator output a post fragment — reconstructing full plan from all JSON objects")
                plan_json = _reconstruct_plan(creator_output, date_iso, acct, strategy_path)

            # Strip "tool" field from image_prompt (defensive cleanup)
            for post in plan_json.get("posts", []):
                ip = post.get("image_prompt", {})
                if isinstance(ip, dict):
                    ip.pop("tool", None)

            actual_posts = len(plan_json.get("posts", []))
            if actual_posts >= expected_slots:
                break  # Got all posts

            if creator_attempt < max_creator_retries:
                logger.warning(
                    f"Creator {acct} produced {actual_posts}/{expected_slots} posts "
                    f"(attempt {creator_attempt + 1}/{max_creator_retries + 1}) — retrying"
                )
            else:
                logger.error(
                    f"Creator {acct} produced {actual_posts}/{expected_slots} posts "
                    f"after {max_creator_retries + 1} attempts — accepting partial output"
                )

        save_json(plan_path, plan_json)

        # Validate content plan
        passed, val_output = run_validate("creator", plan_path)
        if not passed:
            logger.warning(f"Creator {acct} validation failed: {val_output}")

        # Cross-validate with strategy
        passed, val_output = run_validate("creator_cross", plan_path, strategy_path)
        if not passed:
            logger.warning(f"Creator {acct} cross-validation failed: {val_output}")

    # Step 3: Marc Strategic Review (1 LLM call)
    logger.info("Step 3: Marc Strategic Review")
    run_marc_review(date, date_iso, accounts, "pipeline")

    elapsed = time.time() - start_time
    logger.info(f"=== PIPELINE COMPLETE: {elapsed:.0f}s ===")


# ---------------------------------------------------------------------------
# War Room flow — REMOVED in v5
# ---------------------------------------------------------------------------
# The war room flow was removed in v5 (Session 49) because the operator never
# reviewed the outputs and the same recommendations were flagged for 8+
# consecutive days with zero action. The feedback loop was amplifying the wrong
# signal. If analytics feedback is ever needed again, reintroduce as an
# optional, lighter tool — not a daily auto-run.
#
# The old run_warroom() function and its prompts are archived at:
#   prompts/archive/warroom.md
#   prompts/archive/marc_review.md (also handled war room reviews)


# ---------------------------------------------------------------------------
# Marc Strategic Review
# ---------------------------------------------------------------------------

def run_marc_review(date: str, date_iso: str, accounts: list[str], flow_type: str):
    """Run Marc's strategic review at the end of a flow."""

    # Gather all outputs from this flow
    review_context = {
        "flow_type": flow_type,
        "date": date_iso,
        "accounts": accounts,
    }

    # Always include current metrics, directives, and account data
    review_context["standing_directives"] = read_file_content("data/strategy/standing_directives.json")
    review_context["global_rules"] = read_file_content("config/global_rules.md")

    # Include real account metrics from SQLite + archive data
    for acct in accounts:
        review_context[f"account_metrics_{acct}"] = get_account_metrics_summary(acct, days=7)

    # Flow-specific outputs
    if flow_type == "pipeline":
        review_context["strategy"] = read_file_content(f"data/strategy/strategy_{date}.json")
        for acct in accounts:
            review_context[f"content_plan_{acct}"] = read_file_content(f"data/content/content_plan_{date}_{acct}.json")
    elif flow_type.startswith("warroom"):
        session = flow_type.split("_")[1] if "_" in flow_type else "morning"
        if session == "morning":
            review_context["morning_briefing"] = read_file_content(f"data/metrics/morning_briefing_{date}.json")
        else:
            review_context["strategy_feedback"] = read_file_content(f"data/strategy/strategy_feedback_{date}.json")
        for acct in accounts:
            review_context[f"metrics_{acct}"] = read_file_content(f"data/metrics/metrics_{date}_{acct}.json")
    elif flow_type == "outbound":
        for acct in accounts:
            review_context[f"outbound_plan_{acct}"] = read_file_content(f"data/outbound/outbound_plan_{date}_{acct}.json")
            review_context["outbound_log"] = read_file_content(f"data/outbound/outbound_log_{date}.json")

    # Format context
    context_text = ""
    for key, val in review_context.items():
        if isinstance(val, (list, dict)):
            context_text += f"\n\n### {key}\n```\n{json.dumps(val)}\n```"
        else:
            context_text += f"\n\n### {key}\n```\n{val}\n```"

    prompt = build_prompt(
        "marc_review.md",
        date=date_iso,
        date_compact=date,
        flow_type=flow_type,
        accounts=", ".join(accounts),
        context=context_text,
    )

    review_output = run_claude_p(prompt, model="opus", timeout=600)

    # Parse Marc's review — expect JSON with telegram_message and directive_updates
    try:
        review_json = extract_json(review_output)
    except (json.JSONDecodeError, ValueError):
        # If not valid JSON, treat the whole output as text
        logger.warning("Marc review didn't return JSON, using raw text")
        review_json = {"telegram_message": review_output[:2000], "directive_updates": []}

    # Save review
    review_path = f"data/reports/marc_review_{date}_{flow_type}.json"
    save_json(review_path, review_json)

    # Send Telegram message
    telegram_msg = review_json.get("telegram_message", "")
    if telegram_msg:
        send_telegram(telegram_msg)

    # Send HTML reports if applicable
    if flow_type == "pipeline":
        for acct in accounts:
            plan_path = f"data/content/content_plan_{date}_{acct}.json"
            html_path = plan_path.replace(".json", ".html")
            run_script(f"python3 scripts/generate_html_report.py content_plan {plan_path}")
            if os.path.exists(os.path.join(PROJECT, html_path)):
                send_telegram_document(html_path, f"Content Plan {acct} — {date_iso}")
    elif flow_type.startswith("warroom"):
        session = flow_type.split("_")[1] if "_" in flow_type else "morning"
        if session == "morning":
            briefing_path = f"data/metrics/morning_briefing_{date}.json"
            html_path = briefing_path.replace(".json", ".html")
            run_script(f"python3 scripts/generate_html_report.py generic {briefing_path} --title 'Morning Briefing {date_iso}'")
            if os.path.exists(os.path.join(PROJECT, html_path)):
                send_telegram_document(html_path, f"Morning Briefing — {date_iso}")
        else:
            report_path = f"data/metrics/daily_report_{date}.json"
            if os.path.exists(os.path.join(PROJECT, report_path)):
                html_path = report_path.replace(".json", ".html")
                run_script(f"python3 scripts/generate_html_report.py daily_report {report_path}")
                if os.path.exists(os.path.join(PROJECT, html_path)):
                    send_telegram_document(html_path, f"Daily Report — {date_iso}")
    elif flow_type == "outbound":
        # Escalate manual replies
        manual_replies = review_json.get("manual_replies_escalation", "")
        if manual_replies:
            send_telegram(manual_replies)

    # Process directive updates
    directive_updates = review_json.get("directive_updates", [])
    if directive_updates:
        _apply_directive_updates(directive_updates)


def _apply_directive_updates(updates: list[dict]):
    """Apply Marc's directive updates to standing_directives.json.

    Enforces DIR-NNN ID requirement and prevents duplicates.
    """
    import re
    sd_path = "data/strategy/standing_directives.json"
    sd = load_json(sd_path) or {"directives": []}

    for update in updates:
        action = update.get("action", "")

        if action == "add":
            # Add new directive — must have valid DIR-NNN id
            new_dir = update.get("directive", {})
            dir_id = update.get("id") or new_dir.get("id", "")
            if not dir_id:
                dir_id = update.get("id", "")
            # Ensure id is on the directive object
            if dir_id:
                new_dir["id"] = dir_id

            # Reject directives without valid DIR-NNN id
            if not re.match(r"^DIR-\d{3}$", str(dir_id)):
                logger.warning(f"Rejected directive without valid DIR-NNN id: {dir_id!r}")
                continue

            # Reject duplicate ids
            existing_ids = {d.get("id") for d in sd["directives"]}
            if dir_id in existing_ids:
                logger.warning(f"Rejected duplicate directive: {dir_id}")
                continue

            if new_dir:
                sd["directives"].append(new_dir)
                logger.info(f"Added directive: {dir_id}")

        elif action == "resolve":
            # Resolve existing directive
            dir_id = update.get("id", "")
            for d in sd["directives"]:
                if d.get("id") == dir_id:
                    d["status"] = "resolved"
                    d["resolved_date"] = today_iso()
                    d["resolution"] = update.get("resolution", "Resolved by Marc review")
                    logger.info(f"Resolved directive: {dir_id}")

        elif action == "expire":
            dir_id = update.get("id", "")
            for d in sd["directives"]:
                if d.get("id") == dir_id:
                    d["status"] = "expired"
                    logger.info(f"Expired directive: {dir_id}")

    save_json(sd_path, sd)


# ---------------------------------------------------------------------------
# Execute ready directives
# ---------------------------------------------------------------------------

def execute_ready_directives():
    """Check standing_directives.json, run script-type directives."""
    sd = load_json("data/strategy/standing_directives.json")
    if not sd:
        return

    changed = False
    for d in sd.get("directives", []):
        if d.get("status") == "active" and d.get("execution_type") == "script":
            cmd = d.get("command", "")
            if cmd:
                logger.info(f"Executing directive {d.get('id', '?')}: {cmd}")
                result = run_script(cmd, timeout=600)
                if result.returncode == 0:
                    d["status"] = "resolved"
                    d["resolved_date"] = today_iso()
                    d["resolution"] = "Script executed successfully (exit 0)"
                    changed = True
                else:
                    logger.error(f"Directive {d.get('id', '?')} failed: {result.stderr[:200]}")

    if changed:
        save_json("data/strategy/standing_directives.json", sd)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="X-Agents Orchestrator")
    parser.add_argument("command", choices=["create", "balance", "pipeline"],
                        help="Flow to execute (create=v5 primary, balance=v5 feed check, pipeline=legacy v4 fallback)")
    parser.add_argument("session", nargs="?",
                        help="(Unused — preserved for backward compat)")
    parser.add_argument("--account", help="Run for specific account only")
    parser.add_argument("--context", default="",
                        help="Optional free-text operator context for `create` command")

    args = parser.parse_args()

    accounts = [args.account.upper()] if args.account else None

    try:
        if args.command == "create":
            # v5 Meruru flow — single account per call
            create_account = (accounts[0] if accounts else "EN")
            run_create(create_account, operator_context=args.context)
        elif args.command == "balance":
            # v5 Meruru balance check — single account per call
            balance_account = (accounts[0] if accounts else "EN")
            run_balance(balance_account)
        elif args.command == "pipeline":
            # Legacy v4 fallback — Strategist + Creator + Marc Review
            logger.warning("Running legacy v4 pipeline. v5 `create` is the primary command.")
            run_pipeline(accounts)
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}", exc_info=True)
        try:
            send_telegram(f"Orchestrator {args.command} failed: {str(e)[:200]}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
