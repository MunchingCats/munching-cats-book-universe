# Munching Cats — Picture Book Production & Story Framework Specification

## 1. Scope & Core Principles (Ages 3–10)
This document governs the storytelling grammar, visual layout constraints, and physical print parameters for the *Munching Cats* picture book series. It serves as the master contract for both manual authoring and automated Cursor layout pipelines.

### The 5 Golden Narrative Rules
1. **Uncompromising Protagonist Agency:** Munchie (or the featured lead) drives all decisions, initiates the plans, and solves dilemmas. No external authority or adult intervention solves the conflict.
2. **The Page-Turn as a Physical Mechanism:** Left-hand pages (even) build setups; right-hand pages (odd) create curiosity or dramatic tension. Every turn of the page must deliver a payoff, consequence, or visual punchline.
3. **The Text-Image Gap:** Text and art must not merely duplicate one another. The text carries the earnest narrative tone; the illustration reveals the humorous, physical reality.
4. **Friction Over Malice:** Antagonists have clear, opposing, and relatable goals. Conflict is driven by slapstick energy, mismatched plans, and comedic misunderstandings rather than cruelty or evil.
5. **Emotional Resonance Without Moralizing:** Themes (friendship, sharing, perseverance) are demonstrated strictly through character choices and rewarding outcomes—never through preachy dialogue or closing morals.

---

## 2. Pacing Architecture: 32-Page / 14-Spread Blueprint

Standard picture books operate in two-page spreads viewed simultaneously:
* **Page 1:** Half-title / Dedication (Right-hand single page)
* **Pages 2–3:** Title Spread & Copyright Page
* **Pages 4–31:** 14 Visual Spreads (The Story Spine)
* **Page 32:** End Matter (Author note, brand seal, teaser)

### The 7-Beat Story Spine
* **Beat 1 (Spreads 1–2 / Pages 4–7): Normalcy & The Craving**
  * Establish the protagonist's core desire and personality flaw in their home environment.
  * *Visuals:* Warm, inviting wide establishing frames.
* **Beat 2 (Spread 3 / Pages 8–9): The Inciting Disruption**
  * The status quo breaks; a tempting opportunity or clear obstacle emerges.
  * *Visuals:* Focused medium shot emphasizing the goal or problem.
* **Beat 3 (Spread 4 / Pages 10–11): The Scheme**
  * The protagonist commits to an overly ambitious, flawed course of action.
  * *Visuals:* Dynamic schematic framing or character planning vignette.
* **Beat 4 (Spreads 5–8 / Pages 12–19): The Rule of Three (Escalation)**
  * *Attempt 1:* Minor snag, quick slapstick recovery.
  * *Attempt 2:* Higher stakes, bigger mess, counteraction from rivals.
  * *Attempt 3:* Full-effort push resulting in unexpected complications.
  * *Visuals:* Accelerated visual tempo; alternating dynamic panels and wide action.
* **Beat 5 (Spreads 9–10 / Pages 20–23): Climax & Maximum Chaos**
  * Peak physical comedy and conflict collision. The initial plan collapses completely.
  * *Visuals:* Full-bleed double-page spread with extreme expressions and motion.
* **Beat 6 (Spreads 11–12 / Pages 24–27): The Breakthrough**
  * Resolution achieved through character quirks, unique traits, or unexpected alliances.
  * *Visuals:* Tempo drops abruptly; dramatic reaction frame followed by relief.
* **Beat 7 (Spreads 13–14 / Pages 28–31): The Reward & Final Kicker**
  * *Spread 13:* Cozy, shared payoff; emotional satisfaction and warm light.
  * *Spread 14:* Spot-illustration kicker teasing upcoming adventures or lingering habits.

---

## 3. Physical Print Specifications (Amazon KDP Standard)

* **Trim Size:** 8.5" × 8.5" ($215.9 \times 215.9\text{ mm}$)
* **Bleed Allowance:** $0.125"$ ($3.175\text{ mm}$) on top, bottom, and outside edges.
* **Full Bleed Submission Dimensions (Per Page):** 8.625" × 8.750" ($219.1 \times 222.3\text{ mm}$)
* **Two-Page Spread Canvas Dimensions:** 17.250" × 8.750" (including bleed)
* **Resolution:** Strictly 300 DPI ($5175 \times 2625\text{ px}$ for two-page spread canvas).
* **Binding Gutter:** Inner margin of $0.50"$ to $0.625"$ kept clear of critical character features, text, and tight focal points.
* **Safe Zone:** All typography, critical storytelling details, and focal character heads must sit at least $0.375"$ inside the trim line ($0.50"$ from the raw canvas edge).
* **Cover Wrap & Barcode:** Back cover must reserve an unobstructed $2.0" \times 1.2"$ white rectangular area in the lower-right corner, offset $\ge 0.25"$ from trim lines.

---

## 4. Director’s Grammar & Visual Layout Rules

Every scene directive generated for the layout engine must specify:
1. **Camera Grammar:** Focal length, elevation (low hero angle, bird's-eye tactical, eye-level intimate), and shot distance (wide, medium, close).
2. **Text Anchor Zone:** Explicit reservation of low-contrast space (`TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_SPAN`, `MARGIN_BAND`) so text sits directly on clean negative space (e.g., solid wall, soft sky, flat floor) without dark backing boxes.
3. **Character Scale Ratios:**
   * Munchie: 100% baseline ($0.50\text{m}$)
   * Lunie: 110% ($0.55\text{m}$)
   * Bast: 85% ($0.425\text{m}$)
   * Ratios must remain locked regardless of camera perspective.

---

## 5. Typography & Color Specifications

### Type Hierarchy
* **Display / Cover Title / Sound Effects:** Pecita (or approved stylized display face). Restricted to cover, title page, and bold onomatopoeia (*CHOMP!*, *WHOOSH!*).
* **Body / Story Narrative:** Open, child-accessible sans-serif or clean serif (e.g., Poppins Semi-Bold, Quicksand) featuring single-storey 'a' and 'g' and generous tracking.
* **Print Black:** 100% K (single-plate ink) for all body text to avoid CMYK registration blur.

### Color Palette Roles
* `#000000` — Pure Print Ink / Character Silhouette Linework
* `#FF8040` — Tangerine Energy (Action highlights, Munchie accents, callouts)
* `#FBC3F5` — Candy Bloom (Whimsical accents, soft props, playful highlights)
* `#C9D0C6` — Muted Sage (Neutral ground, foliage, architectural surfaces)
* `#74B3CE` — Atmospheric Sky (Daylight, floor rugs, cool shadow balance)
* `#E6E4E4` — Alabaster Paper (Narrative text safe zones, speech callouts)
* `#FFF275` $\rightarrow$ `#FF8040` Gradient — Simulated Gold/Luminous Effect