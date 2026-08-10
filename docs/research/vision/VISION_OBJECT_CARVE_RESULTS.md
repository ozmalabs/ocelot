# OBJECT-NOTION CARVE — RESULTS: **DEGRADE (a large, real, well-characterised improvement).** Common-fate motion grouping collapses the real-video shatter from **113 non-ground regions/frame to ~6** (19×), ELIMINATES the <=2-cell speckle confab (**68% → 0%** at cell resolution), and isolates the object from the coarsening **4× beyond a same-grid value control** — the threshold FALLS OUT (Otsu, read-back == independent recompute on real footage), the synthetic RIGID mover carves as ONE region, all physics gates stay green, oracle 222/0 before AND after. The caveat that makes it a DEGRADE not a CONFIRM: the ARTICULATED presenter carves into her **MOVING PARTS (~6 regions), not one whole-body region**, because her arms move differently from her slow torso (correct common-fate, but "whole person = one region" is not recovered by motion alone), and a residual per-block sensor-speckle survives from spurious block-SAD on the near-uniform studio background.

Pre-registration `VISION_OBJECT_CARVE_PREREG.md`, committed **`5f8757f99f`** BEFORE
the results doc; the discriminator (CONFIRM/DEGRADE/FALSIFY) and the §13 falls-out
claim were fixed there. The gate was written and its pass-criteria fixed before
the real-video probe was run.

## THE ONE VARIABLE — grouping CRITERION, nothing else

The exact-iso-value carve (`Substrate::segment_and_track`) groups cells by EQUAL
grey value — single-frame appearance, no object notion, so natural texture
shatters. The new carve (`Substrate::segment_motion_and_track`, opt-in via
`native.segment_motion`) groups the cells that MOVE TOGETHER — **common fate**.
The cross-frame tracker (`track_comps`, the old tracking phases factored out
VERBATIM) is REUSED byte-for-byte; only what it carves changed. Motion is sensed
by the EXISTING `motion_group_world.vector_field` (block SAD) — the estimator is
reused, not reinvented.

## 1. REAL-VIDEO CONFIRM — the shatter collapses (SAME clip, SAME 64×36 decode)

`scripts/real_video_object_carve_probe.py`, the identical clip/window/decode as
the real-video probe (ABC Phonics presenter, `t=50s`, 4s → 15fps → 60 frames,
64×36 grey, L=4). Every number read FROM THE GRAPH (`read_regions`). `speckle` =
regions ≤2 GRID-UNITS (cells for the 64×36 arms, blocks for the block-grid arms).

| arm | resolution | non-ground/frame | speckle | speckle frac | largest non-ground | ground frac | mtol |
|---|---|---|---|---|---|---|---|
| **A VALUE** (the wall) | 64×36 | **113.2** | 78.1 (≤2 cells) | **68.3 %** | 141 cells (0.06) | 0.74 | — |
| **B MOTION** B=4 | 64×36 | **5.9** | **0** | **0 %** | 35 cells (0.015) | 0.95 | 1.03 |
| B MOTION B=2 | 64×36 | 30.1 | 0 | 0 % | 18 cells | 0.93 | 0.24 |
| C MOTION B=4 | 16×9 (blocks) | 4.8 | 4.6 (≤2 blocks) | 74.6 % | 1.9 blocks | 0.96 | 1.24 |
| **D VALUE** B=4 (control) | 16×9 (blocks) | **20.3** | 15.2 (≤2 blocks) | 68.7 % | 20.6 blocks (0.14) | 0.58 | — |

**The headline (A → B, B=4, same 64×36):** ~1 object → **113 → 6 non-ground
regions/frame (19×), and ≤2-cell speckle confab 68 % → 0 %.** The shatter is gone.

**The motion contribution is isolated from the coarsening (C vs D, same 16×9
grid):** the value carve at the coarse grid still gives 20.3 non-ground regions;
the motion carve gives 4.8 — a **4.2× further reduction that is the common-fate
grouping, not the downsampling.** (D is the control the coarser grid demands: a
smaller grid alone reduces the count, so the fair test holds the grid fixed and
swaps the criterion.)

**Two honest reads of the speckle drop:**
- At cell resolution (A vs B, directly comparable units): 68.3 % → **0 %**. The
  <=2-cell shatter is eliminated. PARTLY a floor artefact I disclose: the motion
  field is block-replicated, so no region CAN be ≤2 cells — the smallest possible
  region is one B×B block. The genuine content is the region COUNT (113 → 6).
- At the block grid (C), a per-block speckle of 74.6 % REMAINS *by fraction* — but
  it is **4.6 one-block regions/frame in absolute terms** (vs the value wall's 78
  specks), i.e. a handful of background blocks that block-SAD gave a spurious
  motion vector on the near-uniform studio wall. The fraction is high only because
  the coherent regions also dropped to a handful; the absolute confab fell ~17×.

## 2. WHY IT IS A DEGRADE, NOT A CONFIRM — the presenter is ARTICULATED

`ground_frac = 0.95` (B=4) is the tell: the background PLUS the presenter's slowly
moving TORSO all read as the dominant/static group and merge into ground. Only her
FAST-moving parts (arms/hands doing phonics actions) contrast above the derived
tolerance and mint as figures. So the ~6 non-ground regions are her MOVING PARTS,
and the largest is only ~35 cells (1.5 % of the field) — **not one whole-body
region.** This is *correct* common fate (a waving arm genuinely moves differently
from a still torso — Spelke's cohesion applies to what moves as one, and an
articulated body does not), but it means **motion alone does not recover "the whole
person as one region."** Whole-body segmentation would need appearance + motion
together, not motion alone. The prereg predicted exactly this (prediction 4).

## 3. THE LEARNING-LOOP PRECONDITION — holds for a RIGID mover, per-part for the presenter

The precondition that made `PHYSICS_FALL_FROM_EYE` work is *one object ⇒ one Region
whose centroid traces its motion*.

- **For a RIGID translating object** (the physics cases — a fall, a push, a thrown
  block): the synthetic gate PROVES it now holds on TEXTURED input — a textured
  blob translating within the aperture carves as ONE region (
  `test_moving_object_is_one_region`), and two different-common-fate objects carve
  as TWO. On real video the precondition would now hold for such a mover.
- **For the ARTICULATED real presenter**: it holds PER MOVING PART, not per person
  — but she was never a rigid mover. So on THIS clip the precondition is IMPROVED
  (a moving arm is now a coherent, trackable region instead of texture confetti)
  but not fully met at the whole-person level. That is the honest boundary.

## 4. §13 — THE MOTION THRESHOLD FELL OUT (on synthetic AND real footage)

No motion constant appears in `segment_motion_and_track`. The tolerance is Otsu's
between-class split over the field's OWN adjacent-pair vector-difference dispersion
(faithful to the graph rule `mo_tol_otsu`); the reference frame is the largest
motion group (`mo_dominant`). Evidence:

- The engine's read-back `mtol` equals an INDEPENDENT Python Otsu recompute over
  the same pd field, to 1e-9, on two different synthetic fields
  (`test_motion_threshold_falls_out`).
- It ADAPTS: `mtol` is **0.24 → 1.03** across B=2/B=4 on the real clip, **0.35 →
  1.24** at the block grid — DERIVED per frame from the field, never passed in.
- The only declared magic is `vector_field`'s search-radius = block (the aperture,
  §13-exempt exactly as its `block` is): a per-frame displacement > block exceeds
  the block-overlap and fragments (observed in gate development at dx=4, B=2).

## 5. ADDITIVE — the synthetic results survive

`segment_and_track` (the value carve) is UNCHANGED and remains the default; the
change is a SEPARATE opt-in method. The tracking phases were factored into a shared
`track_comps` VERBATIM (both carves call it). Confirmed byte-identical BEHAVIOUR:

- Physics gates **green**: `test_fall_from_eye_migrated`, `test_mass_by_action_migrated`,
  `test_galileo_migrated`, `test_generic_order_n_migrated` (+ object-carve +
  provenance) = **43 passed**.
- ORACLE `scripts/rung7_vision_bench.sh` (data/ symlinked): **BEFORE 222 passed /
  0 failed** (shared engine `ac8625525b09`); **AFTER 222 passed / 0 failed** (own
  engine `1792a9ce0af4`).
- Own gate `tests/test_object_carve_migrated.py`: **4 passed** (moving object → one
  region; two common-fate objects → two; static → ground, no figure; §13 falls-out).
- Instrument seams `pytest -k migrated` (provenance + failure_baseline): **18 passed**.

## 6. VERDICT — DEGRADE

Common-fate motion grouping is the object notion the exact-value carve lacked. It
collapses the real-video shatter (**113 → 6 non-ground regions/frame, 19×**),
eliminates the ≤2-cell speckle confab (**68 % → 0 %**), and isolates the object
from coarsening (**4.2× beyond a same-grid control**); the threshold falls out; a
rigid textured mover is now ONE region; the value carve is byte-identical and every
gate is green. It is a DEGRADE not a CONFIRM because an ARTICULATED human carves
into her moving PARTS (~6 regions), not one whole-body region — correct common
fate, but whole-object recovery needs appearance + motion — and a residual
per-block sensor-speckle survives on the near-uniform background. **The FALSIFY
conditions did NOT occur:** motion IS groupable without a magic threshold (Otsu
falls out, verified on real footage), it IS additive (value carve byte-identical,
physics green), and the background IS separable by motion (ground 0.95; motion
isolates the object 4× beyond coarsening).

## 7. PROVENANCE / DISCIPLINE

- Worktree branch **`gamma-substrate/object-carve-commonfate`** (NOT main);
  prereg **`5f8757f99f`** BEFORE the results doc.
- Engine **`1792a9ce0af4`**, built IN THIS TREE by `scripts/engine_build.sh`,
  `source_match = own` (asserted from inside the process). This rung ADDS RUST
  (a new `Substrate` method + a py.rs handoff); **NO new Term variant**
  (`NUM_TERM_VARIANTS = 181`, unchanged).
- ORACLE 222/0 BEFORE (shared `ac8625525b09`) and AFTER (own `1792a9ce0af4`).
- SEED CLAIM 144000-144999 header (verbatim, run before any number):
  `SEED CLAIM 144000-144999: CLEAN -- no collision DETECTED.` The probe drew NO
  seed (deterministic decode + block-SAD + Otsu + flood + tracking); the gate uses
  fixed `default_rng` seeds.
- Machine-readable: `results/real_video_object_carve.json`. Probe wall 0.8 s (60
  frames × 7 arms), `OMP_NUM_THREADS=2`.

## 8. WHAT I GOT WRONG (in full)

1. **My first synthetic gate used a FLAT (constant-fill) moving blob — and it
   SHATTERED (6-8 fragments).** A textureless region has NO observable motion: its
   interior block-SAD is a flat tie broken to (0,0), so the blob interior reads
   v=0 and merges into the background; only the boundary blocks see motion. I had
   the aperture problem backwards — I assumed the synthetic FLAT blob would be the
   EASY case and real texture the hard one, when the opposite is true: a TEXTURED
   object is what moves coherently, and real footage (textured) is *easier* for the
   motion carve than a clean flat synthetic blob. Fixed the gate to a textured
   object (which is also honest about what the sensor can see).
2. **The "0 % speckle" at cell resolution is partly a FLOOR ARTEFACT, not pure
   grouping.** The motion field is block-replicated, so no carved region can be
   ≤2 cells — the ≤2-cell metric is structurally zero at cell resolution. I say so
   and lead the confab story with the region COUNT (113 → 6) and the block-grid
   absolute speckle (78 → 4.6), which are not floor-limited.
3. **I initially expected the presenter to carve as ONE region and read the low
   region count as a full CONFIRM.** `ground_frac = 0.95` corrected me: her slow
   torso merges into the static ground and only her fast arms mint as figures, so
   the ~6 regions are her moving PARTS. Motion alone does not recover the whole
   articulated body — the honest verdict is DEGRADE, and I re-registered the
   learning-loop precondition as "holds for a rigid mover, per-part for the
   presenter."
4. **The per-block background speckle (74.6 % by fraction at B=4) looks alarming
   until put in absolute terms (4.6 blocks/frame vs the wall's 78).** A high
   fraction over a tiny denominator is not a high count; I report both so the
   fraction is not oversold as a regression.
5. **`segment_and_track` was refactored (the tracking phases moved into a shared
   `track_comps`) rather than duplicated.** The move is verbatim, so behaviour is
   byte-identical BY CONSTRUCTION — but "byte-identical" is only trustworthy
   because the physics gates + oracle 222/0 are the guard, not because I eyeballed
   the diff. Had they gone red I would have reverted to duplication.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine | oracle before/after | verdict |
|---|---|---|---|---|
| object-notion carve (block 144000-144999) | The exact-iso-value eye lacked an object notion; the fix is COMMON FATE — group the cells that MOVE TOGETHER (`segment_motion_and_track`, opt-in, via `vector_field` block-SAD + Otsu tolerance that FALLS OUT + dominant-group reference + union-find flood, then the UNCHANGED `track_comps` tracker). On the SAME real presenter clip (64×36 grey, 60 frames), non-ground regions/frame **113 → 6 (19×)**, ≤2-cell speckle confab **68 % → 0 %**, and **4.2× fewer** regions than a same-grid value control (motion isolated from coarsening); `mtol` derived per frame (0.24-1.24), read-back == independent Otsu recompute. A synthetic RIGID textured mover carves as ONE region (gate); an ARTICULATED presenter carves into her MOVING PARTS (~6, ground 0.95 hides the slow torso), so whole-person recovery needs appearance+motion — **DEGRADE**. Physics gates byte-identical (43 passed); value carve UNCHANGED (additive). NO new Term (NUM 181). | `1792a9ce0af4` (own; ADDS RUST) | 222/0 → 222/0 | **DEGRADE** (large real improvement; articulated body → parts, residual background sensor-speckle) |

## 9. NAMED NEXT LEVERS

1. **APPEARANCE + MOTION for whole-object recovery.** Motion carves what moves;
   binding a moving part to the appearance-connected body it belongs to (the slow
   torso the motion carve drops into ground) needs the two cues together. The
   articulated presenter is the case that demands it.
2. **A NULL for the background sensor-speckle.** The residual per-block confab is
   spurious block-SAD on a near-uniform region — the inherited sensor bound
   (`VISION_PARALLAX*` named the ~7-8 % confab). An MDL / block-std gate on the
   sensor (refuse a motion vector where the block carries too little structure)
   would suppress it — but must itself fall out, not be a picked floor.
3. **CODEC MOTION VECTORS as the sensor** (memory CODEC↔EYE) — replace computed
   block-SAD with the transmitted H.264/265 motion field where the corpus exposes
   it, removing the computed-flow confab at its source.
