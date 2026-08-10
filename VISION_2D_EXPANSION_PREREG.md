# PREREG — THE 2-D EXPANSION (azimuth×elevation retina; Rungs 1-4 were a 1-D strip)

**Seed block: 166000–166999** (`check_claim(166000, 166999)` CLEAN — no
collision detected; drawn once at `default_rng(166000)`). Committed BEFORE any
confirmatory number.

## The claim

Rungs 1-4 (onset / motion / carve / salience) are 1-D because the photon eye is
a 1-D AZIMUTH STRIP (`domains/photon_eye.py`: `n_az` columns over a central
`vband`, elevation collapsed). This rung EXTENDS the retina to a 2-D
azimuth×elevation RECEPTOR SHEET — each `(az, el)` cell a receptor with its OWN
adaptation / onset-event history; onset events carry `(col, row)` position — and
generalizes the event-native COMMON-FATE CARVE from a 1-D column to a 2-D cell
grid.

**HEADLINE (the falsifiable proof 2-D adds real capability):** two objects at
the SAME azimuth but DIFFERENT elevation are ONE thing to the 1-D carve (which
collapses elevation and merges them into a single azimuth span) and TWO things
to the 2-D carve (which keeps them apart as two connected components at their
correct `(az, el)` locations).

**HONEST SCOPE (stated, not hidden):** this rung delivers the 2-D RETINA + 2-D
ONSET + 2-D CARVE. 2-D MOTION and 2-D SALIENCE are NAMED FOLLOW-ONS (the 1-D
`retinal_event_motion` / `retinal_residual_salience` kernels are unchanged). The
2-D carve splits objects by 2-D spatial connectivity (8-neighbour) + a
coherence/`n_events` gate; splitting two SPATIALLY-TOUCHING objects of DIFFERENT
common fate is likewise a named follow-on (as in 1-D the controls use gaps).

## The mechanism (fixed before the confirmatory run)

- **Rust kernel `retinal_common_fate_carve_2d`** (a new pure `CognitiveTask`
  kind — NO new DSL Term enum variant; peer of `retinal_common_fate_carve`).
  Payload `[n_az, n_el, max_gap, vel_tol, k, c_0, r_0, e_0, …, c_{k-1}, r_{k-1},
  e_{k-1}]` — retina width/height, two params, and the `k` onset events
  `(col, row, own-epoch)`. It:
  1. reduces the events to one mean epoch per firing CELL `(col, row)`;
  2. groups firing cells into maximal 8-connected COMPONENTS (Chebyshev-1
     adjacency in the `(col, row)` grid) — a spatial elevation/azimuth gap
     separates components;
  3. for each component fits a 2-D motion by least squares (`col` on epoch,
     `row` on epoch) → `direction = sign(Δcol/Δe slope)`, `speed = |2-D velocity|`,
     `coherence = |Pearson r| of the dominant axis`, `n_events`.
  Output is a FIXED per-cell layout of stride 9 (flat index `f = row*n_az + col`):
  `[is_group_start, col_min, col_max, row_min, row_max, direction, speed,
  coherence, n_events]`, each component's block written at its ANCHOR cell (the
  member with the smallest flat index; all other cells zero). A per-cell graph
  rule then mints exactly one polygon per component, in the Rung-1..4 house style.
- **Seed `seeds/retinal_onset_2d.json`** rule `retinal_mint_onset_2d`: matches a
  `RetinalCell` (with `col`, `row`, flat `index`) against its rod receptor's
  done `photon_transduce_onset` task (the SAME byte-identical onset kernel Rung 1
  uses) and mints a `RetinalOnsetEvent{column_index, row_index, magnitude_db,
  epoch}` above the dB threshold, refractory per cell. `RetinaOnsetParams2d` is
  the graph-data gate.
- **Seed `seeds/retinal_carve_2d.json`** rule `retinal_mint_carve_2d`: matches
  every `RetinalCell` against the done 2-D carve task and mints a
  `VisionPolygon{col_min, col_max, row_min, row_max, direction, speed, coherence,
  n_events, epoch}` iff `output[index*9+0] == 1.0`, `coherence > min_coherence`,
  AND `n_events > min_events` (both DATA on a `RetinaCarveParams2d` node), once
  per cell-epoch via a `carve2d_epoch` guard.
- **OFF by default (§9):** the whole 2-D path engages only under
  `context["retina_2d"]`, which builds the `RetinalCell` sheet + the
  `RetinaOnsetParams2d` / `RetinaCarveParams2d` gate nodes and loads the two 2-D
  seeds. Absent it, ZERO 2-D nodes/seeds exist, the 1-D `RetinalColumn` strip and
  Rungs 1-4 are byte-unchanged, and the 2-D kernel is never invoked.
- **Python is mechanical only:** the adapter builds the `(az, el)` cell grid,
  packs `RetinalOnsetEvent` `(column_index, row_index, epoch)` into the 2-D carve
  task payload, and reads `VisionPolygon` nodes back out. No decision in Python.

## Headline QUANTITY + pre-registered claim

Controlled synthetic scene on an `n_az = 16 × n_el = 12` retina: TWO objects at
the SAME azimuth columns `[4..9]` moving with the SAME left-to-right common fate
(cell `(col, row)` fires onset at epoch `= col − 4`), object **A** at elevation
rows `[2..3]` and object **B** at elevation rows `[8..9]` (an elevation gap, rows
`[4..7]`, between them). The identical events are fed to BOTH carves — collapsed
to `(col, epoch)` for the 1-D kernel, kept as `(col, row, epoch)` for the 2-D
kernel — and both are driven through their REAL mint rules.

> **1-D carve → EXACTLY 1 coherent `VisionPolygon` (elevation collapsed, the two
> objects conflated into one azimuth span `col 4..9`). 2-D carve → EXACTLY 2
> coherent `VisionPolygon`s, one at `(col 4..9, row 2..3)` and one at
> `(col 4..9, row 8..9)` — the two objects separated at their correct
> `(az, el)` locations.**

Because the synthetic sweeps are noiseless the per-object diagonals are exactly
linear (`coherence = 1.0`), so both counts are exact, not intervals.

## Able-to-fail controls (read MEASURED values; no constant re-derived in Python)

1. **SAME az / DIFF el (the headline)** → 2-D: **2**, 1-D: **1**.
2. **DIFFERENT az** (A at `col 0..3`, B at `col 10..13`, both `row 4..5`, same
   motion, an azimuth gap between them) → 2-D: **2**, 1-D: **2** (2-D does NOT
   over-split a scene the 1-D carve already separates).
3. **STATIC / no events** → 2-D: **0**, 1-D: **0**.
4. **SCRAMBLED epochs** (the headline scene with per-event epochs shuffled — the
   common-fate diagonal destroyed) → 2-D: **0** coherent, 1-D: **0** coherent
   (each component/run falls below `min_coherence`).

## Default-OFF / byte-identity (§9) + oracle

- With `retina_2d` OFF: no `RetinalCell`, no `RetinaOnsetParams2d`, no
  `RetinaCarveParams2d`, the 2-D seeds unloaded, and the 2-D carve task never
  built. Rungs 1-4 (onset / motion / carve / salience) byte-unchanged.
- Oracle `bash scripts/rung7_vision_bench.sh` = **0 failed, BEFORE == AFTER**
  (2-D flag off on both sides). Both counts reported.

## §10 provenance

The gate asserts `engine_provenance()["source_match"] in ("own", "shared")` —
never a pinned hash, never `== "shared"`.

## Gate

`tests/test_2d_retina_migrated.py`: the kernel called directly (headline 1-vs-2
plus the four controls), the two objects carved end-to-end through the 2-D eye
build, default-OFF byte-identity, a source audit that the 2-D carve reads only
the `RetinalOnsetEvent` stream, and §10 provenance.

## NO TIMING CLAIM

Another agent runs in parallel. This rung's claim is CORRECTNESS ONLY — 2-D
disambiguates what 1-D conflates. No wall-clock number is asserted.
