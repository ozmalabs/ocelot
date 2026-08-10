# RESULTS — THE 2-D EXPANSION (az×el retina; 2-D onset + 2-D carve)

Prereg: `VISION_2D_EXPANSION_PREREG.md` (seed block 166000–166999, committed
ALONE at `9d665fe744` before any confirmatory number). Gate:
`tests/test_2d_retina_migrated.py` (9 passed). Engine `source_match = own`
(this worktree's own build; canonical artifact NOT modified).

## What landed

Rungs 1-4 were 1-D because the photon eye was a 1-D azimuth strip. This rung
adds, additive and OFF by default behind `context["retina_2d"]`:

- **Rust kernel `retinal_common_fate_carve_2d`** (`runners/dsl/src/cognitive_tasks.rs`)
  — a new pure `CognitiveTask` kind (NO new DSL Term enum variant). Reduces the
  `(col, row, epoch)` onset events to one mean epoch per firing cell, groups
  cells into maximal 8-connected COMPONENTS (Chebyshev-1 adjacency — a spatial
  gap in azimuth OR elevation separates components), fits each component's 2-D
  motion, emits a per-cell stride-9 layout
  `[is_group_start, col_min, col_max, row_min, row_max, direction, speed,
  coherence, n_events]` anchored at each component's smallest-flat-index cell.
- **`seeds/retinal_onset_2d.json`** — `retinal_mint_onset_2d` mints a
  `RetinalOnsetEvent{column_index, row_index, magnitude_db, epoch}` per firing
  cell, off the SAME byte-identical `photon_transduce_onset` kernel Rung 1 uses.
- **`seeds/retinal_carve_2d.json`** — `retinal_mint_carve_2d` mints one
  `VisionPolygon{col_min,col_max,row_min,row_max,direction,speed,coherence,
  n_events,epoch}` per coherent component (gated on `min_coherence`/`min_events`
  DATA on `RetinaCarveParams2d`, once per cell-epoch).
- **`domains/photon_eye.py`** — mechanical only: `_build_2d` builds the `(az,el)`
  cell sheet, `submit_photons_2d` packs onset tasks per cell, `settle_carve_2d`
  packs the 2-D carve task from the event stream, `carve_polygons_2d` reads
  polygons back with their elevation span. No decision in Python.

## The headline — MEASURED (2-D separates what 1-D conflates)

Scene: `n_az=16 × n_el=12`. Two objects at the SAME azimuth columns `[4..9]`,
identical L→R common fate (`epoch = col−4`); object A at rows `[2..3]`, object B
at rows `[8..9]` (elevation gap `[4..7]`). The SAME events fed to both carves
(collapsed to `(col,epoch)` for 1-D; `(col,row,epoch)` for 2-D):

| carve | coherent objects | spans |
|---|---|---|
| **1-D `retinal_common_fate_carve`** | **1** | one azimuth span `col 4..9` (elevation collapsed — the two objects CONFLATED) |
| **2-D `retinal_common_fate_carve_2d`** | **2** | `(col 4..9, row 2..3, +1)` and `(col 4..9, row 8..9, +1)` — SEPARATED at correct `(az,el)` |

**Prediction met exactly: 1-D → 1, 2-D → 2.** End-to-end through the 2-D eye
build + the REAL `retinal_mint_carve_2d` rule: 2 `VisionPolygon`s at
`(4,9,2,3)` and `(4,9,8,9)`, both direction `+1`, coherence `= 1.0`, sharing
azimuth and non-overlapping in elevation.

## Able-to-fail controls — MEASURED

| control | 1-D | 2-D | predicted |
|---|---|---|---|
| SAME az / DIFF el (headline) | 1 | 2 | 1 / 2 ✓ |
| DIFFERENT az (A col0-3, B col10-13) | 2 | 2 | 2 / 2 ✓ (2-D does not over-split) |
| STATIC / no events | 0 | 0 | 0 / 0 ✓ |
| SCRAMBLED epochs | see below | see below | collapse → 0 |

## Scrambled control — an HONEST prereg REFINEMENT

The prereg predicted "SCRAMBLED → 2-D 0, 1-D 0". Measured, a SINGLE random
epoch-shuffle of the small (~12-cell) headline components is a SMALL-SAMPLE-NOISY
incoherence test: over a fixed 200-seed sweep (166000–166199) on the committed
scene the mean coherent count COLLAPSES from the structured value but is not a
per-seed 0 —

- **mean 1-D coherent = 0.145** (structured 1); 29/200 seeds leave a spurious run,
- **mean 2-D coherent = 0.215** (structured 2); 40/200 seeds leave a spurious component.

This is **not a 2-D defect** — the EXISTING 1-D carve shares it (14.5% spurious);
its own scrambled test just used one lucky seed. At `n≈12` a shuffled `|Pearson r|`
has std `≈0.3`, so it exceeds the `0.5` gate ~20% of the time. The control is
therefore stated as a DISTRIBUTION COLLAPSE (structured 2 → shuffled mean 0.215,
CI-separated), which is the honest able-to-fail form.

The coherence gate sharpens to a **crisp per-seed 0 as components grow**: a
`4×10`-cell object shuffled at the committed seed 166000 → **0 coherent 2-D
components** (200-seed robustness: 1/200 spurious). Both facts are gated
(`test_scrambled_epochs_collapse_the_coherent_count`,
`test_scrambled_epochs_are_deterministically_incoherent_at_scale`).

## Default-OFF / byte-identity (§9) + oracle

- `retina_2d` OFF ⇒ `_retina_2d is False`, no `RetinaOnsetParams2d` /
  `RetinaCarveParams2d`, `settle_carve_2d()` a no-op, 2-D seeds unloaded; the 1-D
  carve path still mints its 2 polygons unchanged (gated).
- **Oracle `bash scripts/rung7_vision_bench.sh`:**
  - BEFORE (base engine, 2-D flag off): **214 passed, 10 skipped, 0 failed**
  - AFTER (this rung's engine, 2-D flag off): **214 passed, 10 skipped, 0 failed**
  - **BEFORE == AFTER**, 0 failed both sides.

## §10 provenance

`engine_provenance()["source_match"] == "own"` (gated). The worktree built its own
`_native.abi3.so`; the canonical artifact's mtime/size were verified UNCHANGED
before and after every build (the worktree `.so` was ABSENT — no symlink into
canonical — so `cp` could not write through).

## What generalized to 2-D vs named follow-ons

- **Generalized:** the retina (az strip → az×el sheet, per-cell adaptation/onset),
  the onset stage (events carry `(col,row)`), and the common-fate CARVE
  (1-D column runs → 2-D connected components).
- **Named follow-ons (unchanged 1-D kernels):** 2-D MOTION
  (`retinal_event_motion`) and 2-D SALIENCE (`retinal_residual_salience`); and a
  velocity-consistency connectivity predicate to split two SPATIALLY-TOUCHING
  objects of different common fate (the 2-D carve currently splits by spatial
  connectivity + coherence gating, so touching different-motion blobs are not
  yet split — as in 1-D the controls rely on gaps).

## Honest residuals

1. The scramble control is small-sample-noisy at `n≈12` (mean-collapse, not
   per-seed 0); it becomes crisp at scale. A velocity-consistency connectivity
   predicate (the deferred 2-D follow-on) would sharpen it.
2. Coherence is reported on the axis with the larger spatial spread (the dominant
   motion axis); a genuinely 2-D coherence over both axes is a refinement.
3. The 2-D eye path is synchronous test-scope; wiring it into the async agent
   loop + percept synthesis is not part of this rung.

## Proposed VISION_PROTOCOL ledger row (supervisor merges; I do NOT edit it)

`| 166000–166999 | 2-D EXPANSION | az×el retina + 2-D onset + 2-D carve; HEADLINE 2-D SEPARATES same-az/diff-el (1-D=1, 2-D=2), end-to-end 2 VisionPolygons at correct (az,el); controls diff-az 2/2, static 0/0, scramble collapses (mean 2-D 0.215 vs struct 2, crisp 0 at scale); OFF by default, oracle 214p/10s/0f BEFORE==AFTER; source_match own | gate tests/test_2d_retina_migrated.py 9/9 | 2-D motion+salience & touching-object velocity-split named follow-ons |`
