# VISION — KILL THE QUADRATIC: prune the accumulating settled tasks (PREREG)

**Block 183000.** Committed BEFORE any recorded number. Seed claim `183000-183999`
CLEAN (`python3 scripts/seed_claim.py 183000 183999`). `source_match` must be
`own`/`shared`. No Rust is built (adapter/graph fix); the canonical `.so`
(md5 `417f667716d71ed7d98bae5df25fe9df`) must be UNCHANGED.

## What 182000 diagnosed (do not re-derive)

The 2-D photon eye mints one `photon_transduce_onset` CognitiveTask per cell per
tick. Left un-pruned they accumulate; the onset rule joins
`retina -> column -> rod -> has_task -> task`, so every accumulated task is
re-examined on every `run_rules` call, and per-tick cost CLIMBS over the run
(25 s/tick at 4800 cells and climbing; 240×180 did not finish in 30 min). The
eye already owns the pruning idea (`_refresh_settled`) but it is 1-D-only (it
gates on `self._percepts`, empty on the 2-D sheet), so the 2-D scaling path never
pruned via the eye.

## The fix (graph/adapter, no Rust)

`GraphEye.prune_settled_tasks()` — a mechanical host-I/O method that removes the
terminal-status (`done/failed/stale/superseded/shed`) retina CognitiveTask nodes.
It publishes nothing and decides nothing; percepts / polygons / onset events /
motion / salience are minted into their OWN node types by `run_rules` BEFORE a
task reaches terminal status and persist independently of the task. `_refresh_settled`
gains a guarded 2-D branch that calls it (the 1-D path is byte-unchanged), and the
2-D carve/measure scaling path (`doom_carve_scale_measure._tick`) is wired to the
eye's own prune. THE SETTLEMENT AXIOM MADE CONCRETE: a settled task left in the
graph is an uncleared residual.

## Falsifiable claims + prereg thresholds

Measured on the COMMITTED real `defend_the_line` fixture
(`tests/fixtures/doom_carve_scale/frames_160x120.npz`), VizDoom-free, via
`scripts/eye_timing_measure.py`. Run SOLO (timing is a shared-resource measure).

### C1 — BYTE-IDENTITY (PRIMARY; a speedup that changes any output is REJECTED)

The full common-fate carve protocol run WITH the prune vs WITHOUT it must produce
**byte-identical** outputs at every affordable resolution (300 / 1200 / 4800
cells):

- **C1a** identical VisionPolygon set (spans + direction/speed/coherence/n_events,
  full precision); AND
- **C1b** identical onset-event stream (the async percept the carve reads:
  sorted `(column_index, row_index, epoch)`); AND
- **C1c** identical `union_iou` and `carve_precision`.

**C1d** — the 182000 harness (`M.carve_scale_run`, seed 182000), whose per-tick
prune now delegates to `prune_settled_tasks`, reproduces the LANDED 160×120 carve:
fires `n_polygons ≥ 1`, `union_iou ≥ 0.10`, `carve_precision ≥ 0.85` (the 182000
H1c band; the exact `4 / 0.1215 / 0.978` recorded as a fact — fixture luma is
float32, so a last-place Poisson hair may shift it). PASS = all of C1a–C1d.

### C2 — QUADRATIC → LINEAR, the accumulation axis (THE HEADLINE)

Per-tick cost vs TICK INDEX at fixed 4800 cells (8 ticks, real motion frames),
NO-PRUNE vs PRUNE. Pruning must convert the cumulative cost from ~quadratic in
run length to ~linear:

- **C2a** NO-PRUNE cumulative-cost-vs-ticks exponent **> 1.7**; PRUNE **< 1.3**.
- **C2b** NO-PRUNE per-tick last/first ratio **> 3** (climbing); PRUNE **< 1.6**
  (flat).
- **C2c** NO-PRUNE tasks accumulate (`tasks_left > 10000`); PRUNE `tasks_left == 0`.

### C3 — CELLS scaling + representative speedup

Mean steady-state per-tick vs cells across the sweep, NO-PRUNE (≤4800) vs PRUNE
(full sweep incl. 19200):

- **C3a** NO-PRUNE per-tick-vs-cells exponent **> 1.7** (super-linear).
- **C3b** the EXPONENT DROP `exponent_noprune − exponent_prune(≤4800) ≥ 0.15`
  (the process-independent robust claim).
- **C3c** representative absolute speedup at 4800 cells **≥ 10×**.

**Prereg'd honest disclosure (part of the claim, NOT a hedge added later):**
task-pruning does NOT make the cells axis LINEAR — the pruned per-tick-vs-cells
exponent stays super-linear (~1.8) because a SECOND O(cells²) cost remains: the
onset-mint rule's per-tick event scan, whose event count grows with cells. That
residual is the NAMED next lever (event-stream windowing / SIMD / per-area
index), NOT task accumulation. The quadratic THIS rung kills is the
accumulation-over-run-length (C2); the cells axis gets a real exponent drop (C3b)
+ a large constant-factor speedup (C3c), reported without overclaim.

### C4 — 240×180 completes

With the prune, 240×180 (43200 cells) per-tick is **bounded** (< 300 s/tick), so a
full run COMPLETES (contrast: no-prune 240×180 did not finish in 30 min). Reported
as a FACT; no real-time claim at any resolution.

## Oracle + gate + provenance

- Oracle `bash scripts/rung7_vision_bench.sh`: **0 failed, BEFORE == AFTER** (the
  fix touches a hot vision path; the oracle unchanged is load-bearing). Report the
  worktree count both sides.
- Gate `tests/test_eye_timing_migrated.py` — self-contained on the committed
  fixture; pins C1 (byte-identity), C2 (accumulation), and a scope check that the
  prune removes ONLY terminal-status retina tasks.
- Existing `tests/test_doom_carve_scale_migrated.py` (182000) must stay green
  (proves the wiring is byte-identical on the landed carve).
- `git diff --stat` limited to `domains/photon_eye.py` (+ method, guarded 2-D
  branch) and `scripts/doom_carve_scale_measure.py` (guarded delegation); new
  files: the measure script, the gate, results.
- Scaling curves saved under `results/eye_timing/`.

## Named residual (explicit)

Real-time at full resolution is NOT delivered here and is not claimed. The pruned
per-tick is still super-linear in cells (the onset-mint event scan); real-time at
high resolution needs the SIMD / per-area-index accelerator (the documented next
lever), which this rung deliberately does not attempt.
