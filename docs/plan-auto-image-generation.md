# Plan: Automated Image Generation via Higgsfield

## Problem

The operator manually generates images from pipeline-produced image prompts:
1. Opens Higgsfield web UI
2. Copy-pastes `prompt` + `negative_prompt` from content plan JSON
3. Generates image, waits, downloads
4. Uploads to X when posting

This takes ~15-20 min/day for 4 images and blocks the pipeline from running fully autonomously.

## Approach: Automate the Web UI (No Extra API Cost)

Higgsfield has a separate Cloud API (cloud.higgsfield.ai) but it requires purchasing credits on top of the Pro plan. **We skip the API entirely and automate the web UI instead**, using the existing Pro plan credits.

The operator's current workflow is:
1. Open higgsfield.ai → select Seedream model
2. Paste prompt + negative prompt → set aspect ratio 9:16
3. Click generate → wait → download image

This is a repeatable, mechanical sequence — perfect for browser automation. The agent does exactly what the operator does, but without human hands.

### Cost

| Component | Monthly Cost |
|-----------|-------------|
| Higgsfield Pro (existing, already paying) | $29 |
| Browser Use LLM costs (~120-180 images × ~$0.05-0.15) | ~$6-27 |
| Claude Vision QA (~120-180 images × ~$0.02) | ~$2-4 |
| **Total** | **~$37-60/mo** |

No extra Higgsfield charges. All image generation runs through the existing Pro plan.

## Critical Unknowns (Must Resolve in Step 1)

Before writing the generation script, manually test Browser Use with Higgsfield and confirm:

| Question | Why it matters | Risk if wrong |
|----------|---------------|---------------|
| Can Browser Use reliably fill prompt + negative prompt fields? | Core workflow — if fields can't be filled, nothing works | Need to fall back to Playwright with manual selectors |
| Does Higgsfield detect/block browser automation? | Bot detection could lock the Pro account | May need stealth mode or manual intervention |
| How long does generation take per image? | Determines pipeline time and timeout settings | Pipeline timeouts if too slow |
| Can Browser Use handle the "wait for generation complete" step? | Images take 10-60s to generate — must wait reliably | Premature download attempts, broken images |
| Can Browser Use download the generated image? | Must save the file locally for validation + posting | May need alternative download approach (screenshot + crop, URL extraction) |
| Does cookie persistence work across runs? | Re-login every run wastes time and may trigger security flags | Must handle session management |
| How many credits does one Seedream generation consume? | Pro plan has limited monthly credits | May exhaust credits before month end with regenerations |

## The Character Consistency Problem

**This is the biggest risk in the entire plan.**

Text-to-image models produce a **different person every generation**. There is no "Meruru" in the model's weights. The current manual workflow likely involves the operator:
1. Generating multiple images per prompt
2. Cherry-picking ones that look consistent with the established Meruru aesthetic
3. Possibly using image-to-image with a reference face

Automating this means dealing with high rejection rates. Possible strategies:

### Strategy A: Generate-and-Filter (Simplest)
- Generate 3-4 variations per slot
- Claude Vision scores each for character consistency against a reference image set
- Auto-select the best match, reject if none score above threshold
- **Pro**: No extra tooling. **Con**: Expensive (3-4x image credits), still unreliable.

### Strategy B: Image-to-Image with Reference (If API supports it)
- Upload a "canonical Meruru" reference image alongside the text prompt
- API uses reference for face/body guidance, text prompt for scene/outfit/pose
- **Pro**: Much more consistent. **Con**: Requires img2img API support (unverified).

### Strategy C: Post-Processing Face Swap
- Generate scene/body via text-to-image
- Swap face with a canonical Meruru face using a separate tool (e.g., InsightFace, roop)
- **Pro**: Very consistent faces. **Con**: Extra tooling, uncanny valley risk, ethical concerns.

### Strategy D: Fine-Tuned Model / LoRA
- Train a LoRA on Meruru's established look
- Use it with Seedream or FLUX for consistent character
- **Pro**: Best consistency. **Con**: Requires training infra, model hosting, significant effort.

**Recommendation**: Start with **Strategy A** (generate-and-filter). Test rejection rate. If >50% images rejected for character inconsistency, escalate to Strategy B or C.

## Architecture Decision: Browser Automation Tool

All options automate the Higgsfield web UI using the existing Pro plan. No API credits needed.

### Option A: Browser Use CLI (RECOMMENDED)
- **Pro**: AI-assisted element detection — adapts when UI changes without code updates
- **Pro**: No CSS selector maintenance — elements found by description
- **Pro**: Persistent browser sessions with cookie management
- **Pro**: Can combine deterministic commands (index-based clicks) with AI fallback
- **Con**: LLM costs for AI-driven mode (~$0.05-0.15/image)
- **Con**: Newer project, less battle-tested than Playwright
- **Cost**: ~$6-27/mo LLM costs

### Option B: Playwright
- **Pro**: Zero LLM cost — purely deterministic
- **Pro**: Fast, mature, excellent documentation
- **Con**: Brittle — breaks every time Higgsfield changes their UI
- **Con**: Must manually maintain CSS selectors
- **Con**: Cannot adapt to unexpected popups, layout changes, CAPTCHAs
- **Cost**: $0/mo (but maintenance time when UI changes)

### Option C: Claude Computer Use
- **Pro**: Highest adaptability — Claude sees the screen and reasons about it
- **Con**: $0.50-5.00 per image — way too expensive for daily use
- **Con**: Slowest option, beta feature
- **Cost**: $60-600/mo — not viable

**Decision**: **Option A (Browser Use CLI)**. The AI-assisted element detection is the key advantage — when Higgsfield changes their UI (and they will), Browser Use adapts automatically instead of breaking. Playwright is the fallback if Browser Use proves unreliable, but the maintenance burden of Playwright selectors makes it a worse long-term choice.

## Pipeline Integration

### Current Flow
```
orchestrator.py pipeline
  Step 0: analyze_references.py          # Analyze new ref images
  Step 1: claude -p Strategist (opus)    # Strategy + creative briefs
  Step 2: validate.py strategist         # Validate strategy
  Step 3: claude -p Creator (sonnet)     # Content plan + image prompts
  Step 4: validate.py creator            # Validate content plan
  Step 5: claude -p Marc Review (opus)   # Strategic review
  → Operator manually generates images from prompts
  → Operator manually posts to X
```

### Proposed Flow
```
orchestrator.py pipeline
  Step 0: analyze_references.py          # Analyze new ref images
  Step 1: claude -p Strategist (opus)    # Strategy + creative briefs
  Step 2: validate.py strategist         # Validate strategy
  Step 3: claude -p Creator (sonnet)     # Content plan + image prompts
  Step 4: validate.py creator            # Validate content plan
  Step 5: generate_images.py             # NEW — generate via Higgsfield API
  Step 6: validate_images.py             # NEW — Claude Vision quality check
  Step 5-6 RETRY LOOP (max 2 retries per slot for rejected images)
  Step 7: claude -p Marc Review (opus)   # Strategic review (now includes image status)
  → Operator reviews images in Telegram (approve/reject/regenerate)
  → Operator posts to X (or future: auto-post approved images)
```

### Generate-Validate-Retry Loop

```python
MAX_RETRIES = 2

for acct in accounts:
    plan_path = f"data/content/content_plan_{date}_{acct}.json"

    for attempt in range(MAX_RETRIES + 1):
        # Generate images for slots without accepted images
        run_script(f"python3 scripts/generate_images.py {plan_path}")

        # Validate via Claude Vision
        run_script(f"python3 scripts/validate_images.py {plan_path}")

        # Check if any slots still rejected
        plan = load_json(plan_path)
        rejected = [p for p in plan["posts"] if p.get("image_status") == "rejected"]
        if not rejected:
            break
        if attempt < MAX_RETRIES:
            logger.info(f"{len(rejected)} images rejected, retrying (attempt {attempt + 2}/{MAX_RETRIES + 1})")

    # After all retries, any still-rejected slots → notify operator
    final_rejected = [p for p in plan["posts"] if p.get("image_status") == "rejected"]
    if final_rejected:
        slots = [p["slot"] for p in final_rejected]
        send_telegram(f"Image generation: {len(final_rejected)} slots failed after {MAX_RETRIES + 1} attempts: {slots}. Manual generation needed.")
```

### Graceful Degradation

When image generation fails (API down, no credits, all retries exhausted):
1. Pipeline continues — content plan still has full image prompts
2. Marc Review reports which slots need manual image generation
3. Telegram message includes the prompts for manual copy-paste into Higgsfield web UI
4. Operator can use `/regenerate N` later when issue is resolved
5. **The pipeline never blocks on image generation failure**

## Implementation Plan

### Phase 1: Browser Use CLI Setup & Web UI Mapping

**Manual testing checklist:**

- [ ] `pip install browser-use && browser-use install`
- [ ] Open Higgsfield web UI: `browser-use open https://higgsfield.ai`
- [ ] Log in with existing Pro account (handle auth/cookies)
- [ ] Run `browser-use state` to get element indices for the image generation page
- [ ] Map the web UI elements:
  - Model selector (Seedream v4)
  - Prompt text field
  - Negative prompt field (if visible — some UIs hide it behind "Advanced")
  - Aspect ratio selector (9:16)
  - Generate button
  - Download button (appears after generation completes)
- [ ] Script the full flow: open → select model → fill prompt → fill negative prompt → set aspect ratio → generate → wait → download
- [ ] Test with one of our actual prompts (120-180 words)
- [ ] Test with 4 sequential generations — measure time + reliability
- [ ] Test cookie persistence: close browser, reopen, verify still logged in
- [ ] Verify downloaded image quality matches manual generation
- [ ] Check how many Pro plan credits one generation consumes

**Decision gate**: If Browser Use has >30% failure rate or takes >5 min for 4 images, fall back to Playwright with hardcoded selectors.

### Phase 1B: Playwright Fallback (only if Browser Use is unreliable)

- [ ] `npm init playwright@latest`
- [ ] Inspect Higgsfield web UI with DevTools — record CSS selectors for each element
- [ ] Script the same flow with Playwright's `page.fill()`, `page.click()`, `page.waitForSelector()`
- [ ] Handle auth via saved browser context (`storageState`)
- [ ] Note: selectors will need updating whenever Higgsfield changes their UI

### Phase 2: Core Image Generation Script

**New file: `scripts/generate_images.py`**

```
Usage:
    python3 scripts/generate_images.py data/content/content_plan_20260326_EN.json
    python3 scripts/generate_images.py --slot 2 data/content/content_plan_20260326_EN.json
    python3 scripts/generate_images.py --regenerate 3 data/content/content_plan_20260326_EN.json
    python3 scripts/generate_images.py --variations 1 data/content/content_plan_20260326_EN.json
```

Responsibilities:
1. Read content plan JSON
2. For each post needing an image (`status: "draft"` and no `image_path`, or `image_status: "rejected"`):
   a. Extract `prompt`, `negative_prompt`, `aspect_ratio` from `image_prompt`
   b. Call Higgsfield via Browser Use CLI (or API if Phase 1B):
      - Open web UI, select Seedream model
      - Fill prompt field, fill negative prompt field
      - Set aspect ratio to 9:16
      - Click generate, wait for result
      - Download generated image
   c. Save to `media/generated/{post_id}.png`
   d. Compress to <2MB with Pillow if needed
   e. Update content plan JSON: `image_path`, `image_generated_at`, `image_status: "generated"`
3. Support `--slot N` for single-slot generation
4. Support `--regenerate N` to re-generate a rejected image (new seed)
5. Support `--variations N` to generate 3 variants for slot N

**Browser Use workflow per image:**
```python
def generate_one_image(prompt: str, negative_prompt: str, aspect_ratio: str, output_path: str):
    """Generate a single image via Browser Use CLI on Higgsfield web UI."""
    # Ensure browser is open and logged in
    subprocess.run(["browser-use", "open", "https://higgsfield.ai/image-generator"])

    # Select model (Seedream v4)
    subprocess.run(["browser-use", "click", MODEL_SELECTOR_INDEX])

    # Fill prompt
    subprocess.run(["browser-use", "input", PROMPT_FIELD_INDEX, prompt])

    # Fill negative prompt
    subprocess.run(["browser-use", "input", NEG_PROMPT_FIELD_INDEX, negative_prompt])

    # Set aspect ratio
    subprocess.run(["browser-use", "click", ASPECT_RATIO_INDEX])  # 9:16

    # Generate
    subprocess.run(["browser-use", "click", GENERATE_BUTTON_INDEX])

    # Wait for result
    subprocess.run(["browser-use", "wait", "--text", "Download", "--timeout", "120"])

    # Download
    subprocess.run(["browser-use", "click", DOWNLOAD_BUTTON_INDEX])
    # Move downloaded file to output_path
```

**Note**: Element indices will be discovered during Phase 1 testing and may need periodic updates if Higgsfield changes their UI. Browser Use's AI mode can auto-discover elements as fallback.

**Content plan JSON additions per post:**
```json
{
  "image_path": "media/generated/EN_20260326_01.png",
  "image_generated_at": "2026-03-26T10:30:00+09:00",
  "image_status": "generated",
  "image_credits_used": 1,
  "image_variations": [
    "media/generated/EN_20260326_01_v1.png",
    "media/generated/EN_20260326_01_v2.png",
    "media/generated/EN_20260326_01_v3.png"
  ]
}
```

**Session & credit monitoring:**
```python
def check_session():
    """Verify Higgsfield web session is still valid before generating."""
    # Check if browser session is logged in
    # If session expired: attempt re-login with stored credentials
    # If re-login fails: alert operator, skip image gen

def check_credits_remaining():
    """Scrape remaining Pro plan credits from Higgsfield dashboard."""
    # Navigate to account/billing page
    # Extract remaining credits
    # If <20% remaining: send Telegram warning
    # If 0 remaining: skip image gen, notify operator
```

### Phase 3: Image Quality Validation (Claude Vision)

**New file: `scripts/validate_images.py`**

```
Usage:
    python3 scripts/validate_images.py data/content/content_plan_20260326_EN.json
```

Responsibilities:
1. For each post with `image_status: "generated"`:
   a. Load generated image + a canonical Meruru reference image
   b. Call `claude -p` with both images (vision) to check:
      - Character consistency vs reference (does she look like Meruru?)
      - No visible text, letters, logos, watermarks
      - Expression matches approved list (no teeth-showing)
      - Outfit matches the prompt description
      - Scene matches the prompt description
      - No artifacts, distortion, extra limbs, bad hands
      - Overall photorealistic quality (iPhone candid feel, not editorial)
   c. Output: quality score (0-100), pass/fail, specific issues list
   d. Update content plan: `image_quality_score`, `image_quality_issues`
   e. Score <60 → `image_status: "rejected"` with reason
   f. Score 60-79 → `image_status: "generated"` with warning (operator decides)
   g. Score ≥80 → `image_status: "accepted"`
2. Rejected images trigger retry in the pipeline loop

**Quality check prompt:**
```
You are reviewing a generated image for quality. Compare it against the reference image of the character "Meruru" (provided).

Check these criteria (score each 0-10):
1. FACE MATCH: Does the subject's face resemble the reference? (age ~21, Japanese, dark hair)
2. BODY MATCH: Does the body match? (hourglass, fit, proportions consistent with reference)
3. NO TEXT: No visible text, letters, numbers, logos, watermarks, typography anywhere?
4. EXPRESSION: No teeth showing, no open mouth smile? (approved: subtle smirk, lips parted, neutral gaze, soft pout)
5. ANATOMY: No extra limbs, distorted hands, extra fingers, artifacts?
6. SCENE ACCURACY: Does the scene match: {scene_description}?
7. OUTFIT ACCURACY: Does the outfit match: {outfit_description}?
8. REALISM: Does it look like an iPhone candid photo? (not editorial, not AI-looking)
9. COMPOSITION: Good framing, no awkward crops, subject is the focus?
10. OVERALL: Would this pass as a real social media photo at first glance?

Output JSON:
{
  "scores": {"face_match": N, "body_match": N, ...},
  "total_score": N,
  "pass": true/false,
  "issues": ["specific issue 1", "specific issue 2"],
  "recommendation": "accept" | "reject" | "borderline"
}
```

**Canonical reference**: Store 3-5 "best of" Meruru images in `media/reference/canonical/` for validation comparison.

### Phase 4: Telegram Integration

**Updates to `scripts/telegram_bot.py`:**

1. **Image preview**: After pipeline, send each generated image as a Telegram photo with caption + quality score
2. **`/approve N`**: Approve slot N's image (sets `image_status: "approved"`)
3. **`/reject N [reason]`**: Reject slot N → triggers regeneration
4. **`/regenerate N`**: Re-generate image for slot N (new seed, same prompt)
5. **`/variations N`**: Generate 3 variations for slot N, send as Telegram album for operator to pick

### Phase 5: Orchestrator Integration

**Updates to `scripts/orchestrator.py`:**

Add Steps 5-6 with retry loop after Creator validation (see "Generate-Validate-Retry Loop" above).

## File Storage

```
media/
  reference/            # Operator-curated reference images (existing)
    canonical/          # NEW — 3-5 "best" Meruru images for validation comparison
  generated/            # NEW — Auto-generated images from Higgsfield
    EN_20260326_01.png
    EN_20260326_01_v1.png
    EN_20260326_01_v2.png
    EN_20260326_02.png
    ...
```

- Add `media/generated/` to `.gitignore` (images are large, regenerable)
- Auto-cleanup images older than 7 days
- Canonical reference images are checked into git (small set, essential for validation)

## Cost Estimate

| Component | Monthly Cost |
|-----------|-------------|
| Higgsfield Pro (already paying) | $29 |
| Browser Use LLM costs (~120-180 images × ~$0.05-0.15) | ~$6-27 |
| Claude Vision QA (~120-180 images × ~$0.02) | ~$2-4 |
| **Total** | **~$37-60/mo** |
| **Extra cost vs. today** | **~$8-31/mo** (only LLM costs are new) |

vs. operator time saved: ~15-20 min/day × 30 days = 7.5-10 hours/month

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Character inconsistency (different face every generation) | HIGH | Generate-and-filter with Claude Vision. Escalate to img2img/face-swap if rejection rate >50%. |
| Higgsfield bot detection blocks Browser Use | HIGH | Use stealth mode / headful browser. If blocked, fall back to Playwright. Worst case: operator generates manually (current workflow). |
| Browser Use fails on Higgsfield UI changes | MEDIUM | AI mode auto-discovers elements. If persistent, remap indices. Fall back to Playwright selectors. |
| Higgsfield login/session expires during generation | MEDIUM | Cookie persistence. Auto re-login flow. Alert operator if auth fails repeatedly. |
| Pro plan credits exhausted mid-month | MEDIUM | Monitor via dashboard scrape. Alert at low balance. Reduce regeneration attempts near month end. |
| Browser Use too slow (>5 min for 4 images) | MEDIUM | Optimize: skip AI mode for known elements, use index-based commands. Fall back to Playwright for speed. |
| Generated images >2MB | LOW | Auto-compress with Pillow. |
| Higgsfield downtime | LOW | Non-fatal pipeline step. Operator gets prompts for manual generation. |

## Prerequisites Before Starting

1. Higgsfield Pro account (already have)
2. `pip install browser-use Pillow && browser-use install`
3. **Step 1 is mandatory** — test Browser Use with Higgsfield web UI before writing the generation script
4. Operator selects 3-5 "canonical Meruru" reference images for `media/reference/canonical/` (needed for Phase 4)

## Implementation Order

| Step | What | Effort | Depends On |
|------|------|--------|-----------|
| 1 | **Browser Use CLI setup** — install, map Higgsfield web UI elements, test 4 images | 3-4 hours | Pro account |
| 1-gate | **Go/no-go**: Is Browser Use reliable? (<30% failure, <5 min for 4 images) | 15 min | Step 1 |
| 1B | (If Browser Use fails) **Playwright fallback** — inspect selectors, script flow | 3-4 hours | Step 1 results |
| 2 | `generate_images.py` — core generation script wrapping Browser Use | 3-4 hours | Step 1 |
| 3 | Select canonical Meruru references for validation | 30 min | Operator |
| 4 | `validate_images.py` — Claude Vision QA | 3 hours | Step 2 |
| 5 | Orchestrator integration (retry loop) | 1 hour | Steps 2+4 |
| 6 | Telegram preview + approve/reject/regenerate | 3 hours | Step 5 |
| 7 | Session/credit monitoring + graceful degradation | 1 hour | Step 2 |

**Total: ~15-17 hours.**

## Success Criteria

1. Pipeline generates 4 images automatically with <50% rejection rate
2. Claude Vision validation catches >80% of quality issues (character drift, artifacts, text in image)
3. Rejected images auto-retry up to 2 times before escalating to operator
4. Operator reviews final images via Telegram photos and approves/rejects
5. When image gen fails entirely, operator gets prompts for manual generation (graceful degradation)
6. End-to-end pipeline time: <20 min (currently ~12 min without images)
7. Credit usage stays within plan limits with monitoring alerts at 80%
