"""Analyze reference images in media/reference/ using Claude vision.

Produces a text catalog of visual descriptions that the Creator LLM
can use as fresh external inspiration for image prompts and captions.

Usage:
    python3 scripts/analyze_references.py
    python3 scripts/analyze_references.py --max 10
    python3 scripts/analyze_references.py --force  (re-analyze all, ignore cache)

Output:
    data/content/reference_catalog.json — cached descriptions of all analyzed images
    Stdout: summary of new/updated analyses

Zero X API calls. Uses claude -p with vision for image analysis.
"""

import argparse
import glob
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

JST = ZoneInfo("Asia/Tokyo")
REFERENCE_DIR = os.path.join(PROJECT, "media", "reference")
CATALOG_PATH = os.path.join(PROJECT, "data", "content", "reference_catalog.json")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [REF_ANALYZE] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are analyzing a reference image for an AI beauty content account. Describe this image in a structured way that a content creator can use as inspiration.

Analyze the COMPLETE visual composition:

1. **scene**: Where is this? (bedroom, bathroom, gym, beach, studio, outdoor, etc.) What makes this specific setting work?
2. **pose**: Body position, stance, hand placement, head angle, overall energy
3. **outfit**: What is worn? Color, style, fit, how it works with the body
4. **lighting**: Direction, warmth, intensity, natural vs artificial, shadows
5. **mood**: What emotion or energy does this image convey? What makes it compelling?
6. **camera**: Angle (low/eye-level/high), framing (full body/medium/close), POV (selfie/mirror/third-person)
7. **color_palette**: Dominant 3-4 colors
8. **what_works**: Why would this image perform well on social media? What's the hook?

Output ONLY valid JSON:
{
  "scene": "...",
  "pose": "...",
  "outfit": "...",
  "lighting": "...",
  "mood": "...",
  "camera": "...",
  "color_palette": "...",
  "what_works": "...",
  "one_line": "A single sentence capturing the essence of this image for quick reference"
}"""


def file_hash(path: str) -> str:
    """Quick hash of file to detect changes."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(8192))  # First 8KB is enough for change detection
    return h.hexdigest()[:12]


def load_catalog() -> dict:
    """Load existing catalog or return empty."""
    try:
        with open(CATALOG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"images": {}, "generated_at": None, "total": 0}


def save_catalog(catalog: dict) -> None:
    os.makedirs(os.path.dirname(CATALOG_PATH), exist_ok=True)
    catalog["generated_at"] = datetime.now(JST).isoformat()
    catalog["total"] = len(catalog["images"])
    with open(CATALOG_PATH, "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    logger.info(f"Catalog saved: {catalog['total']} images → {CATALOG_PATH}")


def analyze_image(image_path: str) -> dict | None:
    """Analyze a single image using claude -p with vision."""
    abs_path = os.path.abspath(image_path)
    filename = os.path.basename(image_path)

    # Build a prompt that instructs Claude to read the image
    prompt = f"""Read the image at: {abs_path}

{ANALYSIS_PROMPT}"""

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "sonnet", "--no-session-persistence"],
            capture_output=True, text=True, timeout=60,
            env=env, cwd=os.path.expanduser("~"),
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout analyzing {filename}")
        return None

    if result.returncode != 0:
        logger.warning(f"Failed to analyze {filename}: {result.stderr[:200]}")
        return None

    output = result.stdout.strip()

    # Extract JSON
    if output.startswith("```"):
        lines = output.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        output = "\n".join(lines).strip()

    start = output.find("{")
    end = output.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(output[start:end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning(f"Could not parse JSON from analysis of {filename}")
    return None


def get_reference_images() -> list[str]:
    """Get all image files in media/reference/."""
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(REFERENCE_DIR, ext)))
    return sorted(images)


def main():
    parser = argparse.ArgumentParser(description="Analyze reference images for content creation")
    parser.add_argument("--max", type=int, default=None, help="Max images to analyze per run")
    parser.add_argument("--timeout", type=int, default=240, help="Max total seconds before stopping (saves progress). Default 240s.")
    parser.add_argument("--force", action="store_true", help="Re-analyze all images, ignore cache")
    args = parser.parse_args()

    run_start = time.time()

    images = get_reference_images()
    logger.info(f"Found {len(images)} reference images")

    catalog = load_catalog() if not args.force else {"images": {}, "generated_at": None, "total": 0}

    # Determine which images need analysis
    to_analyze = []
    for img_path in images:
        filename = os.path.basename(img_path)
        current_hash = file_hash(img_path)

        existing = catalog["images"].get(filename)
        if existing and existing.get("hash") == current_hash:
            continue  # Already analyzed, unchanged
        to_analyze.append((img_path, filename, current_hash))

    if args.max:
        to_analyze = to_analyze[:args.max]

    if not to_analyze:
        logger.info("All images already analyzed. Use --force to re-analyze.")
        print(f"Catalog up to date: {catalog['total']} images")
        return

    logger.info(f"Analyzing {len(to_analyze)} new/changed images (timeout={args.timeout}s)...")

    analyzed = 0
    for img_path, filename, current_hash in to_analyze:
        # Check time budget before starting next image (~20s per image)
        elapsed = time.time() - run_start
        if elapsed + 25 > args.timeout:
            remaining = len(to_analyze) - analyzed
            logger.info(f"Time budget reached ({elapsed:.0f}s/{args.timeout}s). {analyzed} done, {remaining} deferred to next run.")
            break

        logger.info(f"[{analyzed + 1}/{len(to_analyze)}] Analyzing {filename}...")
        analysis = analyze_image(img_path)

        if analysis:
            catalog["images"][filename] = {
                "filename": filename,
                "hash": current_hash,
                "analyzed_at": datetime.now(JST).isoformat(),
                "analysis": analysis,
            }
            analyzed += 1
            logger.info(f"  → {analysis.get('one_line', 'done')}")
        else:
            logger.warning(f"  → Failed, skipping")

        # Small delay between API calls
        time.sleep(1)

    # Always save progress (even partial)
    if analyzed > 0:
        save_catalog(catalog)

    elapsed = time.time() - run_start
    remaining = len(to_analyze) - analyzed
    print(f"Analyzed {analyzed} new images in {elapsed:.0f}s. Catalog total: {catalog['total']}. Remaining: {remaining}")


if __name__ == "__main__":
    main()
