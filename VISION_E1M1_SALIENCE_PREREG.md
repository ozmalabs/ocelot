# E1M1 + SALIENCE WIRING — PRE-REGISTRATION (block 156000-156999)

*Written and committed BEFORE the E1M1 run. VISION_PROTOCOL §3.*

`SEED CLAIM 156000-156999:` **CLEAN** — the verbatim `check_claim` verdict is in
the clause below.

## What this rung is

A **WIRING** rung (the supervisor's words: "this should be a case of wiring").
No new perception mechanism. Two existing pieces are connected and SCORED against
VizDoom's labels-buffer ground truth:

1. Switch the Doom eye probe from the bundled `defend_the_center` scenario to the
   **REAL map E1M1** (real `DOOM.WAD`, scripted deterministic walk).
2. Wire the EXISTING salience signal — Rust `memory::order_n_shape_salience`,
   exposed as `substrate_rs._native.Substrate.shape_salience(seq) -> float`, the
   same operator the effort dial's `salience_threshold` consumes — to RANK the
   carved-region trajectories by surprise.

Reused unchanged: the value/motion carve (`native.segment` / `native.segment_motion`
via `falling_world`), the region read-back via `has_region`/`within`, the IoU
scorer, and the efference-copy egomotion cancellation (`efference_carve`,
`calibrate_gain`) from blocks 152000–155000. **No Rust added. No seed consumed
for graph data. New files only** (`scripts/e1m1_salience_probe.py`,
`tests/test_e1m1_salience_migrated.py`, this doc, the results doc), so the shipped
carve path is byte-identical by construction and every committed result reproduces.

## §3 clause 8 — the `check_claim` output, verbatim

```
SEED CLAIM 156000-156999: CLEAN -- no collision DETECTED.
  Scope: 856 files with seed sinks; 573 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The block base 156000 is used as the VizDoom seed and RNG base; the range is
reserved for this rung.

## The three deliverables, each pre-registered two-sided

### W1 — E1M1 carve vs defend_the_center

**Statistic.** Per-GT-object best IoU of the value carve (existing `native.segment`,
L=4 quantization) against the downsampled labels buffer, plus false-positive
regions/frame and carve ms/frame. Grid: **down=2 → 120×160** ("~2× downsample per
the real-time ceiling"). The SAME carve is run on `defend_the_center` at the
identical grid/level for an apples-to-apples comparison, and the committed
`results/eye_on_doom.json` (down=4, 80×60) baseline is cited.

**Prediction.** E1M1's added complexity (many wall textures, doors, corridors,
decorations) FRAGMENTS the value carve — false-positive regions/frame RISE vs
`defend_the_center`, and absolute object IoU DEGRADES (the map is far richer than
a single blob on a bare arena). The win is that the pipeline **runs end-to-end on
the real map** and produces a ground-truth-scored number, not that IoU improves.
A null (E1M1 IoU ≈ defend_the_center IoU, fp/frame ≈ equal) would say the arena's
bareness was not what carried the earlier score.

### W2 — salience ranks the ground-truth objects (THE HEADLINE)

**The wiring.** Carved regions are tracked across frames by a mechanical
nearest-overlap association (no GT). Each track yields three 1-D trajectories —
centroid-x, centroid-y, area — and its salience is
`max(shape_salience(cx), shape_salience(cy), shape_salience(area))` using the
EXISTING `Substrate.shape_salience`. High for a directed/looming/moving track,
zero for a flat (view-fixed) one, by the operator's own construction.

**Statistic.** (a) mean salience per GT category — MONSTER (live enemies),
ITEM (barrels/armour/decor that LOOM as the agent approaches), APPARATUS
(the view-fixed DoomPlayer weapon sprite), BACKGROUND (walls/floor). (b) AUC of
salience separating FOREGROUND (monster∪item) from APPARATUS, and FOREGROUND from
BACKGROUND. (c) salience@k: is a GT foreground object's best track in the top-K
most-salient tracks, swept k. GT is used ONLY to attribute a track's category for
SCORING — never in the salience computation.

**Prediction, two-sided.** The view-fixed APPARATUS is flat → salience ≈ 0 by
construction, so **AUC(foreground vs apparatus) > 0.5 robustly** — this is the
clean, falsifiable headline. FOREGROUND vs BACKGROUND is HARDER during a walk:
the textured background also flows under egomotion, so its tracks carry non-zero
salience; I predict AUC(foreground vs background) is ABOVE 0.5 but MODEST, and I
expect W3's egomotion cancellation to be what cleanly suppresses the background.
A null on the apparatus test (AUC ≤ 0.5) would falsify the wiring's basic claim
that a view-fixed thing is non-salient.

**The cutoff is the existing mechanism, not a magic number (§13).** I report
salience@k for a SWEPT k and the raw per-category distributions, plus the fraction
of each category above the effort dial's own `EffortDial().salience_threshold()`
(the shipped 0.02, which falls out of the dial, not tuned here). No threshold is
fitted to the score.

### W3 — egomotion cancellation on textured corridors (the free win 155000 predicted)

**Background.** Block 155000 found egomotion cancellation is a NO-OP on
`defend_the_center` because the untextured arena gives block-SAD no gradient
(calibrated gain ≈ (0,0), nonzero-flow fraction ≈ 0). E1M1's textured walls,
WALKED, should make egomotion sensor-visible.

**Statistic.** (a) egomotion visibility on the walk: mean nonzero-flow fraction
and the dominant moving-flow vector. (b) cancelled-vs-raw best IoU to the GT
MONSTER (imp) on the frames it is present, using the UNCHANGED `efference_carve`
with gain calibrated from the walk's own flow.

**Prediction, two-sided.** Egomotion becomes VISIBLE (nonzero-flow fraction ≫ 0,
a coherent dominant flow vector) — the opposite of `defend_the_center`, meeting
155000's scope condition. Whether cancellation then RAISES enemy IoU is a genuine
open question given the imp is small (1–9 px → sub-pixel at down=2): I predict
egomotion becomes visible (the scope condition is met) but I do NOT predict a
large IoU gain, because at down=2 the imp is near the block-matcher's floor. I
will report cancelled-vs-raw as it falls and diagnose honestly. A finding that
egomotion is STILL not visible on E1M1 would say the block-SAD flow needs a finer
aperture than down=2 affords — a diagnosis, not a rescue.

## Decision rule

This is an exploratory WIRING + measurement rung (like 152000/155000), NO
pass/fail CONFIRM target. The deliverables are: the end-to-end E1M1 carve number
vs defend_the_center; the salience-vs-ground-truth ranking (the headline); the
egomotion-visibility + cancelled-vs-raw result; and a gate that (i) proves the
salience wiring reads the existing signal, (ii) a constructed salient-moving
trajectory scores strictly above a static one (able to fail), (iii) the E1M1
end-to-end runs and records metrics, skipping explicitly if the WAD/VizDoom is
absent. Judged by the ground-truth labels-buffer score, never impressions; raw
distributions reported.

## Determinism / declared residuals (§13)

VizDoom seed = 156000; a FIXED scripted action sequence (forward with a
right-turn burst into the courtyard at tics 40–60 and a dwell scan 78–160, so a
live DoomImp and the looming items enter view); skill 3; RES_320×240 → down=2
→ 120×160; L=4 quantization (the eye's shipped default); flow block = 8
(constant ~16 px physical aperture, as 153000). Grid / downsample / walk length /
seed / quantization level are the sensor's aperture, declared here, NOT tuned to
the score. Scoring is IoU/position and salience ranking — cross-process stable,
never region-id.

## Engine

Measured under the tree's own engine; `engine_preamble()` refuses a diverged or
stale binary in the measuring process, and the source fingerprint / `source_match`
is recorded in `results/e1m1_salience.json`. No Rust change, so the engine is a
build of this tree's (unchanged) Rust source.
