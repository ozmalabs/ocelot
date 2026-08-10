# EFFERENCE-COPY EGOMOTION CANCELLATION — PRE-REGISTRATION (block 155000–155999)

**The GENERAL capability** (not Doom support), grounded in a confirmed
principle — **active inference / sensory attenuation**: an agent predicts the
sensory consequences of its OWN actions via an **EFFERENCE COPY** (a forward
model of its motor command), CANCELS them, and the RESIDUAL is the world / the
other. Applied to vision: predict the optic flow caused by the agent's OWN
motion (**egomotion**), cancel it, and the residual flow isolates
INDEPENDENTLY-MOVING world objects; regions that are view-fixed (≈zero observed
flow while the world flows) are the agent's own **APPARATUS** (self). ONE
self-prediction mechanism yields three things at once: (a) world/object carving
under egomotion, (b) static-background separation, (c) self-apparatus
identification. Doom (`defend_the_center`) is the EVAL that hands per-pixel
ground truth; the capability is general.

**Why turning is the tractable first case.** Pure ROTATION (turning) produces an
optic flow that is ~uniform and DEPTH-INDEPENDENT (rotational retinal slip has
no parallax; only translation/walking does). So the egomotion flow from a turn
command is well-predicted by a single gain (flow-per-turn-unit). This rung does
TURNING; translation/walking (parallax, depth-dependent) is the harder extension,
NAMED not built.

**The chain.** 152000–154000 established, on Doom with VizDoom labels-buffer
GROUND TRUTH: the value carve sees a resolved enemy (IoU 0.42 at 2×); the
object-notion motion/expansion carve works when the enemy is close/super-pixel
but 153000 found EGOMOTION (player turning) HURTS the common-fate carve
(motion 0.159 < value 0.243 under turning) because the whole scene flows. This
rung fixes the TURNING regime the principled way: cancel the self-predicted
egomotion flow, carve the residual.

## §3 clause 8 — SEED CLAIM (verbatim `seed_claim.py` / `check_claim`, run BEFORE the probe file existed)

```
$ python3 scripts/seed_claim.py 155000 155999
SEED CLAIM 155000-155999: CLEAN -- no collision DETECTED.
  Scope: 855 files with seed sinks; 573 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Unresolved-sink count at prereg time: **573** (priced, per §3 clause 8).
Seeds used within the block: `155000` (VizDoom `set_seed` + block base),
`155001`/`155002` (synthetic RNG for H1 scene / calibration). After the probe
exists, `check_claim` naturally reports these as occupied by THIS file;
excluding it returns CLEAN. No other tree file draws in the block (confirmatory
seeds never used for anything else — §3.4).

## The mechanism

- **Forward model (efference copy), GROUNDED not tuned (§13).** The turn→flow
  gain is CALIBRATED from the agent's OWN turning observations: turn with the
  scene, measure the resulting dominant/median flow = the egomotion gain
  (flow-per-turn-unit). An efference copy is a *learned forward model grounded
  in the agent's action*, NOT a magic constant. The predicted egomotion flow is
  then `E_pred = gain × turn_command` — a uniform field (rotation is
  depth-independent).
- **Cancellation is arithmetic.** `residual = observed_flow − E_pred`.
- **Apparatus identification is a mechanical readout.** Cells with ≈zero OBSERVED
  flow while the global scene flows (median |flow| ≫ 0) are the view-fixed
  self-apparatus. The zero-flow tolerance FALLS OUT of the block-matcher's own
  integer/sub-pixel floor (Otsu on |observed|), not tuned. Apparatus cells are
  folded into the reference frame (their residual set to the background zero) so
  the residual carve does not mislabel self as a world object.
- **The carve is the EXISTING Rust primitive** `segment_motion_and_track`,
  byte-for-byte unchanged, fed the residual flow instead of the raw flow.
- **Model-free baseline (the codec move, for comparison).** Cancel the
  DOMINANT / per-frame MEDIAN observed flow (global-motion compensation)
  instead of the command-predicted flow. The self-grounding claim is that
  predicting from the agent's OWN command matches or beats estimating the
  dominant flow — explicitly compared.

## Hypotheses (two-sided)

- **H1 (mechanism, SYNTHETIC — the ideal oracle).** A synthetic scene with a
  KNOWN egomotion (uniform pan) + an INDEPENDENTLY-moving object + a VIEW-FIXED
  overlay (apparatus). Predict the egomotion flow from the known motion, cancel
  it, and: **(i)** the residual carve isolates the independently-moving object
  (IoU vs its known mask) where the raw (uncancelled) carve FAILS under
  egomotion; **(ii)** the view-fixed overlay is identified as APPARATUS (≈zero
  observed flow while the world flows) and is NOT carved as a world object;
  **(iii)** static background → residual ≈ 0. Two-sided: the residual carve may
  fail to isolate the object, or the apparatus may not separate — recorded
  either way.
- **H2 (Doom, ground-truth-scored).** On `defend_the_center` with the player
  TURNING (fixed turn action, seed `155000`, ~2× downsample per 153000's
  real-time ceiling), predict the egomotion flow from the agent's OWN turn
  command via the calibrated forward model, cancel it, carve the residual →
  the enemy. Score enemy IoU vs the labels buffer, COMPARED TO the uncancelled
  carve under turning (153000's hurt baseline). Also identify the self-apparatus
  (HUD/weapon) as the ≈zero-observed-flow region under turning. Two-sided: if
  cancellation recovers the enemy under turning where the raw carve is hurt →
  CONFIRM; if the enemy's own motion is still sub-pixel/distant (154000's
  aperture wall persists — cancellation does NOT fix sub-pixel) → the honest
  bimodal DEGRADE, named.

## Statistic (exactly)

- Per-object **IoU by POSITION** (Jaccard of cell-sets) between a carved region
  and the ground-truth object mask; best over carved regions. Raw distribution +
  mean/median/max.
- **Apparatus identification**: the recovered zero-observed-flow region's IoU to
  the known apparatus mask (H1) / to the DoomPlayer weapon-sprite label (H2);
  and the observed-flow magnitude on apparatus vs world regions.
- **Static-background residual**: mean |residual| over background cells (H1;
  exact integer arithmetic → expect 0.0).
- **Efference-vs-dominant**: object IoU under command-predicted cancellation vs
  median-observed cancellation, on the same field; and the recovered gain from
  the two paths.

## n, FIXED IN ADVANCE

- H1: a deterministic scene grid — the primary egomotion scene + the controls
  (no-egomotion no-op; static-scene+egomotion; moving-object-no-egomotion;
  apparatus-not-carved; moving-object-not-apparatus). A constructed mechanism
  grid, not a sample.
- H2: the enemy-present frames of a single seeded turning capture (seed
  `155000`, up to 60 tics), plus a calibration turn of the same length.

## Decision rule

- **H1 (i)** supported iff the residual carve's object IoU exceeds the raw
  carve's object IoU by a material margin under egomotion AND the residual carve
  object IoU is high (> 0.5). **(ii)** supported iff the apparatus is identified
  (apparatus-region observed-flow ≈ 0 while world flow ≠ 0; apparatus IoU high)
  AND a real moving object is NOT mislabeled apparatus (its observed flow ≠ 0).
  **(iii)** supported iff static-background residual ≈ 0 (< 0.01).
- **Controls:** no-egomotion → cancellation is a no-op (predicted flow ≈ 0),
  carve byte-identical to the uncancelled carve; static-scene + egomotion →
  residual ≈ 0 everywhere (nothing carved); moving-object + no-egomotion →
  carved identically with/without cancellation.
- **H2** supported iff cancelled enemy-IoU (mean) > uncancelled enemy-IoU on the
  same turning capture AND clears 153000's ~0.015 turning floor. Otherwise a
  NAMED DEGRADE (the sub-pixel aperture wall persists), recorded. The apparatus
  (weapon) is expected to be cleanly identified as zero-flow either way.
- A NULL is a real result (§7), never rescued by changing the measure (§5).

## Prediction (stated in advance, with provisos)

- **H1 (i)** will hold: under a fragmenting textured background (the Doom-faithful
  regime), the largest coherent uniform-flow region is the zero-flow apparatus,
  so the RAW `segment_motion` picks the APPARATUS as its dominant reference and
  inverts figure/ground — the world becomes "figure" and the small object's IoU
  collapses. Cancellation forces the true background (residual ≈ 0) to be the
  reference and, with the apparatus folded into it, the object is the sole clean
  figure. **Proviso:** if the raw carve happens to isolate the object anyway
  (background stays dominant), the decisive contribution is (ii) apparatus
  identification, not (i) — reported honestly.
- **H1 (ii)/(iii)** will hold cleanly: zero observed flow is exactly recoverable
  in integer arithmetic; subtracting a uniform E from a uniform background gives
  exactly 0.
- **H2 is genuinely uncertain** and I predict the BIMODAL DEGRADE: the enemy is
  sub-pixel/distant in most turning frames (154000's wall), and cancelling a
  uniform egomotion does NOT create sub-pixel signal where there was none — so
  the enemy IoU will likely clear the floor only on the few super-pixel
  close-approach frames and floor elsewhere. The APPARATUS (weapon), by
  contrast, is large and view-fixed and will be cleanly identified as zero-flow.
- **Efference vs dominant.** On the SYNTHETIC (object + apparatus occupy enough
  of the frame to bias the per-frame median), command-prediction will be
  unbiased where median-cancellation is pulled off the true egomotion — the
  self-grounding advantage. On Doom (enemy sub-pixel, background dominates the
  median) the two will be ~equal — reported.

## §13 — every number falls out of a natural process

- The turn→flow **gain** is MEASURED from the agent's own calibration turn
  (median observed flow), never set. It is the same quantity the model-free
  baseline estimates per-frame — the comparison is exactly whether the
  self-grounded (command) source matches the observation-grounded (median) one.
- The zero-flow **apparatus tolerance** falls out of the flow field's own
  magnitude distribution (Otsu / the block-matcher's integer floor), not tuned.
- The carve **tolerance** is the existing `segment_motion` Otsu, unchanged.
- Grid / downsample / turn-rate / block are DECLARED sensor residuals (as in
  152000–154000), stated up front, not tuned to the score.

## Architecture (CLAUDE.md — the agent is Rust)

The grouping is the EXISTING Rust primitive `segment_motion_and_track`,
byte-identical (no Rust added, no seed, no default moved — NEW FILES ONLY, so
the shipped carve path is byte-identical BY CONSTRUCTION). The forward model
(turn command → predicted flow), the cancellation subtraction, the apparatus
zero-flow readout, and the affine gain fit are MECHANICAL sensor / measurement
transforms over arrays (no conditional over graph state, no agent decision — the
peer of `vector_field` / `divergence_field` / `quantize`). The VizDoom driver is
a world adapter; the agent's turn command is a known world-adapter fact (the
action it issued); the labels buffer is the SCORING ORACLE, never fed to the
eye. Scoring is set arithmetic (IoU) by POSITION, never by cross-process
region-id.

## Gate

`tests/test_efference_egomotion_migrated.py` — H1 (residual carve isolates the
independent object under egomotion where raw fails, ABLE TO FAIL; apparatus
identified; static → residual ≈ 0), the controls (no-egomotion no-op;
apparatus-not-carved; moving-object-not-apparatus), H2 (Doom enemy IoU under
turning > uncancelled baseline OR the named bimodal DEGRADE), the
efference-vs-dominant comparison, and byte-identity of the carve path when
cancellation is off. Reads measured/graph values, never exact-d2, skips if
VizDoom absent.
