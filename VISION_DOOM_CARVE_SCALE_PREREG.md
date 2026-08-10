# VISION — SCALE THE DOOM RETINA + MAKE THE CARVE FIRE (pre-registration)

**Seed block: 182000–182999.** `python3 scripts/seed_claim.py 182000 182999`
verbatim:

```
SEED CLAIM 182000-182999: CLEAN -- no collision DETECTED.
  Scope: 882 files with seed sinks; 596 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

Provenance: `source_match in ("own","shared")` (never a pinned hash). Canonical
`.so` md5 `417f667716d71ed7d98bae5df25fe9df` must be UNCHANGED (no Rust built).

## What this rung does

Block 181000 (`VISION_DOOM_EYE_PREREG.md`, ledger `fcba2b74`) put the event-native
photon eye on real VizDoom at **15×20** and the eye BUILT + scored structure — but
its 2-D common-fate **CARVE produced ZERO VisionPolygons** (structure came only
from the held-reconstruction ↔ depth-edge correlation). The honest read: it was
RESOLUTION-LIMITED (sub-pixel objects) — the same sub-grid wall the old RGB arc
found (enemy → ~2 cells → gone; a finer grid cleared it).

This rung **SCALES the az×el retina resolution** and gets the eye's OWN
common-fate carve to actually produce objects, SCORED against VizDoom's **labels**
buffer (ORACLE ONLY, never fed to the eye).

**Uses the photon eye's OWN carve, NOT the dead RGB path.** Doom luminance →
Poisson photon flux (`submit_photons_2d`) → `photon_transduce_onset` events →
`retinal_common_fate_carve_2d` (the async 2-D common-fate carve, blocks 164/173)
→ `VisionPolygon`. NO RGB / Image / Patch node, NO `native.segment`, NO agent
decision in Python. VizDoom depth/labels are ORACLE-ONLY.

**Reuse only — no Rust, no new Term, no new seed.** The existing 2-D eye
(`GraphEye`, `photon_eye.py`) + `retinal_onset_2d` / `retinal_carve_2d` seeds,
byte-for-byte. New files only: a measure script, a self-contained gate + committed
fixture, this prereg, a results doc, overlays.

**TIMING IS DEFERRED** (the user's explicit scope: "scale up the resolution AND
carve. Address the timing after."). Real-time is NOT a requirement of this rung.
No timing pass/fail. Cost is reported as WORK UNITS (onset counts) /
wall-seconds-to-complete FACTS for the next rung. The run must merely COMPLETE.

## The differential-motion condition (disclosed up front)

The common-fate carve needs a genuinely **independently-moving object**. Pure
egomotion (turning) sweeps the WHOLE field coherently → one connected blob
covering everything, which the current spatial-connectivity carve **cannot**
velocity-split (a named follow-on in the kernel; `_vel_tol` is reserved). Full
egomotion compensation is a SEPARATE frontier, not this rung.

So the scene is **`defend_the_line`** (VizDoom built-in) with a **STILL camera**
(noop action) and **laterally-moving monsters** (a Demon and a DoomImp sweep
across the field, ~90–115 px lateral over the window). This is the same
moving-enemy regime the old RGB ~0.24 baseline used (`defend_the_center`), so the
comparison is honest. Egomotion is AVOIDED and this condition is disclosed.

## Fixed configuration (declared apertures — NOT tuned to the score)

- **Scene:** `defend_the_line.cfg`, `seed = 182000`, HUD + weapon render OFF,
  STILL camera (noop), `skip = 6` tics per captured frame (differential-motion
  magnitude), `N_CAP = 14` frames (`f0` + `M = 13` motion frames).
- **Retina sweep (n_az × n_el = cols × rows, 4:3 LANDSCAPE downsamples of the
  320×240 screen):** `20×15`, `40×30`, `80×60`, `160×120`. `20×15` is the
  sub-grid-wall grid (an exact area-mean twin of block 181000's 15×20 landscape
  grid); `160×120` is the FIRES-resolution (the headline grid). The measure also
  runs `240×180` as an "as high as COMPLETES" endpoint (reported, not gated).
- **Luminance→flux:** `count ~ Poisson(luma)` per receptor per tick (block-180000
  mapping: the 8-bit ITU-R 601 luminance IS the per-receptor photon-count mean,
  Poisson shot noise per tick).
- **Eye regime:** `adapt_rate = 0.4` (fast adaptation so the STATIC background
  silences quickly and only the moving monster fires onsets — this is the one
  aperture that differs from 181000's 0.15, and it is justified by the
  differential-motion goal, NOT tuned to the IoU), `onset_threshold_db = 6.0`
  (the SHIPPED value — a lower threshold was measured to fire on background
  flicker and collapse precision, so 6.0 is kept), `onset_refractory_epochs = 0`,
  `retina_2d`, synchronous, `worker_capacity = 1`.
- **Carve params (SHIPPED defaults, NOT tuned):** `carve_min_coherence = 0.5`,
  `carve_min_events = 2.5` (>2.5 ⇒ a component needs ≥3 firing cells).
- **The feed:** hold `f0` for `W = 6` warmup ticks (background adapts → goes
  silent), then feed the `M` motion frames; settle the carve over the motion
  window (`epoch ≥ W+1`). Per tick, DONE retina `CognitiveTask` nodes are pruned
  (mechanical housekeeping — the eye's own `_refresh_settled` prunes exactly
  these; it keeps the per-cell `run_rules` cost flat, which is what lets high
  resolution COMPLETE — it does not change the carve).
- **Ground truth (ORACLE, never fed):** VizDoom `labels_buffer`, area-mean/modal
  downsampled to the retina grid; DoomPlayer excluded.

## Scoring (declared)

The common-fate carve captures a moving object's **swept path** over the window,
so the primary carve-vs-labels measure is **collective coverage**: the UNION of
all `VisionPolygon` bbox spans vs the UNION of monster label cells over the
motion window.

- **`union_iou`** = |carve ∪-cells ∩ monster ∪-cells| / |carve ∪ monster| — the
  headline carve-vs-labels IoU.
- **`carve_precision`** = fraction of carved cells that lie on a real monster
  (the carve's real strength — is what it draws actually an object?).
- **`carve_recall`** = fraction of the monster region the carve covers.
- **`best_single`** = best single-polygon IoU vs a monster's swept union
  (reported).
- **`false_poly_rate`** = fraction of polygons touching NO monster cell (the
  REFUSAL measure).

## HEADLINE 1 (falsifiable) — RESOLUTION CLEARS THE SUB-GRID WALL and the CARVE FIRES

- **H1a reproduce_zero:** at the sub-grid grid `20×15`, the carve mints
  `n_polygons == 0` (reproduces the 181000 zero carve).
- **H1b fires_at_scale:** at the FIRES-resolution `160×120`, `n_polygons ≥ 1`.
- **H1c recovers_objects:** at `160×120`, `union_iou ≥ 0.10` AND
  `carve_precision ≥ 0.85` (the carved cells are almost entirely on real
  monsters). The floor `0.10` is the RESOLUTION-PHYSICS floor for THIS carve: it
  is a PRECISE-SPARSE moving-EDGE carve (fires on the coherently-moving
  boundary), fundamentally different from the OLD dense value-carve
  (`native.segment`) that produced the ~0.24 number — the 181000 prereg already
  documented this provenance caveat. The number is reported honestly alongside
  precision; it is NOT claimed to match the dense value-carve regime.
- **H1d rises_with_resolution:** `n_polygons` is non-decreasing across the sweep
  AND strictly rises from the sub-grid grid to the fires grid
  (`n_polygons(160×120) > n_polygons(20×15) == 0`); AND `union_iou(160×120) >
  union_iou(80×60)` (object recovery rises with resolution).

## CONTROLS (able-to-fail)

- **C1 refusal_static:** the REFUSAL control feeds the STATIC `f0` for the whole
  run (warmup + a window of the same length) — NO independently-moving object.
  The adapted field is silent, so the carve must mint `n_polygons == 0` at EVERY
  resolution. (A carve that fabricated on textureless/adapted input would mint
  here.)
- **C2 refusal_real:** on the real run at the fires-resolution, the carve must not
  fabricate — `false_poly_rate ≤ 0.10` (a carve that "fires" by covering
  everything, or by firing on background, is not a win).

## PASS DEFINITION

- **HEADLINE 1 passes** iff {H1a, H1b, H1c, H1d}.
- **CONTROLS pass** iff {C1 (all resolutions), C2}.

Each criterion is a boolean over MEASURED values. The gate
(`tests/test_doom_carve_scale_migrated.py`) reads the mechanism from a
self-contained committed frame fixture (real `defend_the_line` luma + modal
labels at `20×15`, `80×60`, `160×120`), so it runs without VizDoom, and is able
to fail on a flat carve (zero at sub-grid, fires + IoU≥floor + precision at
scale, count rises, refusal on the static control).

## DISCIPLINE

- Separate prereg commit BEFORE any number (this file alone).
- New files only; existing seeds/adapters + `.so` byte-identical (§9). Existing
  vision gates stay green (`test_doom_eye_migrated`, `test_held_surface_migrated`,
  `test_two_eyes*`); `bash scripts/rung7_vision_bench.sh` = 0 failed,
  BEFORE == AFTER.
- Cost is WORK UNITS / wall-seconds (onset counts, completion), never a timing
  pass/fail (timing is the NEXT rung).
- Honest residual up front: this carve is a PRECISE-SPARSE common-fate detector —
  its `union_iou` is recall-limited (it fires the coherently-moving EDGE, not the
  dense body), while its precision is near-1. Dense-body / velocity-split
  segmentation and full egomotion compensation are named follow-ons.
