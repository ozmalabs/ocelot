# RESULTS — CLOSING THE 2-D LOOP (2-D motion + 2-D salience)

Prereg: `VISION_2D_MOTION_SALIENCE_PREREG.md` (seed block 170000–170999,
committed ALONE at `876670212f` before any confirmatory number). Gate:
`tests/test_2d_motion_salience_migrated.py` (14 passed). Engine
`source_match = own` (this worktree's own build `a4f578f86c26`; canonical
artifact NOT modified).

## What landed

The 2-D expansion (166000) made the RETINA, ONSET events, and CARVE 2-D
(az×el), but left MOTION and SALIENCE 1-D (azimuth-only). This rung closes the
loop: onset → motion → carve → salience are all 2-D. Additive, OFF by default.

- **Rust kernel `retinal_event_motion_2d`** (`runners/dsl/src/cognitive_tasks.rs`)
  — a NEW pure `CognitiveTask` kind (NO new DSL Term enum variant; the 1-D
  `retinal_event_motion` kind byte-untouched). Payload
  `[n, c_0, r_0, e_0, …]`. Recovers a 2-D velocity `(v_az, v_el)` = the
  least-squares slope of `col`-on-epoch and `row`-on-epoch. Output
  `(v_az, v_el, dir_az, dir_el, speed=|(v_az,v_el)|, residual, coherence, n)`
  where `coherence = sqrt((s_ec² + s_er²) / (s_ee·(s_cc + s_rr)))` — the
  combined multiple-correlation that reduces EXACTLY to the 1-D `|Pearson r|`
  when there is no elevation spread, and is 1.0 for a noiseless sweep in ANY
  direction including pure elevation.
- **Rust kernel `retinal_residual_salience_2d`** — a NEW kind (1-D
  `retinal_residual_salience` byte-untouched). Same header as the 2-D carve:
  `[n_az, n_el, max_gap, vel_tol, k, c, r, e, …]`. Reduces events to one mean
  epoch per firing CELL, groups cells into 8-connected components (the SAME
  grouping the 2-D carve uses), fits each component's 2-D velocity, picks the
  DOMINANT component as the background `v_dom`, emits per-cell stride-3
  `[fired, raw=|v_comp|, residual=|v_comp − v_dom|]` (the 2-D vector-difference
  norm — 157000's egomotion-cancelled residual, now on the az×el field).
- **`seeds/retinal_motion_2d.json`** (`retinal_mint_motion_2d`) +
  **`seeds/retinal_salience_2d.json`** (`retinal_mint_salience_2d`) — the 2-D
  twins of the 1-D motion/salience rules, gated by `RetinaMotionParams2d` /
  `RetinaSalienceParams2d` DATA nodes.
- **`domains/photon_eye.py`** — mechanical only: `_build_2d` loads the 2-D
  motion/salience seeds + params when `visual_motion`/`visual_salience` are set;
  `settle_motion_2d` / `settle_salience_2d` pack the event stream;
  `motion_percepts_2d` / `salience_percepts_2d` read back. No decision.

## THE HEADLINE — MEASURED (1-D blind, 2-D sees)

Grid `n_az=16 × n_el=12`; noiseless unit-step sweeps; gates `MIN_COHERENCE=0.5`,
`MIN_EVENTS=2.5`. Both kernels fed the SAME event set (elevation collapsed for
the 1-D kernel).

### Motion — pure-elevation mover (col fixed, rows step +1/epoch)

| kernel | reading |
|---|---|
| **1-D `retinal_event_motion`** | **speed 0.000, coherence 0.000** — BLIND (all events at one azimuth column → zero azimuth spread) |
| **2-D `retinal_event_motion_2d`** | **v_az 0.000, v_el +1.000, coherence 1.000** — SEES (correct sign + magnitude) |

**Prediction met exactly.** Reversing the sweep flips the sign: `v_el` down
`+1.000`, up `−1.000`.

### Salience — pure-elevation mover vs azimuth background

Background rows 6–9 × cols 0–15 (epoch = col); vertical mover col 12, rows 0–2,
epochs 11/12/13 (timed so the 1-D collapse of col 12 stays consistent with the
background run — the mover is genuinely invisible to azimuth-only salience);
gap rows 3–5 separates the two 2-D components.

| kernel | max residual salience |
|---|---|
| **1-D `retinal_residual_salience`** | **0.0000** — MISSES (flat map; reads only the uniform azimuth background) |
| **2-D `retinal_residual_salience_2d`** | **1.4142 at cell (12, 0)** — RANKS the mover (`\|(v_az,v_el)\| = \|(1,1)\|`) |

Every 2-D cell with residual > 0.5 is EXACTLY a mover cell `{(12,0),(12,1),
(12,2)}`; the background (which IS the dominant motion) has residual 0.

## Able-to-fail controls — MEASURED

| control | 1-D | 2-D | predicted |
|---|---|---|---|
| **PURE-ELEVATION** (headline) | speed 0, coh 0 | v_el +1, coh 1 | 1-D blind / 2-D sees ✓ |
| **PURE-AZIMUTH** (row fixed, cols step) | speed 1, coh 1 | v_az +1, **v_el 0**, coh 1 | BOTH see; 2-D keeps 1-D case ✓ |
| **DIAGONAL** (col & row step) | — | v_az 1, v_el 1, speed √2=1.414, coh 1 | 2-D recovers BOTH ✓ |
| **SIGN** (reverse sweep) | — | v_el flips +1 → −1 | sign recovered ✓ |
| **STATIC** (no events) | — | all 0 | 0 ✓ |
| **SCRAMBLED** epochs (10-cell diagonal, 100-seed sweep) | — | mean coh **0.253** (struct 1.0), 14/100 above the 0.5 gate | coherence collapses ✓ |

Scramble is the same small-sample-noisy control the 166000 carve documented: a
single shuffle of a small component leaves a spurious `|r|>0.5` on a minority of
seeds, so it is stated as a DISTRIBUTION collapse (structured 1.0 → shuffled
mean 0.253, far below the gate), not a per-seed 0.

## End-to-end through the REAL 2-D mint rules

- **Motion:** pure-elevation mover driven through the 2-D eye build →
  `retinal_mint_motion_2d` mints EXACTLY 1 `RetinalMotionPercept` with
  `v_az 0.0, v_el 1.0, dir_el +1, coherence 1.0`.
- **Salience:** azimuth background + a spatially-separated vertical mover
  (col 3, rows 0–2) → `retinal_mint_salience_2d` mints one `RetinalSalience`
  per firing cell (67 cells); the top residual **1.414 is at mover cell (3, 0)**.

## Default-OFF / byte-identity (§9) + oracle

- Without `visual_motion`/`visual_salience`, the 2-D build has NO
  `RetinaMotionParams2d`/`RetinaSalienceParams2d`, the 2-D motion/salience seeds
  are unloaded, and `settle_motion_2d()`/`settle_salience_2d()` are no-ops. The
  2-D CARVE path still mints its 2 same-az/diff-el polygons unchanged (gated).
- The 1-D `retinal_event_motion`/`retinal_residual_salience` kinds and seeds are
  byte-untouched; a horizontal mover is still read by the 1-D pipeline as before
  (gated: `test_1d_motion_and_salience_paths_are_unchanged`).
- **Oracle `bash scripts/rung7_vision_bench.sh`:**
  - BEFORE (this worktree's baseline engine, no new kernels): **214 passed, 10 skipped, 0 failed**
  - AFTER (this rung's engine, flags off): **214 passed, 10 skipped, 0 failed**
  - **BEFORE == AFTER**, 0 failed both sides.

## §10 provenance

`engine_provenance()["source_match"] == "own"` (gated). The worktree built its
own `_native.abi3.so` (`a4f578f86c26`) via `scripts/engine_build.sh`
(`cp --remove-destination`, symlink-safe); the canonical artifact's
md5/size/mtime were verified UNCHANGED (`3c96c41f…`, size 7808680, mtime
1784874414) before and after every build.

## Honest residuals

1. Coherence is the COMBINED multiple-correlation over both axes (a genuine
   improvement over the 2-D carve's "coherence on the dominant axis"), but the
   `residual` field is the unexplained 2-D spatial SSE, not a normalized score.
2. The scramble control is small-sample-noisy at n=10 (mean-collapse, not
   per-seed 0), inherited from the 166000 carve; it sharpens as components grow.
3. The 2-D salience groups by 8-connected spatial components + dominant-motion
   `v_dom` (the SAME grouping the 2-D carve uses); splitting two
   spatially-TOUCHING objects of different common fate is still the named
   velocity-split follow-on. The salience headline relies on a spatial gap, as
   the 166000 carve controls do.
4. Both 2-D headlines are demonstrated on noiseless synthetic sweeps at the
   kernel grain; wiring 2-D motion/salience percepts into the async agent loop
   + percept synthesis is not part of this rung.

## Proposed VISION_PROTOCOL ledger row (supervisor merges; I do NOT edit it)

`| 170000–170999 | CLOSING THE 2-D LOOP (2-D motion + 2-D salience) | new Rust kinds retinal_event_motion_2d + retinal_residual_salience_2d (NO new DSL Term variant; 1-D kinds byte-untouched); HEADLINE pure-elevation motion 1-D BLIND (speed 0, coh 0) vs 2-D SEES (v_el +1, coh 1), sign flips; 2-D residual salience RANKS a vertical mover (max 1.414 at the mover) the 1-D salience MISSES (max 0.0); controls pure-az BOTH see (2-D v_el 0), diagonal 2-D recovers both (speed √2), static 0, scramble mean coh 0.253; end-to-end through real mint rules; OFF by default, 2-D-carve + 1-D paths byte-unchanged, oracle 214p/10s/0f BEFORE==AFTER; source_match own | gate tests/test_2d_motion_salience_migrated.py 14/14 | velocity-split of touching different-motion objects still the named follow-on |`
