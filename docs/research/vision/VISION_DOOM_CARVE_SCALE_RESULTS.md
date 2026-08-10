# VISION — SCALE THE DOOM RETINA + MAKE THE CARVE FIRE (results)

**Block 182000.** Prereg: `VISION_DOOM_CARVE_SCALE_PREREG.md` (commit
`c3f03ddba38d288a4e80193854e49abb5ee0809d`, committed BEFORE any number).
`source_match = "own"`. Canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df`
UNCHANGED (no Rust built). **Timing is DEFERRED — no timing pass/fail.**

## Headline

**Resolution clears the sub-grid wall and the eye's OWN 2-D common-fate carve
FIRES.** Block 181000's carve produced ZERO polygons at 15×20 (sub-pixel
objects). Scaling the az×el retina to **160×120**, the carve mints **4
VisionPolygons that land on the moving monsters** (`defend_the_line`, still
camera, laterally-moving Demon + DoomImp), scored vs the VizDoom labels oracle:
**union carve-vs-labels IoU = 0.1215**, **precision = 0.978** (the carved cells
are almost entirely on real monsters), **zero false polygons**, and the STATIC
refusal control mints **zero** at every resolution. Polygon count rises 0 → 0 →
0 → 4 across the sweep. **All prereg criteria pass.**

## The resolution sweep (n_az × n_el = cols × rows, 4:3 landscape)

| grid | cells | n_polygons | union_iou | precision | recall | best_single | false_poly_rate | refusal npoly | onset units | wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 20×15   | 300   | **0** | 0.0    | –     | –     | 0.0    | 0.0 | 0 | 1   | 0.16 |
| 40×30   | 1200  | 0     | 0.0    | –     | –     | 0.0    | 0.0 | 0 | 4   | 1.25 |
| 80×60   | 4800  | 0     | 0.0    | –     | –     | 0.0    | 0.0 | 0 | 47  | 18.6 |
| 160×120 | 19200 | **4** | **0.1215** | **0.978** | 0.122 | 0.138 | **0.0** | 0 | 346 | 282.7 |

`union_iou` = |carve∪-cells ∩ monster∪-cells| / |carve∪monster| over the motion
window (the collective coverage measure fair to a common-fate carve, which
captures the object's swept path). `onset units` = total onset events in the
motion window (WORK UNITS, not wall-clock). Overlays:
`results/doom_carve_scale/overlay_{20x15,40x30,80x60,160x120}.png` (carve
polygons in red vs monster labels in grey) — at 160×120 all 4 boxes lie on the
monster band, none on background.

## Per-criterion (all measured booleans)

| id | criterion | measured | pass |
|---|---|---|---|
| H1a | reproduce_zero: 20×15 n_polygons == 0 | 0 | ✅ |
| H1b | fires_at_scale: 160×120 n_polygons ≥ 1 | 4 | ✅ |
| H1c | recovers_objects: 160×120 union_iou ≥ 0.10 AND precision ≥ 0.85 | 0.1215 / 0.978 | ✅ |
| H1d | rises_with_resolution: n_polygons(160×120) > 0 AND union_iou(160×120) > union_iou(80×60) | 4>0, 0.1215>0.0 | ✅ |
| C1 | refusal_static: 0 polygons on the STATIC control, every resolution | 0/0/0/0 | ✅ |
| C2 | refusal_real: 160×120 false_poly_rate ≤ 0.10 | 0.0 | ✅ |

## What made the carve fire (the mechanism, honestly)

1. **The sub-grid wall is real and dual.** Below 160×120 the moving monster is
   sub-cell in BOTH senses: its per-frame displacement is smaller than a cell
   (so no cell crosses the 6 dB onset threshold twice → no coherent temporal
   trace), and cells only PARTIALLY covered by the monster have diluted contrast
   (below 6 dB). Both dissolve with finer cells. Onset work rises 1 → 4 → 47 →
   346 across the sweep; the carve needs ≥3 coherent firing cells per component
   and does not reach it until 160×120.
2. **Differential motion is required and was used (disclosed).** The common-fate
   carve fires on a genuinely independently-moving object. Pure egomotion sweeps
   the whole field coherently → one blob covering everything, which the current
   spatial-connectivity carve cannot velocity-split (`_vel_tol` reserved). So the
   scene is `defend_the_line` with a **still camera** and monsters sweeping
   laterally — the same moving-enemy regime the old RGB ~0.24 baseline used.
   Egomotion compensation is a separate frontier.
3. **The feed silences the background.** Holding f0 for 6 warmup ticks
   (adapt_rate 0.4) adapts the receptors to the static field → it goes silent →
   only the moving monster fires onsets in the motion window (precision 0.978).
4. **What let high resolution COMPLETE (not a timing claim).** The per-cell
   `photon_transduce` CognitiveTask nodes are minted every tick; left
   un-pruned they accumulate and `run_rules` cost grows quadratically (measured:
   25 s/tick and climbing at 4800 cells by tick 5). Pruning done retina tasks
   each tick — exactly what the eye's own `_refresh_settled` does — makes the
   cost flat (~0.8 s/tick at 4800 cells). This is mechanical housekeeping, not a
   decision, and does not change the carve.

## Timing (a FACT for the next rung — explicitly NOT a pass/fail)

Wall-seconds to run the warmup+motion+settle at each resolution (single core,
under the eye's per-cell `run_rules`): 0.16 / 1.25 / 18.6 / **282.7** s for
20×15 / 40×30 / 80×60 / 160×120. The cost is dominated by per-cell rule matching
and scales with cell count. 160×120 (19200 cells) completes in ~4.7 min; a
240×180 (43200-cell) endpoint was attempted and is very slow under this
per-cell-rule engine (the SIMD/per-area-index accelerators in MEMORY are the
named next lever). **Timing is the NEXT rung; no speed pass/fail is claimed here.**

## Honest residuals

- **The carve is a PRECISE-SPARSE common-fate detector, not a dense segmenter.**
  `union_iou ≈ 0.12` at 160×120 is RECALL-limited (recall 0.12) — the carve
  fires the coherently-moving EDGE, not the dense body — while PRECISION is 0.978
  (near-perfect). This is a different mechanism from the OLD dense value-carve
  (`native.segment`) that produced the ~0.24 number; the 181000 prereg already
  documented that provenance caveat. The 0.10 floor is the resolution-physics
  floor for THIS carve, reported honestly alongside precision — it is NOT claimed
  to match the dense value-carve regime. Dense-body / velocity-split segmentation
  is a named follow-on.
- **Landscape aspect matters at the firing threshold.** A portrait mis-sampling
  (az/el swapped) fired at 60×80/120×160; corrected landscape sampling fires only
  at 160×120 (80×60 stays at 0). The reported sweep is the corrected landscape.
- **Egomotion NOT handled** — disclosed and deliberately avoided; a separate
  frontier.
- **Timing** — see above; the 160×120 run is ~4.7 min, high-res is slow under the
  per-cell-rule engine. A named next-rung lever.

## Provenance & discipline

- New files only (`git diff --stat fcba2b74b1..HEAD` = prereg only; the measure
  script, gate, fixture, results json, overlays are untracked additive). No
  existing seed / adapter / `.so` touched.
- Gate `tests/test_doom_carve_scale_migrated.py` — 7 passed (~21 s), self-
  contained on the committed fixture (`tests/fixtures/doom_carve_scale/`,
  VizDoom-free). It pins the sub-grid zero, fire-at-fine-grain, IoU≥floor +
  precision, count-rises, and both refusal arms; the fine-grain test runs on a
  fixed 87×40 crop of the 160×120 grids for speed (crop floor 0.08; full-res
  headline 0.1215 in the results run).
- Existing named vision gates green: `test_doom_eye_migrated`,
  `test_held_surface_migrated`, `test_two_eyes*` — 43 passed.
- Oracle `bash scripts/rung7_vision_bench.sh`: **214 passed, 10 skipped, 0
  failed** (worktree-without-`data/` condition). BEFORE == AFTER by construction:
  the oracle's file list is fixed and no listed file was modified (additive only).

## Proposed VISION_PROTOCOL ledger row

`182000 | scale Doom retina + make the common-fate carve FIRE | defend_the_line still-camera differential motion; carve 0 polys ≤80×60 → 4 polys @160×120, union carve-vs-labels IoU 0.1215, precision 0.978, 0 false, 0 refusal; count rises 0→4; sub-grid wall cleared | reuse only (no Rust/Term/seed); gate test_doom_carve_scale_migrated 7/7; oracle 214/10/0 BEFORE==AFTER; .so md5 unchanged; source_match own | timing deferred (160×120 ~4.7min, per-cell-rule engine is the next lever); carve is precise-sparse (recall-limited), egomotion + dense-body/velocity-split are named follow-ons`
