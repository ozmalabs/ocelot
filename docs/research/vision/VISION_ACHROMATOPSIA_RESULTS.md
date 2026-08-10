# VISION — CEREBRAL ACHROMATOPSIA: colour-SIGN / chromatic-STRUCTURE dissociation (RESULTS)

*Confirmatory run of `VISION_ACHROMATOPSIA_PREREG.md` (committed BEFORE the run, §3).
Runner `scripts/achromatopsia_measure.py`; gate `tests/test_achromatopsia_migrated.py`;
seed `seeds/vision_colour_identity.json` v1.1.0 (builder
`tools/build_vision_colour_identity.py`); adapter `domains/achromatopsia_world.py`;
raw `results/achromatopsia_measure.json`. A LESION-VALIDATION gate for the design's
luminance-structure / colour-sign split (`VISION_VENTRAL_GROUNDING.md` failure-mode
gate 5; Heywood & Cowey 1997 *TICS*).*

## Engine / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*). This rung adds **NO Rust**,
  so the shared build is legitimate (§10.1 rule 4). Worktree
  `.claude/worktrees/agent-ad67c6af4985b570e`; `git merge-base --is-ancestor
  d8955f47 HEAD` = true (§11).
- **NO new Rust. ONE seed edit** (`vision_colour_identity` 1.0.0 → 1.1.0: adds the
  `achromatopsia` flag + a guard on `ci_mint_category`/`ci_assign`). The flag is OFF
  by default (`ColourIdentityParams.achromatopsia = 0.0` = INTACT), so §9 byte-
  identity holds by construction: the committed `test_colour_identity_migrated.py`
  (6/6) and `test_colour_salience_migrated.py` (6/6) reproduce EXACTLY, and the diff
  vs v1.0.0 is exactly the flag attr + two `Lt(achromatopsia, 0.5)` guard clauses +
  version/description (nothing else moved).

## STEP 1 AUDIT — is this a clean flag-level ablation? (§12.4, file:line)

**VERDICT: YES.** The colour system is two SEPARATE seeds with INDEPENDENT flags:
`vision_colour` (salience / chromatic STRUCTURE: `cc_contrast` `:24`, `cc_salience`
`:732`, gated on `ColourParams.{salience,colour}`) and `vision_colour_identity`
(categorical SIGN: `ci_opponent` `:24`, `ci_mint_category` `:151`, `ci_assign` `:586`,
gated on `ColourIdentityParams.identity`; the `achromatopsia` guard is the
`Lt(achromatopsia,0.5)` clause added to `ci_mint_category` and `ci_assign`). `cc_contrast` reads ONLY raw cones +
neighbours — never `crg`/`cby`/a category — so the chromatic-STRUCTURE readouts are
independent of the identity SIGN by construction. The faithful achromatopsia lesion
(signal preserved, categorical sign abolished) is a dedicated `achromatopsia` flag on
`ColourIdentityParams` (OFF by default = intact) that guards ONLY `ci_mint_category`
+ `ci_assign`, leaving `ci_opponent` (the chromatic SIGNAL) and the whole salience
seed intact. It is pure graph data (a flag on a params node, the same
`PickUnique(ColourIdentityParams)` idiom the `identity` guard uses) — not a Python
code path (§0). All chromatic-structure readouts (chromatic border/contrast `csal`,
shape-from-colour, colour-defined boundary, its displacement) compose from
`cc_contrast`; the opponent signal from `ci_opponent`. Clean.

## Verdict — ALL arms PASS; every pre-registered prediction held exactly

| arm | result |
|---|---|
| **DISSOCIATION** (headline) | **PASS** — with colour-identity ablated, categorization is **LOST** (`n_categories` **2 → 0**, `n_signs` **36 → 0**) while chromatic STRUCTURE is **BYTE-FOR-BYTE PRESERVED**: `max_csal` = **10.0** in BOTH arms, `csal_max_abs_diff_across_arms` = **0.0**, `n_csal_positive` = **20** in both, and the colour-defined boundary DISPLACEMENT = **+1.0 col** in both, identically. Equiluminant figure ⇒ `max_lsal` = **0.0** (the boundary is traced by CHROMA alone — shape-from-colour). |
| **CONTROL_VALIDITY** (§1.1) | **PASS** — neither side is a dead floor. Ablated structure is **ALIVE**: `max_csal_ablated` = 10.0, `n_csal_positive_ablated` = 20, and `op_done_min_ablated` = **1.0** (every cell's `ci_opponent` fired — the opponent SIGNAL is computed; the categorization is *suppressed on live machinery*, not silently absent). Intact identity is ALIVE: `n_categories_intact` = 2, `all_signs_correct_intact` = true. |
| **SPLIT_CLEAN** | **PASS** — a luminance-defined edge yields `max_lsal` = **6.667** IDENTICALLY in both arms (`lsal_max_abs_diff_across_arms` = 0.0) with `max_csal` = 0.0. The colour lesion is chroma/identity-specific; luminance structure is untouched throughout. |
| **FLOOR** | **PASS** — an achromatic stimulus yields `max_csal` = **0.0** (no chromatic structure) and **0 chromatic categories** in BOTH arms (no colour sign), while `max_lsal` = **7.0** (luminance present). The intact arm's ONLY mint is one *colourless grey* origin category at (0,0) (`achromatic_grey_categories_intact` = 1), reported honestly and NOT a colour sign. The achromatic condition kills colour REGARDLESS of the identity flag ⇒ the dissociation is not a luminance artifact. |
| **OFFDAY** (§9) | **PASS** — all flags at default (0) ⇒ inert: `max_cc_done` = 0, `n_categories` = 0, `max_op_done` = 0, `max_sign_rg` = 0. |

## The headline — the split is REAL in the build: colour STRUCTURE and colour SIGN dissociate cleanly

**One flag (`achromatopsia`, OFF by default) suppresses ONLY the categorical-colour
SIGN (`ci_mint_category` + `ci_assign`) — and colour NAMING vanishes (2 categories →
0, 36 signs → 0) while every chromatic-STRUCTURE readout is preserved BYTE-FOR-BYTE:**

- **Chromatic border / edge / contrast** (`csal`, `cc_contrast`): `max_csal` = 10.0
  and the same 20-cell border ring in BOTH arms; `max|csal_intact − csal_ablated| =
  0.0`. The equiluminant figure/ground boundary is detected by cone-opponent contrast,
  identical with and without the sign.
- **Shape-from-colour**: the figure is EQUILUMINANT (`max_lsal = 0.0`), so the 20-cell
  `csal` ring that traces its outline is a *pure-chroma* percept — the shape is
  recovered from colour with luminance salience at zero, in both arms.
- **Colour-defined boundary displacement** (the motion substrate): shift the figure +1
  column and the `csal` boundary centroid moves +1.0 col — identically in the intact
  and ablated arms.

**This is the exact clinical dissociation** (Heywood & Cowey 1997): a ventral colour-
SIGN lesion abolishes conscious colour categorization while the chromatic SIGNAL —
chromatic borders, shape-from-colour, colour-defined motion — survives. The substrate
realises it because the two functions live in two seeds with two flags, and the
STRUCTURE seed never reads the SIGN.

**Neither arm is trivially null (§1.1).** The ablated "0 categories" is a genuine
lesion on LIVE machinery: `ci_opponent` still fired (`op_done = 1` everywhere — the
opponent signal is present) and `csal` still fired (border ring intact). A dead arm
would have scored 0 on everything; this arm scores 0 ONLY on the categorical sign and
full on structure — a measurement, not a lookup.

## What I predicted, and what I got (§3.7 / §7)

I predicted **all five arms PASS**, and every proviso held:
1. **`csal` byte-identity across arms — HELD** exactly (`csal_max_abs_diff = 0.0`).
   The lesion does not leak into the salience seed.
2. **`ci_opponent` fires in the ablated arm — HELD** (`op_done_min_ablated = 1.0`):
   the opponent SIGNAL is preserved; only the SIGN is suppressed. The guard is on
   mint/assign only, as intended.
3. **The equiluminant figure has `lsal = 0` everywhere — HELD** (`max_lsal_intact =
   0.0`): holding L+M and S constant across figure/ground kept both opponent axes
   constant within each region, so `csal > 0` ONLY at the border (20 cells) and the
   boundary is pure-chroma.
4. **The FLOOR intact arm mints one achromatic (0,0) category — HELD**
   (`achromatic_grey_categories_intact = 1`, `n_chromatic_categories = 0`): expected,
   reported, and NOT a colour sign.

**No metric was changed to rescue anything (§5); no arm was re-run (§3.6).** The run
matched the pre-registration on the first execution.

## §9 / bench / siblings

- **Committed byte-identity:** `test_colour_identity_migrated.py` + `..._salience...`
  = **12/12** unchanged after the seed edit (achromatopsia default OFF).
- **Sibling gates green in one process:** colour-identity · colour-salience ·
  **achromatopsia (5/5)** · sdloop-vision · dimension-inference · engine-provenance =
  **48 passed**. The **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is UNMOVED** (the sdloop
  gate `test_orbit_law_arithmetic_matches_the_measured_mint_counts` passed).
- **Rung-7 named vision bench (`scripts/rung7_vision_bench.sh`, `data/` symlinked to
  canonical per §10.2):** **200 passed / 0 failed** (158.7s) — the committed baseline,
  UNMOVED. (Without `data/` present in the fresh worktree the same run is 190 passed /
  **10 skipped** / 0 failed: the 10 skips are data-availability skips, not regressions
  — 0 failed either way.)

## Scope — what is NOT shown (§8), and the named frontier

- A VALIDATION gate for the colour-STRUCTURE / colour-SIGN split ONLY. It does NOT
  build colour constancy, object colour re-ID, or the recognition "what" layer (the
  objecthood wall; named frontier).
- "Colour-defined motion" here is the DISPLACEMENT of a colour-defined boundary across
  two frames (the motion SUBSTRATE), NOT global-motion direction integration (dorsal
  MT; late-maturing, vulnerable — `VISION_VENTRAL_GROUNDING.md`; out of scope).
- The lesion is a clean flag on an armed system; it licenses nothing about WHICH
  cortical locus realises achromatopsia. Heywood & Cowey's behavioural dissociation is
  the target, not a circuit claim.
- **NAMED FRONTIER:** the other `VISION_VENTRAL_GROUNDING.md` failure-mode gates —
  apperceptive/associative, McCollough contingent aftereffect, face-inversion/Thatcher,
  crowding.

## Is the colour-structure / colour-sign split real in the build? — the plain answer

**Yes.** Ablating ONLY the categorical-colour SIGN (`ci_mint_category` + `ci_assign`,
via one OFF-by-default flag) abolishes colour categorization (2 categories → 0, 36
signs → 0) while the chromatic SIGNAL and every chromatic-STRUCTURE readout —
chromatic-border contrast (`csal` 10.0), shape-from-colour (equiluminant figure,
`lsal` 0), the colour-defined boundary and its +1-col displacement — are preserved
BYTE-FOR-BYTE, identical across arms. Neither arm is trivially null (the ablated arm's
opponent signal and border ring both fire; the intact arm categorizes correctly), the
lesion is chroma/identity-specific (a luminance edge is detected identically in both
arms), and an achromatic stimulus kills colour in BOTH arms while luminance survives.
The design's luminance-structure / colour-sign split is validated — with ZERO new Rust
and ZERO metric surgery. **Bounded to** this validation; colour constancy, object
colour, and the "what" layer remain the named, unreached frontier.
