# PREREG — ASYNC COMMON-FATE CARVE (Rung 3 of the photon-eye migration)

**Seed block: 163000–163999** (`check_claim(163000, 163999)` CLEAN — no
collision detected; drawn once at `default_rng(163000)`). Committed BEFORE any
confirmatory number.

## The claim

The photon eye declares `VisionPolygon` but never produces one (`"polygons": []`
in `_read_snapshot`). Rung 3 CARVES objects from the ASYNC EVENT STREAM by
COMMON FATE: contiguous retinal columns whose onset events share a coherent
motion (one shared velocity vector) group into ONE `VisionPolygon`; columns
carrying a DIFFERENT common-fate motion form a DIFFERENT polygon; a
static/incoherent field carves nothing. The carve reads the async event stream
(`RetinalOnsetEvent` column+own-epoch, the same input Rung 2's
`retinal_event_motion` reads) — NOT the coarse `retinal_field` raster and NOT
`native.segment` / `native.segment_motion` (the raster carves).

**HONEST SCOPE (stated, not hidden):** the photon eye is a 1-D AZIMUTH STRIP (a
central vband, elevation collapsed), so this carve is 1-D — contiguous AZIMUTH
SPANS sharing a common motion, emitted as `VisionPolygon` spans. TRUE 2-D carve
(azimuth×elevation objects) requires the retina extended to elevation columns
first — a NAMED follow-on, NOT this rung.

## The mechanism (fixed before the confirmatory run)

- **Rust kernel `retinal_common_fate_carve`** (pure CognitiveTask kind, peer of
  `retinal_event_motion`): payload
  `[n_az, max_gap, vel_tol, k, c_0, e_0, …, c_{k-1}, e_{k-1}]` — the retina width,
  two segmentation params (spatial contiguity limit, relative velocity tolerance),
  and the `k` onset events (column index, own epoch). It:
  1. reduces the events to one mean epoch per firing column, sorted by column;
  2. SEGMENTS the sorted columns into maximal COMMON-FATE runs — a run extends to
     the next firing column only if it is spatially contiguous (column gap
     ≤ `max_gap`), its local space-time slope `Δc/Δe` has the SAME SIGN as the
     run's, AND its magnitude is within `vel_tol` (relative) of the run's first
     local slope; a sign flip, a velocity jump, a spatial gap, or a simultaneous
     pair (`Δe=0`) closes the run;
  3. for each run computes the Rung-2 regression (column on epoch) →
     `direction=sign(slope)`, `speed=|slope|`, `coherence=|Pearson r|`, `n_events`.
  Output is a FIXED per-column layout of stride 7:
  `[is_group_start, col_min, col_max, direction, speed, coherence, n_events]` for
  each column `0..n_az`, the run's block written at its START column's index (all
  other columns zero). This lets a per-column graph rule mint exactly one polygon
  per run, in the Rung-1/Rung-2 per-column house style.
- **Seed `seeds/retinal_carve.json`** rule `retinal_mint_carve`: matches every
  `RetinalColumn` against the done carve task and mints a
  `VisionPolygon{col_min, col_max, direction, speed, coherence, n_events, epoch}`
  iff `output[index*7+0] == 1.0` (this column is a run start), `coherence >
  min_coherence`, AND `n_events > min_events` — both thresholds DATA on a
  `RetinaCarveParams` node — once per column-epoch via a `carve_epoch` guard.
- **OFF by default (§9):** engages only under `context["visual_carve"]`, which
  creates the `RetinaCarveParams` node (and implies the onset path); absent it the
  rule cannot match and no carve task is ever created. Onset / motion / coarse
  paths are byte-identical.
- **Python is mechanical only:** the adapter reads `RetinalOnsetEvent` attrs
  (`column_index`, `epoch`) — the EVENT STREAM, nothing from the raster — packs
  them into the carve task payload, and reads the `VisionPolygon` nodes back in
  `_read_snapshot`. No decision in Python.

## Headline QUANTITY + pre-registered claim

On a controlled synthetic scene with TWO objects occupying disjoint contiguous
azimuth spans and moving with DIFFERENT common-fate motions (object A a
left-to-right sweep, object B a right-to-left sweep), driven through the REAL
mint rule:

> **The carve mints EXACTLY 2 `VisionPolygon`s, one per object; each polygon's
> azimuth span (col_min..col_max) covers its object's columns and each polygon's
> motion direction sign matches its object (A → +1, B → −1).**

Because the synthetic sweeps are noiseless the per-object diagonals are exactly
linear (`coherence = 1.0`), so the count is exact, not an interval.

## Able-to-fail controls (read MEASURED values; no constant re-derived in Python)

1. **TWO motions → 2 polygons**, spans partition the two objects, signs (+1, −1)
   match (the headline).
2. **ONE uniform motion → 1 polygon** (a single object sweeping the whole strip
   carves as one span whose direction matches the sweep).
3. **SCRAMBLED / incoherent → 0 polygons** (the SAME columns with epochs shuffled:
   the velocity-consistency segmentation fragments the runs below `min_events` and
   the regression coherence falls below `min_coherence`, so the mint rule declines
   — measured, prereg'd to 0 coherent polygons).
4. **DEFAULT OFF:** flag off ⇒ no `RetinaCarveParams`, no carve task, no
   `VisionPolygon`; existing paths byte-identical.

## Merge-block criterion (supervisor checks)

The carve groups the async EVENT STREAM (`RetinalOnsetEvent` column+epoch), NOT
the `retinal_field` raster and NOT `native.segment`/`native.segment_motion`. The
gate source-audits `GraphEye.settle_carve` for `RetinalOnsetEvent`/`column_index`/
`epoch` and asserts the forbidden raster/frame-diff symbols are absent.

## Provenance (§10)

`engine_provenance()["source_match"] ∈ {"own", "shared"}` — never a pinned hash,
never `== "shared"`.

## Oracle (§9)

`bash scripts/rung7_vision_bench.sh` = 0 failed, and BEFORE == AFTER with the
carve flag OFF (both sides).

## NO TIMING CLAIM

Another rung runs in parallel; this claim is CORRECTNESS (groups match objects),
never milliseconds.

## Named follow-ons / residuals

- **2-D carve** (azimuth×elevation objects) needs the retina extended to
  elevation columns first — named, not this rung.
- Two objects of the SAME direction separated only in speed split via `vel_tol`;
  two same-direction objects that also share a speed and are spatially adjacent
  (no static gap between them) would merge — a known common-fate limitation, the
  1-D analogue of the aperture limit, named not solved.
