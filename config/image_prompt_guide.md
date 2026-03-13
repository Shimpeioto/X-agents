# Higgsfield SeedREAM — Image Prompt Guide

## Overview

- **Tool**: Higgsfield SeedREAM (`higgsfield`)
- **Output**: Both a structured JSON object AND a flat `prompt` paragraph (150+ words)
- The structured fields ensure nothing is missed; the `prompt` text is what gets pasted into Higgsfield
- All prompts must achieve ultra photorealistic quality — the goal is images indistinguishable from real iPhone/DSLR photos

## Fixed Character Profiles

These profiles are **locked** — use these exact traits for every post on the respective account. Do NOT vary age, body type, or core physical traits between posts. Hair color/style and outfit change per post, but the underlying character is always the same person.

### EN Account Character (Meruru)

- **Age**: Early 20s
- **Ethnicity**: Japanese
- **Hair**: Dark/jet-black or dark brown, long straight or wavy (style varies per post, color stays dark)
- **Body**: Fitness hourglass figure, ample chest, toned core, wide hips, thick thighs
- **Skin**: Light-medium neutral, smooth
- **Face**: Naturally attractive, expressive features
- **Makeup**: Minimal — natural brows, soft lip
- **Persona**: Real influencer feel — confident, playful, casually flirty. Never reveals AI nature. "Cute but Deadly" — effortlessly charming, quietly strategic.

### JP Account Character

- **Age**: Early 20s
- **Ethnicity**: Japanese / East Asian
- **Hair**: Dark (black or dark brown), long, straight or soft waves
- **Body**: Hourglass figure, large full chest, slim waist, wide full hips
- **Skin**: Fair porcelain, smooth, natural glow
- **Face**: Delicate features, almond-shaped eyes, natural Korean-style makeup
- **Persona**: Warm, authentic, intimate. Natural Japanese social media style.

---

## Prompt Schema (JSON structure)

Each `image_prompt` object must contain these structured fields:

```
meta:
  quality      — always "ultra photorealistic"
  camera       — e.g., "iPhone 15 Pro Max", "Sony A7R IV", "Canon EOS R5"
  lens         — e.g., "24mm wide", "85mm prime f/1.4", "50mm f/1.8"
  style        — e.g., "raw iphone mirror selfie", "fashion editorial", "casual lifestyle"

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
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic raw iPhone mirror selfie of a young woman in her early 20s standing in a modern minimalist bedroom. She has long dark brown hair falling past her shoulders in soft natural waves. Hourglass athletic-toned figure with natural skin texture and visible pores. She wears a fitted white ribbed crop top and high-waisted black yoga pants that hug her curves. One hand holds an iPhone 15 Pro Max at chest height, the other rests casually on her hip with fingers slightly spread. Her weight shifts to her left leg creating a subtle hip tilt. She gazes at the phone screen with a relaxed confident expression and soft natural smile. Slight head tilt to the right. The room has a clean white wall behind a large black-framed full-length mirror, grey carpet, and a neatly made bed with white linens visible in the background. Natural golden hour sunlight streams from a window to the left, casting warm highlights across her skin and soft directional shadows on the wall. The lighting creates a warm glow on her face and arms. Soft pink, clean white, warm gold color palette. Casual everyday influencer aesthetic. Shot at eye-level in portrait orientation, centered composition. Photorealistic, high quality, high resolution, 9:16 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
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

### 2. Bathroom / Post-shower

```json
{
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic photo of a young Japanese woman in her early 20s in a modern luxury hotel bathroom just after a shower. She has long straight black hair, wet and clinging to her shoulders and back with water droplets visible. Fair porcelain skin with a natural dewy glow, smooth with subtle water drops on her collarbones and shoulders. Hourglass figure with full curves. She wears a plush oversized white hotel towel wrapped around her torso, tucked above her chest, the towel ending at upper thigh. Delicate features with almond-shaped eyes and natural Korean-style makeup — subtle brow, light mascara, dewy skin finish, soft pink lip tint. She stands facing a large frameless bathroom mirror, holding her phone with both hands at face level, taking a selfie with a warm intimate expression, lips slightly parted, soft gaze at the screen. Slight forward lean toward the mirror. The bathroom has white marble countertop with chrome fixtures, warm recessed lighting overhead, a frosted glass shower door behind her with visible steam wisps, folded grey towels on the counter. Warm artificial lighting from above creates a soft diffused glow on her wet skin, highlights the water droplets, and produces gentle shadows under her jawline. Warm ivory, soft white, chrome silver color palette. Intimate post-shower aesthetic. Shot from mirror reflection POV, slightly low angle, medium shot waist-up, centered composition. Photorealistic, high quality, high resolution, 4:5 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
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

### 3. Pool / Beach / Outdoor

```json
{
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic photo of a young woman in her early 20s lounging by an infinity pool at a tropical resort. She has shoulder-length wavy blonde hair with sun-kissed highlights, slightly tousled from swimming. Athletic-toned hourglass figure with natural sun-kissed skin showing real texture and a light tan. She wears a sleek black string bikini, triangle top with thin straps and matching low-rise bottoms. Her skin glistens with a mix of pool water and sunscreen, water droplets visible on her stomach and thighs. She reclines on a white cushioned pool lounger, propped up on her elbows with her back slightly arched. Right leg extended, left knee bent up casually. She looks directly at the camera with a playful confident smirk, chin slightly down, eyes bright. Behind her the infinity pool edge blends into an ocean horizon view, palm trees frame the right side, white pool deck with another empty lounger to the left. Bright midday tropical sunlight from directly above creates strong highlights on her shoulders and chest with defined shadows beneath the lounger. Water reflections cast dancing light patterns on her lower body. Bright turquoise, tropical green, warm bronze, clean white color palette. Luxury vacation lifestyle aesthetic. Third-person shot, slightly low angle from foot of lounger, full body framing, vertical portrait composition. Photorealistic, high quality, high resolution, 4:5 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "Sony A7R IV",
    "lens": "35mm f/1.4",
    "style": "luxury vacation lifestyle"
  },
  "subject": {
    "hair": {"color": "blonde with sun-kissed highlights", "style": "shoulder-length wavy, tousled"},
    "body_type": "athletic-toned hourglass",
    "skin": "sun-kissed natural tan, real texture, glistening with water and sunscreen",
    "expression": "playful confident smirk, chin slightly down, bright eyes",
    "makeup": "minimal, waterproof mascara, natural sun-flushed look"
  },
  "outfit": {
    "top": {"type": "string bikini top", "color": "black", "material": "stretch fabric", "fit": "triangle top, thin straps"},
    "bottom": {"type": "bikini bottoms", "color": "black", "fit": "low-rise, string sides"},
    "accessories": []
  },
  "pose": {
    "position": "reclining on lounger",
    "stance": "propped on elbows, slight back arch, right leg extended, left knee bent",
    "hands": "elbows on lounger supporting upper body",
    "head_gaze": "looking directly at camera, chin slightly down",
    "vibe": "playful confidence"
  },
  "scene": {
    "location": "tropical resort infinity pool",
    "time": "midday",
    "atmosphere": "bright, energetic, tropical",
    "background": "infinity pool edge into ocean horizon, palm trees right, white pool deck, empty lounger left"
  },
  "camera": {
    "pov": "third-person",
    "angle": "slightly low angle from foot of lounger",
    "framing": "full body"
  },
  "lighting": {
    "type": "bright midday tropical sunlight from above",
    "effect": "strong highlights on shoulders and chest, defined shadows under lounger, dancing water reflections on lower body"
  },
  "mood": {
    "energy": "playful, bold",
    "color_palette": "bright turquoise, tropical green, warm bronze, clean white",
    "aesthetic": "luxury vacation lifestyle"
  }
}
```

### 4. Bedroom / Indoor Casual

```json
{
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic photo of a young Japanese woman in her early 20s sitting casually on an unmade bed in a cozy modern apartment bedroom. She has long straight dark brown hair draped over one shoulder with a few strands falling across her face. Fair porcelain skin with a natural warm glow, smooth with delicate features and almond-shaped eyes. Natural Korean-style makeup with defined soft brows, subtle brown eyeshadow, light mascara, dewy glass-skin finish, and a soft peach lip tint. Hourglass figure with full curves visible through her outfit. She wears an oversized cream-colored knit sweater that hangs off one shoulder revealing a bare collarbone and thin black bra strap, paired with short light-wash denim shorts. She sits cross-legged on rumpled white sheets and a chunky knit throw blanket, leaning forward slightly with her chin resting on her right hand, elbow on her knee. Left hand rests palm-down on the bed beside her. She looks at the camera with a warm inviting expression, soft eyes, gentle closed-lip smile. The bedroom has warm-toned wood furniture, a bedside table with a small brass lamp casting warm light, a potted succulent, and a softly lit string of fairy lights draped along the headboard. Warm lamplight from the bedside creates intimate golden tones across her face and sweater, soft shadows on the far wall, and a gentle highlight on her exposed shoulder. Warm cream, soft gold, cozy brown, muted denim blue color palette. Cozy intimate bedroom aesthetic. Third-person shot at eye-level, medium shot from waist up, centered composition. Photorealistic, high quality, high resolution, 4:5 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "Canon EOS R5",
    "lens": "50mm f/1.8",
    "style": "cozy intimate bedroom portrait"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long straight, draped over one shoulder, strands across face"},
    "body_type": "hourglass figure, full curves",
    "skin": "fair porcelain, natural warm glow",
    "expression": "warm inviting, soft eyes, gentle closed-lip smile",
    "makeup": "natural Korean-style, defined soft brows, subtle brown eyeshadow, glass-skin finish, soft peach lip tint"
  },
  "outfit": {
    "top": {"type": "oversized knit sweater", "color": "cream", "material": "soft knit", "fit": "oversized, off-one-shoulder", "details": "reveals bare collarbone and thin black bra strap"},
    "bottom": {"type": "denim shorts", "color": "light wash", "fit": "short"},
    "accessories": []
  },
  "pose": {
    "position": "sitting cross-legged on bed",
    "stance": "leaning forward slightly",
    "hands": "right hand supporting chin (elbow on knee), left hand palm-down on bed",
    "head_gaze": "facing camera, warm inviting gaze",
    "vibe": "cozy warmth"
  },
  "scene": {
    "location": "cozy modern apartment bedroom",
    "time": "evening",
    "atmosphere": "warm, intimate, cozy",
    "background": "warm-toned wood furniture, bedside table with brass lamp, potted succulent, fairy lights on headboard, rumpled white sheets, chunky knit throw"
  },
  "camera": {
    "pov": "third-person",
    "angle": "eye-level",
    "framing": "medium shot, waist-up"
  },
  "lighting": {
    "type": "warm lamplight from bedside table",
    "effect": "intimate golden tones on face and sweater, soft shadows on far wall, gentle highlight on exposed shoulder"
  },
  "mood": {
    "energy": "quiet, intimate",
    "color_palette": "warm cream, soft gold, cozy brown, muted denim blue",
    "aesthetic": "cozy intimate bedroom"
  }
}
```

### 5. Fashion Editorial / Studio

```json
{
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic fashion editorial photo of a young woman in her early 20s posing in a clean professional photography studio. She has sleek straight jet-black hair pulled into a tight low ponytail with a center part, face fully visible. Athletic-toned hourglass figure with natural skin texture showing real pores. She wears a structured emerald green satin blazer with sharp shoulders, no shirt underneath showing a plunging neckline to the sternum, paired with tailored high-waisted black trousers with a wide straight leg. Gold hoop earrings and a delicate gold chain necklace. She stands in a strong contrapposto pose with her right hip pushed out, left leg stepped slightly forward. Right hand in the blazer pocket, left arm hanging naturally at her side with fingers relaxed. She looks directly at the camera with a neutral focused expression, lips slightly parted, strong eye contact, chin level. The studio has a seamless light grey backdrop paper, no visible wrinkles or seams, a minimal clean environment. Professional studio lighting with a large softbox as key light from upper left creating soft even illumination with subtle shadows on the right side of her face and body, a fill light from the right reducing harsh shadows, and a hair light from behind creating a subtle rim highlight separating her from the background. Cool grey, rich emerald, warm gold, deep black color palette. High fashion editorial aesthetic. Shot at eye-level, full body framing with slight space above and below, centered vertical composition. Photorealistic, high quality, high resolution, 9:16 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
  "aspect_ratio": "9:16",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "Canon EOS R5",
    "lens": "85mm prime f/1.4",
    "style": "high fashion editorial"
  },
  "subject": {
    "hair": {"color": "jet black", "style": "sleek straight, tight low ponytail, center part"},
    "body_type": "athletic-toned hourglass",
    "skin": "natural texture, real pores",
    "expression": "neutral focused, lips slightly parted, strong eye contact, chin level",
    "makeup": "editorial glam, sculpted contour, bold defined brows, smoky neutral eye, matte nude lip"
  },
  "outfit": {
    "top": {"type": "structured blazer", "color": "emerald green", "material": "satin", "fit": "structured, sharp shoulders", "details": "no shirt, plunging neckline to sternum"},
    "bottom": {"type": "trousers", "color": "black", "fit": "tailored high-waisted, wide straight leg"},
    "accessories": ["gold hoop earrings", "delicate gold chain necklace"]
  },
  "pose": {
    "position": "standing",
    "stance": "contrapposto, right hip pushed out, left leg stepped forward",
    "hands": "right hand in blazer pocket, left arm hanging naturally, fingers relaxed",
    "head_gaze": "facing camera directly, chin level, strong eye contact",
    "vibe": "editorial power"
  },
  "scene": {
    "location": "professional photography studio",
    "time": "n/a (studio)",
    "atmosphere": "clean, professional, minimal",
    "background": "seamless light grey backdrop paper, no wrinkles or seams"
  },
  "camera": {
    "pov": "third-person",
    "angle": "eye-level",
    "framing": "full body with slight space above and below"
  },
  "lighting": {
    "type": "professional studio: large softbox key light upper left, fill light right, hair light from behind",
    "effect": "soft even illumination, subtle shadows on right face/body, rim highlight separating from background"
  },
  "mood": {
    "energy": "bold, commanding",
    "color_palette": "cool grey, rich emerald, warm gold, deep black",
    "aesthetic": "high fashion editorial"
  }
}
```

### 6. Lifestyle / Street

```json
{
  "tool": "higgsfield",
  "prompt": "Ultra photorealistic candid street style photo of a young Japanese woman in her early 20s walking through a trendy Tokyo neighborhood. She has long straight dark brown hair flowing behind her in the breeze, catching the light. Fair porcelain skin with a natural glow. Delicate features with almond-shaped eyes and natural Korean-style makeup — soft filled brows, light peach eyeshadow, mascara, glass skin finish, MLBB lip color. Hourglass figure visible through her outfit. She wears a cropped vintage graphic tee knotted at the waist in faded black, a pleated beige mini skirt, white platform sneakers, small round sunglasses pushed up on her head, and a small crossbody leather bag in caramel. She walks mid-stride with her left foot forward, right arm swinging naturally holding iced coffee in a clear cup, left hand adjusting her hair behind her ear. She glances over her right shoulder toward the camera with a spontaneous genuine smile, caught mid-laugh, eyes crinkled. The street has an eclectic mix of small Japanese shop fronts with neon signs, potted plants on the sidewalk, a vintage bicycle parked against a wall, warm-toned brick and painted building facades. Late afternoon golden hour sunlight from behind and left creates a warm backlight halo effect on her hair and silhouette, long directional shadows on the pavement, and a warm amber glow across the entire scene. Warm amber, faded black, creamy beige, caramel brown, soft neon color palette. Candid Tokyo street style aesthetic. Third-person shot from behind and slightly right, three-quarter body framing as she looks back, slight dutch angle for dynamism. Photorealistic, high quality, high resolution, 4:5 aspect ratio.",
  "negative_prompt": "blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction",
  "aspect_ratio": "4:5",
  "meta": {
    "quality": "ultra photorealistic",
    "camera": "Sony A7R IV",
    "lens": "35mm f/1.4",
    "style": "candid street style"
  },
  "subject": {
    "hair": {"color": "dark brown", "style": "long straight, flowing in breeze"},
    "body_type": "hourglass figure",
    "skin": "fair porcelain, natural glow",
    "expression": "spontaneous genuine smile, caught mid-laugh, eyes crinkled",
    "makeup": "natural Korean-style, soft filled brows, light peach eyeshadow, glass skin, MLBB lip"
  },
  "outfit": {
    "top": {"type": "cropped vintage graphic tee", "color": "faded black", "material": "cotton", "fit": "cropped, knotted at waist"},
    "bottom": {"type": "pleated mini skirt", "color": "beige", "fit": "mini length, pleated"},
    "footwear": "white platform sneakers",
    "accessories": ["small round sunglasses on head", "caramel crossbody leather bag", "iced coffee in clear cup"]
  },
  "pose": {
    "position": "walking mid-stride",
    "stance": "left foot forward, natural walking momentum",
    "hands": "right hand holding iced coffee, left hand adjusting hair behind ear",
    "head_gaze": "glancing over right shoulder toward camera",
    "vibe": "spontaneous joy"
  },
  "scene": {
    "location": "trendy Tokyo neighborhood street",
    "time": "late afternoon golden hour",
    "atmosphere": "warm, candid, urban energy",
    "background": "small Japanese shop fronts with neon signs, potted plants on sidewalk, vintage bicycle against wall, brick and painted facades"
  },
  "camera": {
    "pov": "third-person from behind and slightly right",
    "angle": "slight dutch angle for dynamism",
    "framing": "three-quarter body"
  },
  "lighting": {
    "type": "late afternoon golden hour backlight from behind-left",
    "effect": "warm halo on hair and silhouette, long shadows on pavement, amber glow across scene"
  },
  "mood": {
    "energy": "playful, spontaneous",
    "color_palette": "warm amber, faded black, creamy beige, caramel brown, soft neon",
    "aesthetic": "candid Tokyo street style"
  }
}
```

---

## Negative Prompt Library

Build the `negative_prompt` field by combining relevant blocks. **Always include the base block** plus any category-specific additions.

### Base (ALWAYS include)
```
blurry, low quality, low resolution, artifacts, text, watermark, logo
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

### Standard Combined (use for most prompts)
```
blurry, low quality, low resolution, artifacts, text, watermark, logo, extra limbs, distorted face, bad anatomy, deformed hands, extra fingers, cartoon, illustration, CGI, painting, anime, sketch, plastic skin, airbrushed texture, skin smoothing, beautification filters, anatomy normalization, body proportion averaging, aesthetic proportion correction
```

---

## Prompt Writing Rules

1. The `prompt` field must be a **single comprehensive paragraph, 150+ words**
2. Weave ALL structured details into the paragraph naturally — do not use bullet points or field labels
3. Start with the overall scene/shot type, then subject description, then outfit details, then pose, then scene/background, then lighting/mood
4. Include camera simulation details in the prompt text (e.g., "Shot at eye-level" or "captured with iPhone 15 Pro Max")
5. End with quality markers: "Photorealistic, high quality, high resolution, {aspect_ratio} aspect ratio."
6. Use specific, concrete language — not "wearing a nice top" but "wearing a fitted white ribbed crop top"
7. Describe physical actions precisely — not "posing" but "right hand in blazer pocket, left arm hanging naturally with fingers relaxed"
8. Include environmental details that sell realism — water droplets, fabric textures, light reflections, shadow patterns
9. The `negative_prompt` is always REQUIRED — use the standard combined block above as a baseline
10. Subject details (age, body type, core features) come from the Fixed Character Profiles — do NOT vary these between posts
11. Hair color/style and outfits SHOULD vary between posts for visual diversity
