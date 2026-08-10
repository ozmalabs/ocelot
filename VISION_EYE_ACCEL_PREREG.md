# VISION — THE ACCELERATION: a droppable, byte-identical vectorized mirror of the uniform retina sheet (PREREG)

**Block 184000.** Committed BEFORE any recorded number. Seed claim
`184000-184999` CLEAN (`python3 scripts/seed_claim.py 184000 184999` +
`check_claim(184000,184999)` → OK). `source_match` must be `own`/`shared`.
This rung BUILDS Rust — the canonical `.so`
(`/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`,
md5 `417f667716d71ed7d98bae5df25fe9df`, mtime Jul 24 17:41) must be UNCHANGED
by this worktree; the supervisor REBUILDS CANONICAL on merge.

## What 183000 left standing (do not re-derive)

183000 killed the settled-task ACCUMULATION quadratic (`prune_settled_tasks`,
byte-identical, cum-vs-ticks exp 2.27→0.78, 28.5× @4800). But the CELLS axis is
still ~quadratic (exponent **1.83**), and per-tick is still ~**0.73 s @4800
cells** — NOT real-time. The residual O(cells²) is the onset-mint rule's per-tick
`run_rules` join over the retina, and the per-cell transduce/onset work is a
**sheet of IDENTICAL microcircuits** processed one CognitiveTask node at a time.

## The fix (a DROPPABLE, BYTE-IDENTICAL vectorized mirror — the governing principle)

An accelerator is a droppable, byte-identical MIRROR. The graph/`run_rules`
engine STAYS the correctness oracle; the fast path reproduces it EXACTLY; turning
it OFF falls back to the graph path and yields IDENTICAL results. Concretely:

- A Rust batch graph op `retina_onset_batch` (`runners/dsl/src/cognitive_tasks.rs`,
  PyO3 entrypoint `PySubstrate::retina_onset_batch` in `runners/dsl/src/py.rs`)
  computes the WHOLE 2-D retina sheet in ONE FFI crossing, O(cells): it reuses
  the shared `execute_kernel("photon_transduce_onset", …)` VERBATIM and mirrors
  BOTH graph rules — `photon_apply_receptor_transduction` (rod
  activation/adaptation/caught_quanta/input_epoch from output[0..2]) and
  `retinal_mint_onset_2d` (threshold output[3], per-cell refractory, mint
  `RetinalOnsetEvent`) — with the same interned keys and Value types. NO
  CognitiveTask/TaskResult nodes, NO `run_rules` join.
- **NO new Term enum variant.** A new batch graph op + PyO3 entrypoint only.
- **Droppable:** the adapter (`GraphEye.submit_photons_2d`) branches on
  `context['retina_accel']`. OFF ⇒ the existing graph path runs unchanged (the
  oracle). `context['retina_accel_perturb']` injects a WRONG mirror for the
  non-vacuity falsifier.

## Falsifiable claims + prereg thresholds

Measured on the COMMITTED real `defend_the_line` fixture
(`tests/fixtures/doom_carve_scale/frames_160x120.npz`), VizDoom-free, via
`scripts/eye_accel_measure.py`. Run SOLO (timing is a shared-resource measure);
multiple trials; report median + spread.

### C1 — BYTE-IDENTITY (PRIMARY; a speedup that changes any output is REJECTED)

The full common-fate carve protocol run with the accelerator ON vs OFF must
produce **byte-identical** outputs at 300 / 1200 / 4800 / 19200 cells:

- **C1a** identical VisionPolygon set (spans + direction/speed/coherence/
  n_events, full precision); AND
- **C1b** identical onset-event stream (sorted `(column_index, row_index,
  epoch)`); AND
- **C1c** identical `union_iou` and `carve_precision`; AND
- **C1d** identical per-cell transduced state (rod `adaptation` vector, full
  precision — the state that persists across ticks).

**C1e** — the landed 160×120 Doom carve reproduces EXACTLY under the accelerator:
`n_polygons == 4`, `union_iou == 0.1215`, `carve_precision == 0.9784`,
`false_poly_rate == 0.0` (the landed 183000 headline). PASS = all of C1a–C1e.

### C2 — DROPPABLE (ON ≡ OFF)

A flag/param turns the accelerator OFF → the graph path runs → results IDENTICAL
(same gate as C1, the OFF arm IS the oracle). PASS = C1 holds with ON and OFF as
the two arms.

### C3 — CELLS AXIS LINEARIZED + speedup

Mean steady-state per-tick vs cells (300/1200/4800/19200), accelerator ON vs OFF
(OFF = the 183000 pruned graph path). Fit the log-log exponent.

- **C3a** accelerated cells-axis exponent ≤ **1.3** (down from the 183000 pruned
  **1.83**).
- **C3b** exponent DROP (OFF − ON) ≥ **0.4**.
- **C3c** per-tick speedup at 4800 cells ≥ **5×** (accel vs the 183000 pruned
  graph path).
- **C3d** report the resolution/fps reached as a FACT; state honestly whether
  real-time (≥ ~10 fps, ≤ ~0.1 s/tick) is met at any grid, and what remains.

### C4 — FALSIFIER FOR THE BYTE-IDENTITY CHECK (non-vacuity)

A deliberately-perturbed kernel (`retina_accel_perturb`) MUST break the ON≡OFF
match: the perturbed accelerator's onset-event stream ≠ the graph path's. PASS =
`perturb` diverges (proves C1's identity check can detect a wrong mirror).

## Discipline

- SEPARATE prereg commit (this file alone) BEFORE any number.
- Oracle `bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE == AFTER, run
  with the accelerator OFF by default (so the whole bench is byte-unchanged) AND
  confirm ON≡OFF on the eye path.
- Gate `tests/test_eye_accel_migrated.py` pins C1 (ON≡OFF byte-identity), C4
  (perturbed-kernel falsifier), and the C3 exponent/speedup at the mechanism
  grain. Self-contained (committed small fixture).
- `source_match ∈ {own, shared}`.
- Save curves + fps under `results/eye_accel/`.

## Honest residual named UP FRONT (not a hedge)

Even at exponent ~1.0 the per-tick has an O(cells) FLOOR: the batch still touches
every cell every tick (SIMD over a uniform sheet). The next lever beyond SIMD is
the per-area DIRTY-INDEX (process only CHANGED cells = O(surprise), not O(cells)),
which is a SEPARATE rung — this rung linearizes the sheet, it does not make it
sub-linear. Whether real-time at full resolution is delivered is reported as a
FACT, not claimed.
