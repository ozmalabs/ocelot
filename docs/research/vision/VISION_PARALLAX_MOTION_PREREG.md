# PRE-REGISTRATION — DOES THE PARALLAX CARVE SURVIVE REAL *MOTION*? (rung 125000)

*Committed BEFORE any confirmatory number. Only pilots on ALREADY-BURNED seeds
(116000–116039) have been computed (the §3-clause-3 power analysis). Nothing in
this file is edited after the first confirmatory number.*

## THE ONE VARIABLE THIS RUNG CHANGES

The parallax carve is CONFIRMED on synthetic texture (116000) AND on real BSDS
photometry (124000). **But BOTH imposed the parallax BY HAND: each depth plane
got ONE uniform, hand-set horizontal shift (a "windowed slide").** 124000 named
the last unmet variable: real **MOTION**.

**This rung changes exactly that one variable.** The image displacement must
FALL OUT of depth + camera motion via PERSPECTIVE PROJECTION, not be a hand-set
uniform shift. A moving pinhole camera over a scene at depth Z produces image
displacement `d = f·T / Z` — nearer surfaces (small Z) sweep FASTER. The agent's
efference copy is its KNOWN camera pose Δ (the translation T, and the gaze that
FIXATES the reference plane); it subtracts the fixated plane's predicted flow and
the residual for the OTHER planes = `f·T·(1/Z_i − 1/Z_ref)` separates them BY
DEPTH — the depth ORDER must EMERGE from the residual, never be told.

**REAL BSDS300 photometry is kept throughout** (proven in 124000 — do NOT
reintroduce that variable; a FALSIFY must be attributable to MOTION, not
texture). The carve is REUSED byte-for-byte (`parallax_char.group_common_fate` /
`domains.motion_group_world.vector_field` — the same mechanism the load-bearing
`parallax_efference` seed encodes, proven in 116000's graph arm). **NO Rust, NO
new seed** (a measurement reusing the carve, exactly like 124000).

**FRAME/CONTINUUM INVARIANT (CLAUDE.md).** The projection carries continuous
(f, T, Z, tilt, rot) as a CROSS-FRAME map; the OBSERVABLE displacement is the
STEPPED integer render (`np.round` — the sensor senses integers). Continuous
parameters live only in the map that PRODUCES the frame, never in a frame
coordinate. The far background (Z=300, sub-pixel parallax rounding to 0) is the
honest statement of this: the map is continuous, the observable is stepped.

**NO fabrication, NO wrap (124000 discipline):** every displaced pixel is a REAL
scene neighbour, sourced from a crop WIDER than the grid (`off0 = max shift`). A
toroidal roll would inject a false wrap-seam — a new confound, not motion.

## HYPOTHESES (two-sided, both stages)

**STAGE A — fronto-parallel planes under camera TRANSLATION.** Displacement is
still piecewise-constant per plane (Z constant over a fronto-parallel plane), so
the projected scene is the honest MOTION-DERIVED analog of the windowed slide.

- **H_A0 (null):** a motion-derived carve does no better than a static camera —
  eff ≈ 1 (one blob), or the depth order is no better than chance.
- **H_A1:** the carve recovers the correct surface count (eff ≈ N) AND the depth
  order is correct (nearer plane = larger residual magnitude), CI-separated from a
  static-camera control (T=0 → eff ≈ 1).

**STAGE B — a SLANTED plane and/or a camera ROTATION.** Z varies WITHIN a surface
(slant) or the camera rotates, so the flow becomes a GRADIENT WITHIN one surface —
NOT one vector. Common-fate grouping ASSUMES surface = one motion. This is the
real test.

- **H_B0 (null):** the within-surface gradient makes no difference — the carve
  behaves as in Stage A at every gradient.
- **H_B_confirm:** common-fate still recovers the surface(s) despite the gradient
  (it is a TRANSITIVE flood, more robust than its single-vector assumption).
- **H_B_falsify:** the slanted/rotated surface SHATTERS into spurious pieces
  (eff ≫ true count) or MERGES WRONGLY (eff < true count / depth order lost) →
  common-fate grouping is the thing that breaks under real motion, and the named
  next objective is **common-fate → AFFINE-FLOW grouping** (group by a consistent
  local flow AFFINE model + subtract the FULL known flow field, not a single
  vector).
- **H_B_degrade:** holds for a small gradient, breaks past a measured magnitude —
  report the threshold, which must FALL OUT (of the sensor tolerance τ), not be
  picked.

## THE STATISTICS (exactly these; no sweeps beyond the listed configs)

Unit of analysis = the SEED. Speck-robust per the 84000 trap (raw count includes
confab specks): **participation ratio `eff = 1/Σpᵢ²`** and **`largest_frac`**, at
BOTH tolerances τ ∈ {exact 0, sensor √5} (the 94000 Otsu-within-aperture
accuracy tolerance = ‖(1,2)‖, MEASURED not chosen). 95% bootstrap CI (1000
resamples, fixed `default_rng(0..999)`). The DEPTH-ORDER read-off:
`depth_order_correct` = (bands ranked by recovered residual velocity == bands
ranked by true 1/Z), and Spearman `depth_rank_rho`; reported as a per-seed rate.

**Confirmatory arms (all REAL BSDS random crops, n=80, seeds 125000–125079):**

1. **BASELINE (floor re-earn):** windowed slide `[0,3,6]` (`make_real_scene`,
   reproducing 124000) — the in-tree anchor for the exact windowed-slide-vs-
   true-motion comparison.
2. **A1 — Stage A motion:** projected fronto-parallel, depths `[300,10,5]`,
   base `f·T=30` → shifts `[0,3,6]` (far background = sub-pixel, rounds to 0),
   ref = middle. Report eff, largest, `depth_order_correct` rate, and
   byte-identity to arm 1.
3. **A2 — static control:** base=0 → b==a → eff.
4. **B1 — single slanted plane:** one full-frame plane (Z0=7.5, d0=4), tilt ∈
   {0,0.2,0.4,0.6,0.8} (fractional depth variation across the half-width). eff at
   both τ; per-block displacement step.
5. **B2 — 3 planes, MIDDLE slanted:** depths `[300,10,5]`, tilt ∈ {0,0.2,0.4,0.6}
   on the middle band. eff(√5), `depth_order_correct` (merge-wrongly test).
6. **B3 — translation + camera ROTATION:** depths `[300,10,5]`, rot ∈
   {0,0.02,0.04,0.08} rad. eff(√5), `depth_order_correct`.
7. **B4 — PURE rotation (no depth):** base=0, rot ∈ {0,0.02,0.04,0.08}. eff at
   both τ (does rotation invent spurious surfaces?).

The tilt/rot/depth values are STIMULUS CONFIGURATION (the independent variable,
the same standing as 116000's shifts and apertures), reported in full across each
sweep — never cherry-picked. **No measured quantity is compared against a chosen
number to decide a verdict**; the discriminators are a participation ratio, a
fraction, and a rank-order, and any threshold FALLS OUT of τ.

## n, FIXED IN ADVANCE (power analysis on burned seeds 116000–116039)

The effects are large and CIs tight at n=40: Stage A projected eff(√5) =
3.11 [3.04, 3.17] vs static 1.00 [1.00,1.00] (separation ~2.1, ≫ CI width ~0.13),
depth_order 40/40; rotation rot=0.02 eff 2.44 [2.29,2.61] vs rot=0 3.11
[3.04,3.17], CI-separated. **n=80** (matching 116000/124000) tightens all CIs
~√2 and is amply powered for every listed contrast. Confirmatory seeds
**125000–125079**, never used for anything.

## DECISION RULES (including what a null means)

- **STAGE A — CONFIRM** iff ALL co-hold at BOTH τ: projected DEPTH eff CI ⊂
  [2.5, 3.5]; largest_frac < 0.5; `depth_order_correct` rate ≥ 0.90; CI-separated
  from the static control (eff ≈ 1.0); byte-identical to the windowed-slide
  baseline on all 80 seeds. **NULL (H_A0)** if eff ≈ 1 or depth order ≤ chance.
- **STAGE B — a SPLIT verdict is expected and is the finding.** Registered per
  arm:
  - **B1/B2 slant — CONFIRM at √5** iff the carve recovers the true count
    (single plane eff ≈ 1; 3-plane eff ⊂ [2.5,3.5] with depth order ≥0.90) for
    tilt up to a threshold, quantifying the tolerated within-surface gradient
    (max per-block step). **DEGRADE** if it holds for small tilt and breaks past
    a per-block step that must equal ≈ τ (falls out). **FALSIFY** if even the
    gentlest gradient (tilt 0.2, per-block step 1) shatters at √5.
  - **τ=0 is reported as the exact-equality FALSIFY** if any non-zero gradient
    shatters the surface into integer-displacement strips (eff climbs with tilt).
  - **B3/B4 rotation — CONFIRM** if the carve survives a small rotation (eff
    in-band, depth order ≥0.90). **FALSIFY** if a small rotation (rot ≤ 0.04)
    drives eff out of band OR `depth_order_correct` below 0.90 → names
    common-fate → affine-flow + full-field efference as the next rung. A FALSIFY
    here is a FIRST-CLASS result; the carve is NOT rescued.

## PREDICTIONS, STATED IN ADVANCE (with provisos)

1. **Stage A: CONFIRM (~95%).** Projected eff(√5) ≈ 3.1, byte-identical to the
   windowed slide, depth_order 100%, static eff = 1.0. *Proviso:* the far-band
   sub-pixel parallax rounds to 0, so the far plane's residual is exactly −3 (an
   honest distant background); if the crop is too flat the far band could confab.
2. **Stage B slant: DEGRADE at √5, FALSIFY at τ=0 (~85%).** At √5, common-fate
   TOLERATES the within-surface gradient (single-plane eff ≈ 1; 3-plane eff ≈ 3,
   depth order preserved) up to a per-block step ≈ √5, because it is a transitive
   flood — MORE robust than its single-vector assumption. At τ=0, any gradient
   shatters the plane into integer strips (single-plane eff climbs 1→~6 with
   tilt). *Proviso that may break:* the exact tilt at which √5 breaks; the
   3-plane merge-wrongly may appear at higher tilt than swept.
3. **Stage B rotation: FALSIFY (~80%).** A small camera rotation (rot ≥ 0.02)
   corrupts the depth carve — `depth_order_correct` collapses (100% → ~40% at
   0.02, → 0% at 0.04) and eff explodes at 0.08 — because rotation's within-field
   (curvature) flow gradient cannot be nulled by a SINGLE-vector efference
   subtraction nor separated by common-fate from depth parallax. This NAMES the
   next objective: common-fate → affine-flow grouping + full-field efference
   subtraction. *Proviso that may break:* the rot onset threshold; pure rotation
   (B4) should NOT invent spurious surfaces at gentle rot (eff ≈ 1 at √5).

## CONTROLS (§6) AND WHAT EACH ARM CORRESPONDS TO

- **Static camera (A2, base=0):** the world under NO ego-motion — b==a, no flow,
  one blob. The correct "no motion" null (not "no input").
- **Byte-identity to the windowed slide (A1 vs baseline):** proves the ONLY
  change from 124000 is that the shift is DERIVED, not that the pixels moved.
- **Pure rotation with no depth (B4):** isolates rotation's flow from parallax —
  a rotation-only field has no depth surfaces, so any surfaces it mints are
  spurious.
- **Both τ reported (exact 0 AND √5):** the verdict must be stated at both, as in
  116000/124000.

## §13 — WHERE EVERY NUMBER COMES FROM

- **τ FALLS OUT:** exact τ=0 (integer equality, NO NUMBER) and √5 (94000's
  MEASURED Otsu-within-aperture tolerance = ‖(1,2)‖). Verdicts reported at both.
- **The slant shatter threshold FALLS OUT of τ:** a surface shatters when the
  adjacent-block displacement STEP exceeds τ (‖Δv‖ > τ). At √5 a step of 2 still
  merges, a step of 3 shatters — the threshold is the sensor's own tolerance, not
  picked. Reported as the tilt/gradient at which it crosses.
- **The manufacturing knobs, NAMED:** depths Z, base f·T, tilt, rot — all
  STIMULUS/CAMERA CONFIGURATION (the independent variable), reported across each
  full sweep so the bounds are EXHIBITED, not tuned around. The carve introduces
  NO new constant (only τ and the −1/0/1 sentinels, inherited).
- **The sensor bound the true-motion carve INHERITS (94000):** the SAD sensor
  confabulates where local contrast < 0.4 block-std (unreachable in BSDS at this
  band width, 124000) and silent-misses on straight edges (aperture problem).
  True motion's within-surface gradient may INTERACT with it: a slant that pushes
  a block toward a low-contrast crop region compounds the confab. Stated, not
  swept.

## SEED CLAIM — `check_claim(125000, 125999)`, verbatim (§3 clause 8), pre-run

```
SEED CLAIM 125000-125999: CLEAN -- no collision DETECTED.
  Scope: 827 files with seed sinks; 515 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

CLEAN pre-run. The confirmatory seeds are `range(125000, 125080)` (the `range`
CLI blind spot — `seed_audit` will report the `default_rng(sd)` sites as unknown
sinks, disclosed post-run). Bootstrap CIs use fixed `default_rng(0..999)`
resampling generators (the parallax rungs' exact `_ci`), not scene seeds.

## ENGINE, ORACLE, PROVENANCE (§10) — the plan

- Engine built IN THIS TREE by `scripts/engine_build.sh` (`own`); Rust source
  byte-identical to canonical (a shared build would also be legitimate). Term
  index 180 UNUSED. `provenance_line()` printed from INSIDE the measuring process
  into `results/parallax_motion.json`, asserted at start/mid/end and re-verified
  after (`provenance_stable`). `source_match ∈ {own, shared}` asserted (never a
  literal build hash). Provenance gate its OWN step, first.
- ORACLE `bash scripts/rung7_vision_bench.sh` = 222/0 BEFORE and AFTER.
- ≤2 workers (`OMP_NUM_THREADS=2`); `os.getloadavg()` recorded; NO wall-clock
  quantity is a verdict.
- Own gate `tests/test_parallax_motion_migrated.py` (byte-identity, no-
  fabrication, static control, depth-order-falls-out, slant shatter-at-0/survive-
  at-√5, no tuned threshold), positive-controlled.
