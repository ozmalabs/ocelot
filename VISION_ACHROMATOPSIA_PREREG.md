# VISION — CEREBRAL ACHROMATOPSIA: colour-SIGN / chromatic-STRUCTURE dissociation (PRE-REGISTRATION)

*Frontier rung T7. A LESION-VALIDATION gate for the design's luminance-structure /
colour-sign split (`VISION_VENTRAL_GROUNDING.md` failure-mode gate 5;
`VISION_PROTOCOL.md` binding). Written and COMMITTED BEFORE the confirmatory run
(§3). Ablation flag OFF by default = INTACT; the ablation is the experimental arm
(§9). Seeds (burned-seed ledger) **42000–42999** — none used before this rung
(highest prior burn: 39099).*

## STEP 1 — AUDIT (§12.4, file:line): is this a clean flag-level ablation?

**VERDICT: YES — a clean flag-level ablation, faithful to the neurology, with the
chromatic-structure readouts fully composable from the salience/opponent layer
INDEPENDENT of the identity sign.**

The colour system on this substrate is TWO separate seeds with INDEPENDENT flags:

- **`seeds/vision_colour.json`** (SALIENCE / chromatic STRUCTURE), gated on
  `ColourParams.{salience,colour}`:
  - `cc_contrast` (`vision_colour.json:24`) — per cell, `csal` = the surround-
    relative cone-opponent contrast MAGNITUDE (`Sqrt` over the L−M and S−(L+M)
    axes vs the neighbour mean) and `lsal` = the same on the achromatic axis L+M.
    Reads ONLY raw cones + neighbours; NEVER reads `crg`/`cby`/a category.
  - `cc_salience` (`vision_colour.json:731`) — combines into `Region.residual`
    (`lsal + csal + lsal·csal`).
  - This layer is the CHROMATIC EDGE / BORDER / SHAPE-FROM-COLOUR / colour-defined
    boundary computation. It is gated on `salience`/`colour`, **not** on identity.
- **`seeds/vision_colour_identity.json`** (categorical SIGN), gated on
  `ColourIdentityParams.identity`:
  - `ci_opponent` (`:22`) — the integer opponent VALUE `crg=cL−cM`, `cby=cS−(cL+cM)`
    (the chromatic SIGNAL).
  - `ci_mint_category` (`:150`) — MINTS an MDL-gated `ColourCategory` quantum.
  - `ci_assign` (`:566`) — assigns each region its nearest category SIGN.

**The lesion the task names** is disabling the colour-IDENTITY sign layer
(`ci_mint_category` + `ci_assign`) while the chromatic-STRUCTURE layer
(`cc_contrast`) stays ON. In cerebral achromatopsia (Heywood & Cowey 1997 *TICS*)
the cone-opponent SIGNAL is PRESERVED — the patient still detects chromatic
borders, gets shape-from-colour, and colour-defined motion direction — while
conscious colour NAMING/categorization is abolished. So the faithful lesion
suppresses **minting + assignment of the category sign** and PRESERVES both
`cc_contrast` (chromatic structure, a different seed) AND `ci_opponent` (the
opponent signal).

**The `identity` flag alone is a coarser lever:** setting `identity=0` disables the
WHOLE identity seed including `ci_opponent`, and its default (0) is the *ablated*
state — so it neither preserves the opponent signal nor gives intact-by-default. We
therefore add a dedicated **`achromatopsia`** ablation flag on the existing
`ColourIdentityParams` node (new attr, **default 0.0 = INTACT**, §9) that guards
**only** `ci_mint_category` and `ci_assign` (`Lt(achromatopsia, 0.5)`), leaving
`ci_opponent` and the entire salience seed untouched. This is pure GRAPH DATA — a
flag on a params node, not a Python code path (PROTOCOL §0; the guard is the same
`PickUnique(ColourIdentityParams)` idiom the `identity` guard already uses). With
the flag OFF (default) the identity rules are byte-identical to the committed seed
(verified: the committed `test_colour_identity_migrated.py` reproduces exactly).

**Chromatic-structure readouts — all composable from the salience/opponent layer,
independent of the categorical sign:**

| readout | source | independent of identity sign? |
|---|---|---|
| chromatic border / edge / contrast | `csal` (`cc_contrast`, salience seed) | YES — reads raw cones only |
| shape-from-colour (equiluminant figure) | `csal`/`residual` with `lsal=0` | YES — salience seed |
| colour-defined boundary | `csal` ring at the figure/ground border | YES — salience seed |
| colour-defined boundary DISPLACEMENT (motion substrate) | shift of the `csal` centroid across two frames | YES — salience seed |
| opponent SIGNAL | `crg`/`cby` (`ci_opponent`) | preserved (not lesioned) |
| colour categorization / naming (LESIONED) | `n_categories`, `sign_*` (`ci_mint_category`/`ci_assign`) | this IS the sign — abolished when `achromatopsia=1` |

The lesion is a clean flag; every preserved chromatic-structure readout is measured
from `cc_contrast` (or `ci_opponent`), which the flag does not touch.

## Hypothesis (two-sided, §3.1)

**H1 (DISSOCIATION):** With the colour-IDENTITY sign layer ablated
(`achromatopsia=1`), colour CATEGORIZATION fails (0 `ColourCategory` minted, 0 signs
assigned) while chromatic-STRUCTURE readouts (chromatic-border `csal`, shape-from-
colour, colour-defined boundary, colour-defined boundary displacement) are BYTE-FOR-
BYTE PRESERVED, identical to the intact arm. **H0:** ablating identity either (a)
leaves categorization intact, or (b) also degrades a chromatic-structure readout
(`max|csal_intact − csal_ablated| > 0` or the boundary/displacement differs) — in
which case the split is NOT real in the build (a clean negative, reported + diagnosed
per §5/§7).

## The statistic, exactly (§3.2)

Four deterministic arms + one §9 off-day. All values exact (integer counts / exact
float equality); no thresholds are swept, no metric is re-read to rescue a failure.

### Arm DISSOCIATION (headline) — equiluminant colour-defined figure
Stimulus: 6×6 cone-cell grid, all cells L+M=20 (EQUILUMINANT). Ground = colour B
(`cL=5,cM=15,cS=20` ⇒ `crg=−10,cby=0`); a 3×3 figure at rows 1–3, cols 1–3 = colour
A (`cL=15,cM=5,cS=20` ⇒ `crg=+10,cby=0`). Both colours recur ≥3 (A:9, B:27), so both
categorize in the intact arm. Run BOTH arms (`achromatopsia=0` intact,
`achromatopsia=1` ablated) with `salience=1,colour=1,identity=1`.
- **categorization:** `n_categories` — PASS iff intact = 2 (A(10,0) m=9, B(−10,0)
  m=27) and ablated = 0; `n_signs_assigned` intact = 36 (all `sign_dist=0`), ablated
  = 0.
- **chromatic structure PRESERVED:** `max_csal_ablated > 0`;
  `n_csal_positive` (cells with `csal>0`, the chromatic-border ring) equal in both
  arms and > 0; `max|csal_intact − csal_ablated| == 0.0` (byte-identical);
  `max_lsal == 0` (equiluminant ⇒ structure is purely chromatic — shape-from-colour).
- **colour-defined boundary displacement (motion substrate):** frame2 = figure
  shifted +1 col (cols 2–4); the `csal`-positive centroid column shifts by exactly
  +1 in BOTH arms and identically between them.
- **PASS(DISSOCIATION)** = categorization lost (2→0) AND every chromatic-structure
  readout preserved & byte-identical across arms.

### Arm CONTROL_VALIDITY (§1.1 — NOT trivially null; neither side dead)
From the same DISSOCIATION scene:
- **ablated structure ALIVE (not a dead instrument):** `max_csal_ablated > 0` AND
  `op_done_ablated == 1` for every cell (`ci_opponent` fired ⇒ the opponent signal
  is computed) AND `n_csal_positive_ablated > 0`. The ablated "0 categories" is a
  GENUINE suppression on live machinery, not a silent floor (§1.1: an absence off a
  dead arm is a lookup, not a measurement).
- **intact identity ALIVE:** `n_categories_intact == 2` AND `all_signs_correct`
  (every cell recognized as its own category at `dist 0`).
- **PASS(CONTROL_VALIDITY)** = ablated structure fires AND intact categorizes.

### Arm SPLIT_CLEAN (luminance structure fully intact throughout)
Stimulus: a LUMINANCE-defined vertical edge, ZERO chroma — left half
`cL=cM=10,cS=20` (L+M=20, `crg=0,cby=0`), right half `cL=cM=20,cS=40` (L+M=40,
`crg=0,cby=0`). Run BOTH arms.
- **PASS(SPLIT_CLEAN)** = `max_lsal > 0` at the luminance border, IDENTICAL intact
  vs ablated (`max|lsal_intact − lsal_ablated| == 0`), AND `max_csal == 0` (no chroma)
  — the colour lesion is chroma/identity-specific and does NOT touch the luminance
  structure path.

### Arm FLOOR (achromatic ⇒ no colour, in EITHER arm; not confounded with luminance)
Stimulus: an ACHROMATIC luminance ramp — each cell `cL=cM=v, cS=2v` (so `crg=0`,
`cby=0`) with `v` increasing across the 6×6 grid (luminance varies, chroma absent).
Run BOTH arms.
- **PASS(FLOOR)** = `max_csal == 0` (no chromatic structure, BOTH arms) AND
  `n_chromatic_categories == 0` (a category with `|crg|+|cby|>0`; BOTH arms — no
  colour SIGN) AND `max_lsal > 0` (luminance structure present — the achromatic
  condition kills colour REGARDLESS of the identity flag, so the dissociation is not
  a luminance artifact). The intact arm mints exactly one *achromatic* origin
  category at (0,0) (all cells share chroma (0,0)); it is reported honestly and is
  NOT a colour sign (`|crg|+|cby|=0`).

### Arm OFFDAY (§9)
DISSOCIATION scene, ALL flags at default (`salience=colour=identity=achromatopsia=0`).
- **PASS(OFFDAY)** = `max_cc_done == 0` (`cc_contrast` never fired), `n_categories ==
  0`, `max_op_done == 0`, `max_sign_rg == 0` — the seeds are inert; §9 byte-identity.

## n, fixed in advance (§3.3)
All five arms are DETERMINISTIC (fixed synthetic stimuli, exact-value statistics) —
no sampling, so n is not a power question. The one stochastic control is inherited,
not re-run: the committed colour-identity 100-seed noise floor
(`arm_N`, seeds 35000–35099) already establishes 0/100 false mints; this rung does
not re-open it. Seeds **42000–42999** are ALLOCATED to this rung and, being fully
deterministic, **none are consumed** (recorded for the ledger; a later stochastic
extension may draw from this block).

## Confirmatory seeds never used before (§3.4)
42000–42999, previously unburned (highest prior burn 39099). This rung burns none
(deterministic); the block is reserved.

## Decision rule (§3.5)
Report ALL FIVE arms. Headline claim (the split is real) holds iff DISSOCIATION AND
CONTROL_VALIDITY AND SPLIT_CLEAN AND FLOOR AND OFFDAY all PASS. If DISSOCIATION fails
because ablating identity ALSO changes a chromatic-structure readout
(`max|csal_intact−csal_ablated| > 0`, or boundary/displacement differs), the split is
NOT clean in the build — a CLEAN NEGATIVE, reported and diagnosed (§7), NOT rescued
by re-reading (§5). A null on CONTROL_VALIDITY (a dead ablated arm) invalidates the
dissociation (§1.1) and is reported as such.

## Exactly the listed tests. No sweeps (§3.6)
The five arms above and the committed `test_colour_identity_migrated.py` /
`test_colour_salience_migrated.py` byte-identity re-run. No parameter search; a
further attempt needs a NEW prereg with a NEW mechanism-level hypothesis.

## My prediction, stated in advance (§3.7)
I predict **all five arms PASS**. Provisos:
1. **csal byte-identity across arms.** `cc_contrast` reads only raw cones +
   neighbours and is a different seed from the lesioned rules; the `achromatopsia`
   guard touches only `ci_mint_category`/`ci_assign`. So `csal`, `lsal`, `residual`
   must be BIT-IDENTICAL intact vs ablated. If they differ, either the lesion leaks
   into the salience seed (it must not) or the two seeds share unexpected state — a
   real finding, reported.
2. **`ci_opponent` fires in the ablated arm** (`op_done=1`, `crg/cby` computed): the
   opponent SIGNAL is preserved, only the SIGN (mint/assign) suppressed — the
   faithful achromatopsia. If `op_done=0` in the ablated arm I mis-placed the guard
   (would have gated `ci_opponent` too) — check and report.
3. **The equiluminant figure has `lsal=0` everywhere** (all L+M=20), so the boundary
   is traced by chroma alone — shape-from-colour. The colour results doc warns
   `cby=S−(L+M)` is not luminance-invariant; here L+M AND S are held constant across
   figure/ground (both cS=20), so both opponent axes are constant within each region
   and `csal` is non-zero ONLY at the border. If interior `csal≠0`, the stimulus
   leaked luminance — I would correct the STIMULUS (stricter, §1.1), not the measure.
4. **The FLOOR intact arm mints one achromatic (0,0) category** (all cells cluster at
   the origin, count 36 ≥ 3). This is expected and reported; it is NOT a colour sign
   (`n_chromatic_categories=0`). If it minted a chromatic category, the stimulus was
   not achromatic — check.

## Scope — what is NOT shown (§8)
- A VALIDATION gate for the colour-STRUCTURE / colour-SIGN split ONLY. It does NOT
  build colour constancy, object colour re-ID, or the "what" recognition layer (the
  objecthood wall; named frontier).
- "Colour-defined motion" here is the DISPLACEMENT of a colour-defined boundary
  across two frames (the motion SUBSTRATE), NOT global-motion direction integration
  (dorsal MT; late-maturing, vulnerable — `VISION_VENTRAL_GROUNDING.md`; out of
  scope).
- The lesion is a clean flag on an armed system; it licenses nothing about WHICH
  cortical locus realises achromatopsia (Heywood & Cowey's dissociation is the
  behavioural target, not a circuit claim).
- NAMED FRONTIER: the other `VISION_VENTRAL_GROUNDING.md` failure-mode gates
  (apperceptive/associative, McCollough, face-inversion/Thatcher, crowding).

## Provenance (§10) — recorded in the RESULTS on the run.
