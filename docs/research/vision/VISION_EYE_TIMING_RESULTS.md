# VISION — KILL THE QUADRATIC: prune the accumulating settled tasks (results)

**Block 183000.** Prereg: `VISION_EYE_TIMING_PREREG.md` (commit
`5fa47b38d32b3147c8e7af7be95ff30547aa47ce`, committed BEFORE any number).
`source_match = "own"`. Canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df`,
mtime Jul 24 17:41 — UNCHANGED (no Rust built; the fix is graph/adapter-level).
Measured SOLO on the committed real `defend_the_line` fixture
(`tests/fixtures/doom_carve_scale/frames_160x120.npz`), VizDoom-free.

## Headline

The 2-D photon eye's slowness at scale (block 182000) is per-cell
`photon_transduce_onset` CognitiveTask nodes accumulating UN-PRUNED: the onset
rule joins `retina → column → rod → has_task → task`, so every accumulated task
is re-examined on every `run_rules` call and per-tick cost CLIMBS over the run.
The fix is the eye's OWN `GraphEye.prune_settled_tasks()` — clear the
terminal-status retina tasks each tick. It is **byte-identical** (the carve is
unchanged, proven both by prune-vs-no-prune identity AND by reproducing the
landed 182000 carve exactly), and it converts the accumulation from
**quadratic-in-run-length to linear** (cumulative-cost-vs-ticks exponent
**2.27 → 0.78**), a **28.5× per-tick speedup at 4800 cells**, and makes
**240×180 complete** (bounded ~60 s/tick) where no-prune did not finish in 30 min.

Honest boundary (prereg'd, not a hedge): task-pruning does **not** linearise the
per-tick-vs-CELLS axis — it drops the exponent **2.03 → 1.83** and removes a
28.5× constant factor, but the pruned per-tick stays super-linear because a
SECOND O(cells²) cost remains (the onset-mint rule's per-tick event scan, event
count ∝ cells). That residual is the NAMED next lever (event-stream windowing /
SIMD / per-area index), not task accumulation. No real-time claim is made.

## Where the fix went, and why

**Graph/adapter — NO Rust.** The prune is mechanical host I/O (remove nodes the
engine has already finished with), so it is admissible adapter work, not an
agent decision, and needs no engine change:

- `domains/photon_eye.py` — new `GraphEye.prune_settled_tasks()` removes the
  `done/failed/stale/superseded/shed` retina CognitiveTask nodes and returns the
  count. It reads no `self._percepts` (empty on the 2-D sheet), so unlike the
  1-D-only `_refresh_settled` it works on the 2-D scaling path. `_refresh_settled`
  gains a GUARDED 2-D branch that calls it and returns (the 1-D body is
  byte-unchanged; every `latest()`/`processed_count()` caller in the tree is a
  1-D eye, and even a 2-D caller sees the same `None`/`0` it did before — only
  settled residue is removed).
- `scripts/doom_carve_scale_measure.py` — its per-tick `_prune_done_tasks` now
  DELEGATES to `eye.prune_settled_tasks()` (the same terminal-status retina-task
  set it always removed), so the scaling path uses the eye's OWN prune. The
  182000 gate green + the landed-carve reproduction prove this is byte-identical.

## C1 — BYTE-IDENTITY (the primary gate) — PASS

Full carve protocol WITH prune vs WITHOUT it, on the fixture:

| grid | cells | motion | polygons identical | onset stream identical | union_iou / precision identical | tasks_left prune / no-prune |
|---|---|---|---|---|---|---|
| 20×15   | 300  | full (13) | ✅ (0==0) | ✅ (1 event)  | ✅ | 1 / 5701 |
| 40×30   | 1200 | full (13) | ✅ (0==0) | ✅ (7 events) | ✅ | 1 / 22801 |
| 80×60   | 4800 | cap 4     | ✅ (0==0) | ✅ (4 events) | ✅ | 1 / 48001 |

- **C1d — the landed 182000 carve reproduced EXACTLY.** The 182000 harness
  (`M.carve_scale_run`, seed 182000), whose per-tick prune now delegates to
  `prune_settled_tasks`, at 160×120: **4 VisionPolygons, union_iou 0.1215,
  precision 0.9784, recall 0.1219, false-poly-rate 0.0** — identical to the
  landed 182000 headline (4 / 0.1215 / 0.978). The wiring changed nothing.

The onset-event stream (the async percept the carve reads) is byte-identical
across prune/no-prune even where 0 polygons fire — the prune provably changes
nothing the eye computes; it only removes finished-with residue.

## C2 — QUADRATIC → LINEAR (accumulation axis, the headline) — PASS

Per-tick cost vs TICK INDEX at fixed 4800 cells (8 ticks, real motion frames):

| tick | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | last/first | cum-vs-ticks exp | tasks left |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **no prune** (s) | 1.21 | 2.41 | 5.26 | 9.39 | 14.7 | 21.8 | 31.2 | 42.1 | **34.8×** | **2.27** | 38400 |
| **prune** (s)    | 1.25 | 0.73 | 0.69 | 0.74 | 0.73 | 0.73 | 0.74 | 0.74 | **0.59×** | **0.78** | **0** |

No-prune per-tick climbs ∝ tick index (cumulative ~quadratic); prune is FLAT
(cumulative ~linear). This is exactly "25 s/tick and climbing → ~0.8 s/tick flat"
made precise. Thresholds: no-prune cum-exp 2.27 > 1.7 ✅, prune 0.78 < 1.3 ✅;
last/first 34.8 > 3 ✅ and 0.59 < 1.6 ✅; tasks 38400 > 10⁴ ✅ and 0 ✅.

## C3 — CELLS scaling + speedup — PASS (with prereg'd honest residual)

Mean steady-state per-tick vs cells:

| cells (grid) | no prune (ms) | prune (ms) | speedup |
|---|---|---|---|
| 300   (20×15)   | 74.3    | 5.7    | 13× |
| 1200  (40×30)   | 1210    | 46.7   | 26× |
| 4800  (80×60)   | 20750   | 733    | **28.5×** |
| 19200 (160×120) | — (prohibitive) | 10818 | — |

- Fitted exponent (log-log per-tick vs cells): **no-prune 2.03**, prune 1.74
  (≤4800) / **1.83** (full sweep). Exponent DROP 2.03 − 1.74 = **0.29 ≥ 0.15** ✅.
- Speedup at 4800 cells: **28.5× ≥ 10×** ✅.
- **Residual (prereg'd):** the pruned exponent is ~1.8, NOT 1 — pruning removes
  the task-accumulation cost (itself ~O(cells²): the no-prune − prune penalty
  fits exponent ≈2.06) but leaves a second O(cells²) per-tick cost, the
  onset-mint rule's event scan (events ∝ cells). The quadratic THIS rung kills is
  the accumulation-over-run-length (C2); the cells axis is a real exponent drop +
  a 28.5× constant-factor win. Curves: `results/eye_timing/scaling.png`.

## C4 — 240×180 completes — PASS (as a FACT, no real-time claim)

With the prune, 240×180 (43200 cells) per-tick is **bounded** — 122 / 62 / 60 s
(first tick carries build/warm; steady ~60 s/tick) — so a full run COMPLETES
(contrast: no-prune 240×180 did not finish in 30 min, block 182000). Resolution/
throughput reached, reported bare: pruned per-tick is **~0.73 s @ 4800 cells,
~10.8 s @ 19200, ~60 s @ 43200** — this is NOT real-time at any of these grids.

## Per-criterion table

| id | criterion | measured | pass |
|---|---|---|---|
| C1a/b/c | prune≡no-prune: polygons + onset stream + iou/precision, 300/1200/4800 | identical (all) | ✅ |
| C1d | landed 160×120 carve reproduced | 4 / 0.1215 / 0.9784 / 0 false | ✅ |
| C2a | accum cum-exp: no-prune >1.7, prune <1.3 | 2.27 / 0.78 | ✅ |
| C2b | per-tick last/first: no-prune >3, prune <1.6 | 34.8 / 0.59 | ✅ |
| C2c | tasks: no-prune >10⁴, prune ==0 | 38400 / 0 | ✅ |
| C3a | cells exponent no-prune >1.7 | 2.03 | ✅ |
| C3b | exponent drop ≥0.15 | 0.29 | ✅ |
| C3c | speedup @4800 ≥10× | 28.5× | ✅ |
| C4 | 240×180 pruned per-tick bounded (<300 s) | 60 s, completes | ✅ |

## Provenance & discipline

- Oracle `bash scripts/rung7_vision_bench.sh`: **214 passed, 10 skipped, 0
  failed** (worktree-without-`data/`/`chess` baseline). BEFORE == AFTER: the fix
  is additive to `photon_eye.py` (1-D path byte-unchanged) + a same-set delegation
  in the measure script; the oracle's fixed file list has no modified listed file.
- Gate `tests/test_eye_timing_migrated.py`: **4 passed** (byte-identity 20×15 +
  40×30; accumulation quadratic-vs-flat @1200; prune-scope check). 182000 gate
  `tests/test_doom_carve_scale_migrated.py`: **7 passed** (wiring byte-identical).
- No Rust built; canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df` UNCHANGED.
- `source_match = own`. No new Term / no new CognitiveTask kind / no new seed.

## Honest residuals

- **Real-time at full resolution is NOT delivered** and not claimed. The pruned
  per-tick is still super-linear in cells (the onset-mint event scan, O(cells²)),
  so 240×180 completes but at ~60 s/tick. Real-time needs the SIMD / per-area
  dirty-index accelerator (the documented next lever) — a separate rung.
- **Byte-identity of the FIRING carve was proven by reproduction, not by a
  no-prune run at 160×120** (that run IS the quadratic being killed —
  prohibitive). The no-prune/prune identity is proven at 300/1200/4800 on the
  full computation (polygons + onset stream), and the 160×120 landed value is
  reproduced exactly; together these establish the prune changes no output.
- The cells-exponent absolute value is protocol-dependent (a dynamic scene with
  onsets ∝ cells makes it ~2 either way); the process-independent robust results
  are the accumulation cum-exp drop (C2) and the 28.5× constant-factor speedup.

## Proposed VISION_PROTOCOL ledger row

`183000 | kill the settled-task accumulation quadratic (GraphEye.prune_settled_tasks) | per-cell transduce tasks accumulate un-pruned → run_rules re-scans them → per-tick CLIMBS; prune the terminal-status retina tasks each tick | byte-identical (prune≡no-prune polygons+onset stream @300/1200/4800; landed 160×120 carve reproduced EXACTLY 4/0.1215/0.978); accumulation cum-vs-ticks exp 2.27→0.78, per-tick flat vs climbing, 28.5× @4800; cells exp 2.03→1.83 (drop only — O(cells²) event-scan residual remains); 240×180 completes (~60s/tick) vs no-prune >30min | graph/adapter (no Rust/Term/kind/seed); .so md5 unchanged; gate test_eye_timing_migrated 4/4 + test_doom_carve_scale 7/7; oracle 214/10/0 BEFORE==AFTER; source_match own | real-time at full res needs SIMD/per-area-index (named follow-on)`
