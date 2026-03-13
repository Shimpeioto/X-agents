"""Analyze top-performing competitor images via Anthropic Vision API.

Reads a scout report, picks top N posts with images by engagement,
calls Claude Vision to analyze each image, outputs structured Higgsfield-format
reference prompts for the Creator agent.

Usage:
    python3 scripts/image_analyzer.py data/scout/scout_report_20260308.json
    python3 scripts/image_analyzer.py data/scout/scout_report_20260308.json --top 10
    python3 scripts/image_analyzer.py data/scout/scout_report_20260308.json --dry-run

Exit codes: 0=success, 1=error
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

logging.basicConfig(
    format="[%(asctime)s] [IMAGE_ANALYZER] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

VISION_PROMPT = """Analyze this image from a high-performing social media post. Describe it using this exact JSON structure for image generation recreation:

{
  "scene_type": "mirror_selfie|bathroom|pool_beach|bedroom_casual|fashion_editorial|lifestyle_street|other",
  "subject": {
    "apparent_age": "...",
    "hair": {"color": "...", "style": "..."},
    "body_type": "...",
    "skin": "...",
    "expression": "...",
    "makeup": "..."
  },
  "outfit": {
    "top": {"type": "...", "color": "...", "material": "...", "fit": "..."},
    "bottom": {"type": "...", "color": "...", "fit": "..."},
    "footwear": "...",
    "accessories": ["..."]
  },
  "pose": {
    "position": "...",
    "stance": "...",
    "hands": "...",
    "head_gaze": "...",
    "vibe": "..."
  },
  "scene": {
    "location": "...",
    "time": "...",
    "atmosphere": "...",
    "background": "..."
  },
  "camera": {
    "pov": "...",
    "angle": "...",
    "framing": "..."
  },
  "lighting": {
    "type": "...",
    "effect": "..."
  },
  "mood": {
    "energy": "...",
    "color_palette": "...",
    "aesthetic": "..."
  }
}

Be specific and detailed. Describe what you actually see, not what you assume. Return ONLY valid JSON."""

PATTERN_PROMPT = """You are analyzing {count} top-performing competitor images from social media. Here are their structured descriptions:

{descriptions}

Based on these analyses, produce a JSON summary of visual patterns:

{{
  "dominant_scene_types": ["list of most common scene types"],
  "color_palette_trends": ["list of recurring color themes"],
  "lighting_trends": "one sentence on lighting patterns with percentages",
  "pose_patterns": "one sentence on pose trends across the top images",
  "outfit_trends": "one sentence on outfit/style patterns",
  "style_summary": "2-3 sentence summary of what makes these top images successful",
  "key_insight": "One key actionable insight for our content creation"
}}

Return ONLY valid JSON."""


def load_scout_report(path: str) -> dict:
    """Load and parse scout report JSON."""
    with open(path) as f:
        return json.load(f)


def collect_image_posts(report: dict) -> list[dict]:
    """Extract all posts with photo media, sorted by like_count descending."""
    image_posts = []

    for comp in report.get("competitors", []):
        handle = comp.get("handle", "unknown")
        market = comp.get("market", "unknown")
        followers = comp.get("followers", 0)

        for post in comp.get("recent_posts", []):
            media_list = post.get("media", [])
            photos = [m for m in media_list if m.get("type") == "photo" and m.get("url")]

            if not photos:
                continue

            metrics = post.get("public_metrics", {})
            likes = metrics.get("like_count", 0)

            image_posts.append({
                "handle": handle,
                "market": market,
                "followers": followers,
                "tweet_id": post.get("tweet_id", ""),
                "text": post.get("text", ""),
                "likes": likes,
                "engagement_rate": post.get("engagement_rate", 0),
                "image_url": photos[0]["url"],
                "created_at": post.get("created_at", ""),
            })

    image_posts.sort(key=lambda x: x["likes"], reverse=True)
    return image_posts


def analyze_image(client, image_url: str, max_retries: int = 3) -> dict | None:
    """Call Anthropic Vision API to analyze a single image. Returns parsed JSON or None."""
    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "url", "url": image_url},
                        },
                        {
                            "type": "text",
                            "text": VISION_PROMPT,
                        },
                    ],
                }],
            )

            raw_text = response.content[0].text.strip()
            # Strip markdown fences if present
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                # Remove first and last lines (```json and ```)
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_text = "\n".join(lines)

            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            log.error("Vision response not valid JSON (attempt %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            return None

        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str:
                wait = 10 * attempt
                log.warning("Rate limited (attempt %d/%d), waiting %ds...", attempt, max_retries, wait)
                time.sleep(wait)
                continue
            elif "Could not process image" in error_str or "Could not download image" in error_str:
                log.warning("Image unavailable at URL: %s", image_url)
                return None
            else:
                log.error("Vision API error (attempt %d/%d): %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                return None

    return None


def generate_patterns(client, references: list[dict], max_retries: int = 3) -> dict | None:
    """Call Anthropic API to generate visual pattern summary from all analyses."""
    descriptions = json.dumps([r["analysis"] for r in references], indent=2)
    prompt_text = PATTERN_PROMPT.format(count=len(references), descriptions=descriptions)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt_text}],
            )

            raw_text = response.content[0].text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_text = "\n".join(lines)

            return json.loads(raw_text)

        except json.JSONDecodeError as e:
            log.error("Pattern response not valid JSON (attempt %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            return None

        except Exception as e:
            log.error("Pattern API error (attempt %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            return None

    return None


def mock_analysis(image_url: str) -> dict:
    """Return mock analysis for dry-run mode."""
    return {
        "scene_type": "mirror_selfie",
        "subject": {
            "apparent_age": "early 20s",
            "hair": {"color": "dark brown", "style": "long wavy"},
            "body_type": "hourglass, athletic-toned",
            "skin": "fair, natural texture",
            "expression": "confident smile, direct gaze",
            "makeup": "natural, minimal"
        },
        "outfit": {
            "top": {"type": "crop top", "color": "white", "material": "cotton", "fit": "fitted"},
            "bottom": {"type": "jeans", "color": "blue", "fit": "high-waisted"},
            "footwear": "not visible",
            "accessories": ["phone"]
        },
        "pose": {
            "position": "standing",
            "stance": "slight hip tilt",
            "hands": "one holding phone",
            "head_gaze": "looking at phone screen",
            "vibe": "effortless confidence"
        },
        "scene": {
            "location": "bedroom",
            "time": "afternoon",
            "atmosphere": "warm, casual",
            "background": "white wall, mirror"
        },
        "camera": {
            "pov": "mirror selfie",
            "angle": "eye-level",
            "framing": "full body"
        },
        "lighting": {
            "type": "natural window light",
            "effect": "warm highlights, soft shadows"
        },
        "mood": {
            "energy": "confident, relaxed",
            "color_palette": "warm neutrals, white, brown",
            "aesthetic": "casual influencer"
        }
    }


def mock_patterns(count: int) -> dict:
    """Return mock patterns for dry-run mode."""
    return {
        "dominant_scene_types": ["mirror_selfie", "bedroom_casual"],
        "color_palette_trends": ["warm tones", "soft pink", "natural light", "neutrals"],
        "lighting_trends": f"80% natural light across top {count} images, warm golden tones dominate",
        "pose_patterns": "confident, relaxed stances; direct camera gaze common",
        "outfit_trends": "casual everyday wear outperforms editorial; crop tops and loungewear common",
        "style_summary": f"Top {count} performers use raw iPhone-style mirror selfies with minimal styling, warm natural light, and casual-intimate settings. Studio/editorial shots underperform.",
        "key_insight": "The highest-engagement images feel authentic and unposed. Bedroom/bathroom settings with natural light consistently outperform outdoor and studio shots."
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze competitor images via Claude Vision")
    parser.add_argument("scout_report", help="Path to scout report JSON")
    parser.add_argument("--top", type=int, default=5, help="Number of top images to analyze (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls, use mock output")
    args = parser.parse_args()

    # Load scout report
    log.info("Loading scout report: %s", args.scout_report)
    try:
        report = load_scout_report(args.scout_report)
    except FileNotFoundError:
        log.error("Scout report not found: %s", args.scout_report)
        sys.exit(1)
    except json.JSONDecodeError as e:
        log.error("Invalid JSON in scout report: %s", e)
        sys.exit(1)

    # Collect and rank image posts
    image_posts = collect_image_posts(report)
    log.info("Found %d posts with images", len(image_posts))

    if not image_posts:
        log.warning("No posts with images found in scout report")
        # Write empty references file
        date_str = report.get("date", datetime.now(JST).strftime("%Y-%m-%d"))
        date_compact = date_str.replace("-", "")
        output = {
            "date": date_str,
            "generated_at": datetime.now(JST).isoformat(),
            "scout_report_used": args.scout_report,
            "images_analyzed": 0,
            "visual_patterns": {
                "dominant_scene_types": [],
                "color_palette_trends": [],
                "lighting_trends": "No images available for analysis",
                "pose_patterns": "No images available for analysis",
                "outfit_trends": "No images available for analysis",
                "style_summary": "No competitor images were available in the scout report for analysis.",
                "key_insight": "No data available — consider checking media collection in scout.py"
            },
            "references": []
        }
        output_path = os.path.join("data", "content", f"image_references_{date_compact}.json")
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        log.info("Wrote empty references to %s", output_path)
        sys.exit(0)

    top_posts = image_posts[:args.top]
    log.info("Analyzing top %d images (of %d available)", len(top_posts), len(image_posts))

    # Initialize Anthropic client (or skip for dry-run)
    client = None
    if not args.dry_run:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except ImportError:
            log.error("anthropic package not installed. Run: pip install anthropic")
            sys.exit(1)
        except Exception as e:
            log.error("Failed to initialize Anthropic client: %s", e)
            sys.exit(1)

    # Analyze each image
    references = []
    for i, post in enumerate(top_posts, 1):
        handle = post["handle"]
        tweet_id = post["tweet_id"]
        image_url = post["image_url"]
        log.info("[%d/%d] Analyzing @%s (tweet %s, %d likes): %s",
                 i, len(top_posts), handle, tweet_id, post["likes"], image_url)

        if args.dry_run:
            analysis = mock_analysis(image_url)
        else:
            analysis = analyze_image(client, image_url)

        if analysis is None:
            log.warning("Skipping @%s tweet %s — analysis failed", handle, tweet_id)
            continue

        text_preview = post["text"][:80] if post["text"] else ""
        references.append({
            "source": {
                "handle": f"@{handle}",
                "tweet_id": tweet_id,
                "text_preview": text_preview,
                "likes": post["likes"],
                "engagement_rate": post["engagement_rate"],
                "image_url": image_url,
                "market": post["market"],
            },
            "analysis": analysis,
        })
        log.info("  -> scene_type: %s", analysis.get("scene_type", "unknown"))

    if not references:
        log.warning("All image analyses failed — writing empty references")

    # Generate visual patterns summary
    log.info("Generating visual patterns summary from %d analyses...", len(references))
    if args.dry_run:
        patterns = mock_patterns(len(references))
    elif references:
        patterns = generate_patterns(client, references)
        if patterns is None:
            log.warning("Pattern generation failed — using fallback")
            patterns = {
                "dominant_scene_types": [],
                "color_palette_trends": [],
                "lighting_trends": "Pattern analysis failed",
                "pose_patterns": "Pattern analysis failed",
                "outfit_trends": "Pattern analysis failed",
                "style_summary": "Pattern analysis was not available for this run.",
                "key_insight": "Unable to generate pattern insights — individual references still available."
            }
    else:
        patterns = {
            "dominant_scene_types": [],
            "color_palette_trends": [],
            "lighting_trends": "No successful analyses to derive patterns",
            "pose_patterns": "No successful analyses to derive patterns",
            "outfit_trends": "No successful analyses to derive patterns",
            "style_summary": "No competitor images could be analyzed in this run.",
            "key_insight": "No data available"
        }

    # Build output
    date_str = report.get("date", datetime.now(JST).strftime("%Y-%m-%d"))
    date_compact = date_str.replace("-", "")
    output = {
        "date": date_str,
        "generated_at": datetime.now(JST).isoformat(),
        "scout_report_used": args.scout_report,
        "images_analyzed": len(references),
        "visual_patterns": patterns,
        "references": references,
    }

    # Validate JSON before writing
    try:
        json.dumps(output, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        log.error("Output JSON validation failed: %s", e)
        sys.exit(1)

    output_path = os.path.join("data", "content", f"image_references_{date_compact}.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log.info("Wrote %d image references to %s", len(references), output_path)
    log.info("Done.")


if __name__ == "__main__":
    main()
