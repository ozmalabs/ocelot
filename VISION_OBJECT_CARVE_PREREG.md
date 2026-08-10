# OBJECT-NOTION CARVE — PRE-REGISTRATION (block 144000-144999)

The real-video probe (`VISION_REAL_VIDEO_PROBE_RESULTS.md`) named the first wall:
the EXACT-ISO-VALUE carve (`Substrate::segment_and_track`) has NO object notion,
so a naturally-textured moving presenter shatters into **113-528 regions/frame**
(68-92% of them <=2-cell speckle confab) at 64x36 grey, while the background
floods into one region. The named fix: an object-notion carve that groups beyond
iso-value. The arc's own finding (`VISION_PARALLAX*`): **objecthood lives in
TEMPORAL COHERENCE — motion carves what a static frame cannot.**

## THE ONE VARIABLE

Replace the grouping CRITERION, nothing else. The current carve groups cells by
EXACT EQUAL grey value (single-frame appearance). The new carve groups the cells
that MOVE TOGETHER — **COMMON FATE**. Everything downstream (the cross-frame
tracker: persistent Region ids, overlap → nearest-centroid → velocity-predictive
matching) is REUSED byte-for-byte; only what it carves changes.

- Motion is sensed by the EXISTING `motion_group_world.vector_field` (block SAD) —
  the estimator is reused, not reinvented.
- Grouping = union-find flood merging 4-neighbours whose motion vectors agree
  within a tolerance; the STATIC/dominant background is one region.
- New Rust method `Substrate::segment_motion_and_track` (via `native.segment_motion`),
  a SEPARATE opt-in carve. The exact-value `segment_and_track` is UNTOUCHED and
  remains the default (ADDITIVE).

## §13 — THE MOTION THRESHOLD MUST FALL OUT

The moving-vs-static / same-object split must come from the motion distribution,
never a hand-set constant. The tolerance is Otsu's between-class split over the
field's OWN adjacent-pair vector-difference dispersion (faithful to the graph
rule `mo_tol_otsu` in `seeds/vision_motion_group.json`); the reference frame is
the largest motion group (`mo_dominant`). No motion constant appears in the
carve. `vector_field`'s search-radius = block is the declared aperture magic
(§13-exempt, exactly as its `block` is).

## DISCRIMINATOR (fixed before any real-video number)

- **CONFIRM:** common-fate carves the real moving presenter into a SMALL number
  of coherent moving regions (vs 113-528; confab drops from 68-92%), the
  synthetic physics worlds still carve one moving blob and their gates stay green,
  oracle 222/0, the threshold fell out. The learning-loop precondition (one moving
  object = one trajectory) now holds on real footage.
- **DEGRADE:** it helps a lot but a real caveat remains (needs >=K frames /
  displacement <= aperture; a slow/occluded/articulated object partly fragments; a
  residual confab floor) — quantified.
- **FALSIFY:** real-video motion too noisy to group without a magic threshold; OR
  common-fate not additive without disturbing the synthetic carve; OR the
  background not separable by motion on this clip. Name what blocks it. Do NOT
  tune the clip or hand-set the threshold.

## PREDICTIONS

1. The shatter collapses: region count drops by roughly an order of magnitude
   (113 → single/low-tens). ~85%.
2. The <=2-cell speckle at cell resolution is largely eliminated (block-quantized
   motion field has no 1-2-cell regions). ~85%.
3. A RIGID textured mover carves as ONE region (synthetic gate). ~90%.
4. The ARTICULATED presenter carves into her MOVING PARTS (arms move differently
   from torso — correct common-fate), so "whole person = one region" is NOT fully
   recovered by motion alone; a residual per-block sensor-speckle remains from
   spurious SAD on the near-uniform background. ⇒ expected outcome **DEGRADE**, not
   a clean CONFIRM, ~60%.
5. The threshold falls out on real footage (derived per-frame, varies with the
   field). ~90%.

## GATE

`tests/test_object_carve_migrated.py`: a moving textured object → one coherent
region; two different-common-fate objects → two regions; a static field → ground,
no figure; the §13 audit (read-back `mtol` == an independent Otsu recompute; the
threshold adapts to the field). Physics gates (`fall_from_eye`, `mass_by_action`,
`galileo`, `generic_order_n`) stay green (the value carve is byte-identical).
Oracle `scripts/rung7_vision_bench.sh` 222/0 before AND after.

## PROVENANCE / DISCIPLINE

- Worktree branch `gamma-substrate/object-carve-commonfate` (NOT main).
- SEED CLAIM 144000-144999 header (verbatim, run before any number):
  `SEED CLAIM 144000-144999: CLEAN -- no collision DETECTED.` (deterministic
  probe — no RNG drawn; the gate uses fixed `default_rng` seeds.)
- Engine built in-tree (`scripts/engine_build.sh`); `source_match ∈ {own, shared}`
  asserted; oracle 222/0 before AND after. This rung ADDS RUST (a new Substrate
  method + py.rs handoff); NO new Term variant (NUM_TERM_VARIANTS unchanged).
