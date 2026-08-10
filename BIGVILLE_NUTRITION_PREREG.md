# PREREG — block 332000: nutrition (density, variety, deficiency) + ale (body & mind)

Food is currently a single generic resource (a flat `food_energy`), and ale is not modelled
at all — even though the agent holds a `nutrition.json` knowledge seed (kilocalories,
protein, "essential nutrients must be supplied", "deficiency disease specific to nutrient")
it never applies. This rung grounds that knowledge: **different foods have different
nutritional density and nutrient content; variety matters; a chronically missing nutrient
causes deficiency; and ale has a dual effect — calories for the body and intoxication for
the mind.** It composes with the cognitive loop's sustenance drive, mood, and focus.

## The mechanism (`bigville_nutrition.json`)

A `Food{kind, energy, protein, alcohol}` codebook (e.g. fish: energy 3 / protein 2; bread:
energy 4 / protein 0.5; ale: energy 2 / protein 0 / alcohol 1.5).

- **`nu_eat`** — eating food F: `energy += F.energy · (1 − monotony)` (**nutritional
  density** — a denser food restores more, scaled by **variety**); `protein_store += F.protein`;
  `intoxication += F.alcohol`. **Specific satiety**: `monotony` rises if F is the same kind as
  last eaten (diminishing reward), resets to 0 on a new kind.
- **`nu_metabolize`** — per epoch, `protein_store`, `intoxication`, and `monotony` all decay
  (recent intake fades; the drinker sobers up; the palate resets).
- **`nu_deficiency`** — while `protein_store < protein_need`, `deficiency` accrues; a
  sufficient diet lets it recover. Grounds "essential nutrients must be supplied".
- **`nu_psych`** — the mind state: `mood = base + intoxication·mood_gain − deficiency·mood_pen`
  and `focus = base − intoxication·focus_pen − deficiency·focus_pen`. **Ale lifts mood but
  impairs focus; deficiency drags both down.**

## Gates (pass/fail, pre-registered)

1. **G-nutritional-density:** eating a denser food restores **more** energy per unit than a
   sparse one — foods differ nutritionally.
2. **G-variety-matters:** eating the **same** food repeatedly yields **diminishing** energy
   (specific satiety); alternating foods keeps each satisfying.
3. **G-deficiency-from-imbalance:** a diet missing protein (all bread/ale) accrues
   **deficiency** (dragging mood/focus); a protein-containing diet (fish) does not.
4. **G-ale-is-dual (HEADLINE):** drinking ale **both** adds energy (calories for the body)
   **and** raises intoxication, which **lifts mood and impairs focus** (the mind) — both
   effects, in one act.
5. **G-ale-is-empty-calories:** relying on ale sustains energy but supplies **no protein**,
   so **deficiency still accrues** — ale feeds the body poorly while pleasing the mind.
6. **G-no-python-decision (source audit):** eat/metabolize/deficiency/psych are the seed
   rules; the adapter arms which food is eaten, pulses metabolism, and reads.

## Scope / honesty
- One nutrient (protein) stands for the essential-nutrient vector; a full macro/micronutrient
  set + specific deficiency diseases (the `nutrition.json` knowledge) is the refinement.
- `monotony` is a single satiety counter (last-kind repeat); true satiety-specific-satiety per
  food is a richer model, deferred.
- Intoxication's effect is a linear mood-up/focus-down while present; an explicit hangover
  (post-sobering load) is deferred — the empty-calorie deficiency is ale's modelled long cost.
- Composes with the cognitive loop (331000): energy → the sustenance drive; mood/focus → C3/C2.
  This rung is the standalone nutrition+ale demonstrator; the fold-in wires it into `bigville_cognition`.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
