# Higgsfield SeedREAM — Image Prompt Guide

## Overview

- **Tool**: Higgsfield SeedREAM (`higgsfield`)
- **Output**: Both a structured JSON object AND a flat `prompt` paragraph (120-180 words — NOT 250+)
- The structured fields ensure nothing is missed; the `prompt` text is what gets pasted into Higgsfield
- All prompts must achieve ultra photorealistic quality — the goal is images indistinguishable from real iPhone photos

## Competitor-Aligned Style Rules (MANDATORY — from gap analysis 2026-03-16)

These rules override any conflicting guidance in the scene templates below. They are based on real competitor engagement data.

### 1. iPhone Camera ONLY
- Use `"camera": "iPhone 15 Pro Max"` and `"lens": "24mm wide"` for ALL slots, ALL categories
- NEVER use Sony, Canon, or any DSLR/mirrorless camera spec — it produces polished editorial output that doesn't match this niche
- `meta.style` must use casual terms: "raw iphone selfie", "casual mirror pic", "candid phone photo"
- NEVER use the word "editorial" in any style label — it primes the AI for magazine-quality output

### 2. Simple Scenes (Max 2-3 Background Elements)
- The SUBJECT is the focus, not the environment
- Max 2-3 background props per scene (e.g., "white wall, unmade bed" — done)
- Remove architectural details, ornamental plants, terracotta tiles, gallery courtyards
- Winning settings: bedroom, bathroom, gym, beach — simple everyday spaces

### 3. High-Engagement Scene Types (Rotate These)
These are the scenes that drive the highest engagement among competitors:

| Scene Type | Examples | Engagement Signal |
|---|---|---|
| **Bedroom mirror selfie** | @sessypuuh (34.8% ER), @HannaJonso | Highest ER% category |
| **Bathroom/post-shower** | @yuumispm (16.4% ER) | Intimate, casual aesthetic |
| **Beach/pool/bikini** | @tanarainw (21.7K likes), @LeahSunkissed | Highest absolute likes |
| **Gym/fitness** | @imrubyreid (33.7K likes) | Body-confidence content |
| **Cozy bedroom casual** | @Angelwithcakee, @lucidevlinxyz | Girl-next-door relatability |

Low-performing scenes to AVOID in regular rotation: rooftop terrace, urban park/gallery, professional studio, Tokyo street scenes.

### 4. Simple Outfits (Body > Fashion)
- Default to casual, body-revealing basics: sports bra + leggings, bikini, crop top + shorts, oversized tee, simple bodysuit, loungewear
- The outfit should complement the figure, not compete for visual attention
- AVOID fashion-magazine outfit specs (no "cream linen button-down midi dress with thin gold belt")
- Save fashion outfits for occasional variety (max 1 in 4 posts)

### 5. Lighting = 1 Sentence Max
- "Natural window light" or "warm room lighting" — that's enough
- NEVER describe multi-source lighting with shadow mapping
- Over-specifying lighting makes AI generators produce unnatural studio-lit results

### 6. Prompt Length = 120-180 Words Max
- Image generation models have attention limits — every additional detail dilutes focus
- Prioritize: subject (locked traits) > outfit (simple) > pose (vibe) > scene (location + 2 props) > lighting (1 sentence)
- If your prompt exceeds 180 words, cut background props and lighting details first

## Fixed Character Profiles

These profiles are **locked** — use these exact traits for every post on the respective account. Do NOT vary age, body type, or core physical traits between posts. Hair color/style and outfit change per post, but the underlying character is always the same person.

### EN Account Character (Meruru)

- **Age**: Early 20s
- **Ethnicity**: Japanese
- **Hair**: Dark/jet-black or dark brown, long straight or wavy (style varies per post, color stays dark)
- **Body**: Extreme hourglass figure, fit and toned
- **Bust**: Large, full, heavy volume
- **Waist**: Ultra-slim, snatched, high contrast between waist and hips
- **Hips**: Extra wide, voluptuous, muscular and round
- **Glutes**: Highly emphasized, large and rounded buttocks
- **Skin**: Light-medium neutral, smooth
- **Face**: Naturally attractive, expressive features
- **Expression rule**: No teeth-showing smiles. ONLY permitted terms: "closed-mouth smile", "subtle smirk", "lips softly closed", "lips slightly parted", "neutral gaze", "soft pout". NEVER use "bright smile" — image generators interpret this as teeth-showing.
- **Makeup**: Minimal — natural brows, soft lip
- **Persona**: Real influencer feel — confident, playful, casually flirty. Never reveals AI nature. "Cute but Deadly" — effortlessly charming, quietly strategic.

### JP Account Character

- **Age**: Early 20s
- **Ethnicity**: Japanese / East Asian
- **Hair**: Dark (black or dark brown), long, straight or soft waves
- **Body**: Extreme hourglass figure, fit and toned
- **Bust**: Large, full, heavy volume
- **Waist**: Ultra-slim, snatched, high contrast between waist and hips
- **Hips**: Extra wide, voluptuous, muscular and round
- **Glutes**: Highly emphasized, large and rounded buttocks
- **Skin**: Fair porcelain, smooth, natural glow
- **Face**: Delicate features, almond-shaped eyes, natural Korean-style makeup
- **Persona**: Warm, authentic, intimate. Natural Japanese social media style.

---

## Prompt Schema (JSON structure)

Each `image_prompt` object must contain these structured fields:

```
meta:
  quality      — always "ultra photorealistic"
  camera       — ALWAYS "iPhone 15 Pro Max" (see Competitor-Aligned Style Rules above)
  lens         — ALWAYS "24mm wide"
  style        — casual terms ONLY: "raw iphone selfie", "casual mirror pic", "candid phone photo" (NEVER "editorial")

subject:
  (from fixed character profile — do NOT deviate)
  hair         — { color, style } — varies per post
  body_type    — from profile (locked)
  skin         — from profile (locked)
  expression   — e.g., "confident subtle smile", "neutral focused gaze", "playful smirk"
  makeup       — e.g., "natural Korean-style, dewy skin, subtle lip tint", "bold red lip, winged liner"

outfit:
  top          — { type, color, material, fit, details }
  bottom       — { type, color, fit } (omit if dress/one-piece)
  footwear     — (if visible in frame)
  accessories  — [ jewelry, tech devices, hair accessories, sunglasses, etc. ]

pose:
  position     — standing, sitting, lying, kneeling, leaning
  stance       — weight distribution, hip angle, body arch, lean direction
  hands        — specific per hand (e.g., "left hand holding phone, right hand on hip")
  head_gaze    — tilt direction + where eyes look (e.g., "slight right tilt, eyes at phone screen")
  vibe         — overall energy word (e.g., "effortless confidence", "relaxed intimacy", "playful energy")

scene:
  location     — specific place (e.g., "modern minimalist bedroom", "luxury hotel bathroom")
  time         — time of day (e.g., "golden hour", "midday", "evening")
  atmosphere   — mood word (e.g., "warm domestic", "steamy intimate", "bright energetic")
  background   — specific elements (e.g., "white wall, black-framed full-length mirror, grey carpet, unmade bed")

camera:
  pov          — mirror selfie, front camera selfie, third-person, over-shoulder, etc.
  angle        — eye-level, slightly low angle, high angle, dutch angle
  framing      — full body, three-quarter, medium shot, close-up, waist-up
  composition  — centering notes, vertical orientation, rule of thirds

lighting:
  type         — natural sunlight / artificial warm lamp / mixed / ring light / studio softbox
  direction    — from left window, overhead, behind subject, frontal
  effect       — warm highlights, sharp window shadows, soft diffused glow, rim lighting, lens flare

mood:
  energy       — quiet / bold / playful / intimate / confident
  color_palette — 3-5 dominant colors (e.g., "soft pink, clean white, warm gold")
  aesthetic    — one-line style description (e.g., "casual luxury influencer aesthetic")
```

---

## Scene Templates

### 1. Mirror Selfie

```json
{
    "prompt": "Ultra photorealistic raw iPhone mirror selfie of a young woman in her early 20s standing in a modern minimalist bedroom. She has long dark brown hair falling past her shoulders in soft natural waves. Hourglass athletic-toned figure with natural skin texture and visible pores. She wears a fitted white ribbed crop top and high-waisted black yoga pants that hug her curves. One hand holds an iPhone 15 Pro Max at chest height, the other rests casually on her hip with fingers slightly spread. Her weight shifts to her left leg creating a subtle hip tilt. She gazes at the phone screen with a relaxed confident expression and soft natural smile. Slight head tilt to the right. The room has a clean white wall behind a large black-framed full-length mirror, grey carpet, and a neatly made bed with white linens visible in the background. Natural golden hour sunlight streams from a window to the left, casting warm highlights across her skin and soft directional shadows on the wall. The lighting creates a warm glow on her face and arms. Soft pink, clean white, warm gold color palette. Casual everyday influencer aesthetic. Shot at eye-level in portrait orientation, centered composition. Photorealistic, high quality, high resolution, 9:16 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "9:16",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "raw iphone mirror selfie"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long soft natural waves"},
    "body_type": "hourglass, athletic-toned",
    "skin": "natural texture, visible pores",
    "expression": "relaxed confident, soft natural smile",
    "makeup": "minimal natural, dewy skin"
  },
  "outfit": {
    "top": {"type": "crop top", "color": "white", "material": "ribbed cotton", "fit": "fitted", "details": "ribbed texture"},
    "bottom": {"type": "yoga pants", "color": "black", "fit": "high-waisted, fitted"},
    "accessories": ["iPhone 15 Pro Max"]
  },
  "pose": {
    "position": "standing",
    "stance": "weight on left leg, subtle hip tilt right",
    "hands": "right hand holding phone at chest height, left hand on hip",
    "head_gaze": "slight right tilt, eyes at phone screen",
    "vibe": "effortless confidence"
  },
  "scene": {
    "location": "modern minimalist bedroom",
    "time": "golden hour",
    "atmosphere": "warm, clean, domestic",
    "background": "white wall, black-framed full-length mirror, grey carpet, white bed linens"
  },
  "camera": {
    "pov": "mirror selfie",
    "angle": "eye-level",
    "framing": "full body"
  },
  "lighting": {
    "type": "natural golden hour sunlight from left window",
    "effect": "warm highlights on skin, soft directional shadows on wall"
  },
  "mood": {
    "energy": "confident, casual",
    "color_palette": "soft pink, clean white, warm gold",
    "aesthetic": "casual everyday influencer"
  }
}
```

#### Sub-variants (Bedroom Mirror)
- **Clean minimalist**: white wall, made bed, morning golden hour light
- **Cozy messy bed**: rumpled duvet, pillows, warm evening lamp light
- **Hotel room**: hotel decor, neutral tones, warm recessed lighting
- **Getting-ready vanity**: vanity table with products, warm ring light glow

### 2. Bathroom / Post-shower

```json
{
    "prompt": "Ultra photorealistic photo of a young Japanese woman in her early 20s in a modern luxury hotel bathroom just after a shower. She has long straight black hair, wet and clinging to her shoulders and back with water droplets visible. Fair porcelain skin with a natural dewy glow, smooth with subtle water drops on her collarbones and shoulders. Hourglass figure with full curves. She wears a plush oversized white hotel towel wrapped around her torso, tucked above her chest, the towel ending at upper thigh. Delicate features with almond-shaped eyes and natural Korean-style makeup — subtle brow, light mascara, dewy skin finish, soft pink lip tint. She stands facing a large frameless bathroom mirror, holding her phone with both hands at face level, taking a selfie with a warm intimate expression, lips slightly parted, soft gaze at the screen. Slight forward lean toward the mirror. The bathroom has white marble countertop with chrome fixtures, warm recessed lighting overhead, a frosted glass shower door behind her with visible steam wisps, folded grey towels on the counter. Warm artificial lighting from above creates a soft diffused glow on her wet skin, highlights the water droplets, and produces gentle shadows under her jawline. Warm ivory, soft white, chrome silver color palette. Intimate post-shower aesthetic. Shot from mirror reflection POV, slightly low angle, medium shot waist-up, centered composition. Photorealistic, high quality, high resolution, 4:5 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "intimate bathroom mirror selfie"
  },
  "subject": {
    "hair": {"color": "black", "style": "long straight, wet, clinging to shoulders"},
    "body_type": "hourglass figure, full curves",
    "skin": "fair porcelain, dewy glow, water droplets",
    "expression": "warm intimate, lips slightly parted, soft gaze",
    "makeup": "natural Korean-style, subtle brow, light mascara, dewy finish, soft pink lip tint"
  },
  "outfit": {
    "top": {"type": "hotel towel wrap", "color": "white", "material": "plush terry cloth", "fit": "wrapped, tucked above chest", "details": "ending at upper thigh"},
    "accessories": ["iPhone"]
  },
  "pose": {
    "position": "standing",
    "stance": "slight forward lean toward mirror",
    "hands": "both hands holding phone at face level",
    "head_gaze": "facing mirror, soft gaze at phone screen",
    "vibe": "relaxed intimacy"
  },
  "scene": {
    "location": "luxury hotel bathroom",
    "time": "evening",
    "atmosphere": "steamy, warm, intimate",
    "background": "white marble countertop, chrome fixtures, frosted glass shower door, steam wisps, folded grey towels"
  },
  "camera": {
    "pov": "mirror selfie",
    "angle": "slightly low angle",
    "framing": "medium shot, waist-up"
  },
  "lighting": {
    "type": "warm recessed artificial lighting from above",
    "effect": "soft diffused glow on wet skin, highlights water droplets, gentle shadow under jawline"
  },
  "mood": {
    "energy": "intimate, quiet",
    "color_palette": "warm ivory, soft white, chrome silver",
    "aesthetic": "intimate post-shower luxury"
  }
}
```

#### Sub-variants (Bathroom)
- **Home bathroom**: simple white tiles, basic mirror, everyday feel
- **Hotel luxury marble**: marble countertop, chrome fixtures, plush towels
- **Simple steamy minimal**: frosted glass, steam wisps, minimal background

### 3. Pool / Beach / Outdoor

```json
{
    "prompt": "Ultra photorealistic raw iPhone photo of a young woman in her early 20s at the beach. She has long dark brown hair slightly tousled by the wind. Fitness hourglass figure with light-medium skin glistening with sunscreen. She wears a simple black bikini. She stands in shallow water at the shoreline, one hand pushing hair back from her face, the other at her side. Weight on one hip, relaxed confident pose. She looks at the camera with a playful smirk. Sandy beach and blue ocean behind her. Bright natural sunlight. Warm bronze, ocean blue, clean white color palette. Casual beach selfie aesthetic. Full body, eye-level, 4:5 portrait. Photorealistic, high quality, high resolution.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "casual beach photo"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long, tousled by wind"},
    "body_type": "fitness hourglass",
    "skin": "light-medium, glistening with sunscreen",
    "expression": "playful smirk, confident",
    "makeup": "minimal, natural sun-flushed look"
  },
  "outfit": {
    "top": {"type": "bikini top", "color": "black", "fit": "simple triangle"},
    "bottom": {"type": "bikini bottoms", "color": "black", "fit": "simple"},
    "accessories": []
  },
  "pose": {
    "position": "standing in shallow water",
    "stance": "weight on one hip, relaxed",
    "hands": "one hand pushing hair back, other at side",
    "head_gaze": "looking at camera",
    "vibe": "playful confidence"
  },
  "scene": {
    "location": "beach shoreline",
    "time": "midday",
    "atmosphere": "bright, warm, natural",
    "background": "sandy beach, blue ocean"
  },
  "camera": {
    "pov": "friend-took-this-photo",
    "angle": "eye-level",
    "framing": "full body"
  },
  "lighting": {
    "type": "bright natural sunlight",
    "effect": "warm highlights on skin"
  },
  "mood": {
    "energy": "playful, carefree",
    "color_palette": "warm bronze, ocean blue, clean white",
    "aesthetic": "casual beach photo"
  }
}
```

#### Sub-variants (Beach / Pool)
- **Shoreline standing**: feet in shallow water, ocean behind, midday sun
- **Poolside lounging**: pool edge or lounge chair, bright natural light
- **Sitting on sand**: beach towel or bare sand, relaxed golden hour
- **Shallow water wading**: knee-deep, water splashing, playful energy

### 4. Bedroom / Indoor Casual

```json
{
    "prompt": "Ultra photorealistic raw iPhone photo of a young Japanese woman in her early 20s sitting on her unmade bed. Long straight dark brown hair draped over one shoulder. Fitness hourglass figure, light-medium smooth skin. She wears an oversized white tee and black shorts, casual and relaxed. She sits cross-legged on rumpled white sheets, leaning forward with chin resting on one hand. She looks at the camera with a warm smile, soft eyes. Simple bedroom — white wall, unmade bed with white sheets. Warm natural light from a window. Cozy, intimate, everyday. Medium shot, eye-level, 4:5 portrait. Photorealistic, high quality, high resolution.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "casual bedroom photo"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long straight, draped over one shoulder"},
    "body_type": "fitness hourglass",
    "skin": "light-medium, smooth",
    "expression": "warm smile, soft eyes",
    "makeup": "minimal natural"
  },
  "outfit": {
    "top": {"type": "oversized tee", "color": "white", "fit": "oversized, casual"},
    "bottom": {"type": "shorts", "color": "black", "fit": "simple"},
    "accessories": []
  },
  "pose": {
    "position": "sitting cross-legged on bed",
    "stance": "leaning forward slightly",
    "hands": "chin resting on one hand",
    "head_gaze": "facing camera, warm gaze",
    "vibe": "cozy warmth"
  },
  "scene": {
    "location": "bedroom",
    "time": "afternoon",
    "atmosphere": "warm, cozy, everyday",
    "background": "white wall, unmade bed with white sheets"
  },
  "camera": {
    "pov": "friend-took-this-photo",
    "angle": "eye-level",
    "framing": "medium shot, waist-up"
  },
  "lighting": {
    "type": "warm natural window light",
    "effect": "soft warm tones on face"
  },
  "mood": {
    "energy": "quiet, intimate",
    "color_palette": "warm white, soft neutrals",
    "aesthetic": "casual everyday bedroom"
  }
}
```

#### Sub-variants (Bedroom Casual)
- **Sitting on bed**: cross-legged on rumpled sheets, warm window light
- **Couch lounging**: soft cushions, blanket, cozy evening vibe
- **Floor sitting**: cross-legged on carpet/rug, relaxed intimate feel

### 5. Gym / Fitness

```json
{
    "prompt": "Ultra photorealistic raw iPhone mirror selfie of a young woman in her early 20s at the gym. Long dark brown hair in a high ponytail, slightly sweaty. Fitness hourglass figure with toned arms and visible abs, light-medium skin with a natural post-workout flush. She wears a black sports bra and grey high-waisted leggings. She holds her iPhone at chest height in a gym mirror, other hand on hip. Confident expression, slight smirk, looking at phone screen. Gym mirror with weight rack visible behind her. Bright gym fluorescent lighting. Dark, grey, warm skin tones. Raw gym selfie aesthetic. Full body, eye-level, 9:16 portrait. Photorealistic, high quality, high resolution.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "9:16",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "raw gym mirror selfie"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "high ponytail, slightly sweaty"},
    "body_type": "fitness hourglass, toned arms, visible abs",
    "skin": "light-medium, post-workout flush",
    "expression": "confident smirk",
    "makeup": "minimal, natural"
  },
  "outfit": {
    "top": {"type": "sports bra", "color": "black", "fit": "fitted"},
    "bottom": {"type": "leggings", "color": "grey", "fit": "high-waisted"},
    "accessories": ["iPhone 15 Pro Max"]
  },
  "pose": {
    "position": "standing",
    "stance": "weight on one hip, confident curve",
    "hands": "one hand holding phone at chest, other on hip",
    "head_gaze": "looking at phone screen, slight smirk",
    "vibe": "post-workout confidence"
  },
  "scene": {
    "location": "gym",
    "time": "anytime",
    "atmosphere": "energetic, casual",
    "background": "gym mirror, weight rack"
  },
  "camera": {
    "pov": "mirror selfie",
    "angle": "eye-level",
    "framing": "full body"
  },
  "lighting": {
    "type": "bright gym fluorescent lighting",
    "effect": "even illumination, highlights muscle definition"
  },
  "mood": {
    "energy": "confident, strong",
    "color_palette": "dark, grey, warm skin tones",
    "aesthetic": "raw gym selfie"
  }
}
```

#### Sub-variants (Gym)
- **Gym mirror by weights**: weight rack visible, bright fluorescent, post-workout
- **Post-workout locker room**: bench, lockers, warm overhead light
- **Yoga mat stretch**: studio floor, mat, natural light from windows

### 6. Lifestyle / Casual Outdoor

```json
{
    "prompt": "Ultra photorealistic raw iPhone photo of a young Japanese woman in her early 20s outdoors in casual clothes. Long dark brown hair flowing naturally. Fitness hourglass figure, light-medium skin. She wears a simple crop top and jeans, holding iced coffee. She stands on a sidewalk, looking back at the camera with a natural smile. Simple urban background, slightly blurred. Warm afternoon sunlight. Casual candid photo aesthetic. Three-quarter body, eye-level, 4:5 portrait. Photorealistic, high quality, high resolution.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "iPhone 15 Pro Max",
    "lens": "24mm wide",
    "style": "candid phone photo"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long, flowing naturally"},
    "body_type": "fitness hourglass",
    "skin": "light-medium, natural",
    "expression": "natural smile, looking back at camera",
    "makeup": "minimal natural"
  },
  "outfit": {
    "top": {"type": "crop top", "color": "white", "fit": "fitted"},
    "bottom": {"type": "jeans", "color": "blue denim", "fit": "high-waisted"},
    "accessories": ["iced coffee"]
  },
  "pose": {
    "position": "standing, looking back",
    "stance": "natural, relaxed",
    "hands": "one hand holding coffee",
    "head_gaze": "glancing over shoulder at camera",
    "vibe": "spontaneous, carefree"
  },
  "scene": {
    "location": "sidewalk outdoors",
    "time": "afternoon",
    "atmosphere": "warm, casual",
    "background": "simple urban, slightly blurred"
  },
  "camera": {
    "pov": "friend-took-this-photo",
    "angle": "eye-level",
    "framing": "three-quarter body"
  },
  "lighting": {
    "type": "warm afternoon sunlight",
    "effect": "natural warm tones"
  },
  "mood": {
    "energy": "playful, spontaneous",
    "color_palette": "warm natural tones, denim blue, white",
    "aesthetic": "casual candid photo"
  }
}
```

---

## Negative Prompt Library

Build the `negative_prompt` field by combining relevant blocks. **Always include the base block** plus any category-specific additions.

### Base (ALWAYS include)
```
blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text
```

### Anatomy
```
extra limbs, distorted face, bad anatomy, deformed hands, extra fingers
```

### Style Exclusion
```
cartoon, illustration, CGI, painting, anime, sketch
```

### Skin Realism
```
plastic skin, airbrushed texture, skin smoothing, beautification filters
```

### Body Realism
```
anatomy normalization, body proportion averaging, aesthetic proportion correction
```

### Expression Control
```
teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile
```

### Standard Combined (use for most prompts)
```
blurry, low quality, low resolution, artifacts, text, watermark, logo, text on clothing, printed words, letters, numbers, typography, signage, brand logo, neon text, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction, teeth showing, open mouth smile, visible teeth, toothy grin, toothy smile
```

---

## 3-Tier Constraint Hierarchy

### Tier 1 — ENFORCED (validation fails if violated)
- **Character lock**: Subject must match fixed character profile (age, body type, skin, ethnicity)
- **iPhone only**: camera = "iPhone 15 Pro Max", lens = "24mm wide" — NEVER DSLR
- **Negative prompt**: ALWAYS include the standard combined block
- **Prompt length**: 120-180 words max
- **meta.style**: casual terms ONLY (NEVER "editorial")

### Tier 2 — STRONG DEFAULTS (recommended, not enforced)
- **10 scene types**: bedroom mirror, bathroom, beach/pool, gym, cozy bedroom, car interior, kitchen, cafe, living room, rooftop outdoor
- **Casual outfits**: sports bra, bikini, crop top, loungewear, oversized tee, bodysuit, shorts, leggings, sundress, tank top, hoodie
- **Max 2-3 background props** per scene
- **Lighting**: 1 sentence max

### Tier 3 — CREATIVE FREEDOM (Creator chooses freely)
- **Pose**: standing, sitting, lying, kneeling, leaning, mid-turn, crouching, stretching, walking, looking back, arms up
- **Mood/energy**: quiet, bold, playful, intimate, confident, dreamy, fierce, serene, mischievous, powerful, vulnerable
- **Lighting direction/warmth**: natural, warm lamp, cool blue, golden, dramatic, soft diffused
- **Color palette**: any complementary palette
- **Camera angle**: eye-level, low angle, high angle, dutch angle, over-shoulder
- **Props**: phone, coffee, towel, pillow, sunglasses, jewelry, headphones, book, etc.
- **Hair styling**: straight, wavy, ponytail, messy bun, braids, half-up, wet, windswept

---

## Additional Scene Types (beyond the 5 core)

### 7. Car Interior
- Sitting in passenger/driver seat, natural window light
- Sub-variants: parked with window light, backseat casual, driving mirror selfie

### 8. Kitchen / Morning
- Counter leaning, coffee in hand, morning light from window
- Sub-variants: kitchen counter lean, breakfast table, morning coffee moment

### 9. Cafe / Coffee Shop
- Window seat, ambient cafe lighting
- Sub-variants: corner booth, outdoor terrace, counter stool

### 10. Living Room / Couch
- Lounging on sofa, TV glow, cozy evening
- Sub-variants: couch curl-up, floor pillow, blanket nest

### 11. Rooftop / Balcony (occasional — not every day)
- City or nature backdrop, golden hour, wind in hair
- Sub-variants: sunset balcony, morning rooftop, urban skyline

---

## Prompt Writing Rules

1. The `prompt` field must be a **single paragraph, 120-180 words** (NOT 250+ — shorter prompts produce better results)
2. Weave details into the paragraph naturally — do not use bullet points or field labels
3. Order: shot type → subject → outfit → pose → scene (2-3 props max) → lighting (1 sentence) → quality markers
4. ALWAYS specify "iPhone 15 Pro Max" in the prompt text — never DSLR cameras
5. End with quality markers: "Photorealistic, high quality, high resolution."
6. Use specific but concise language — "black sports bra and grey leggings" not "fitted seamless athletic-blend sports bra with thin adjustable straps"
7. Pose description = vibe + 1-2 key elements, NOT per-limb anatomy
8. Background = location name + 2-3 props MAX. The subject should dominate the image, not the environment
9. Lighting = 1 sentence. "Warm natural window light" is enough. No multi-source lighting descriptions.
10. The `negative_prompt` is always REQUIRED — use the standard combined block above as a baseline
11. Subject details (age, body type, core features) come from the Fixed Character Profiles — do NOT vary these between posts
12. Hair color/style and outfits SHOULD vary between posts for visual diversity
13. NEVER use the word "editorial" anywhere in the prompt or meta.style — it produces magazine-quality output that doesn't match this niche
14. Think "my friend took this photo of me" NOT "a photographer shot this for a magazine"
