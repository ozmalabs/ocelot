# VISION — THE ACCELERATION: a droppable, byte-identical vectorized mirror of the uniform retina sheet (results)

**Block 184000.** Prereg: `VISION_EYE_ACCEL_PREREG.md` (committed ALONE BEFORE
any number). `source_match = "own"`. **This rung BUILDS Rust.** The canonical
`.so` (`…/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`,
md5 `417f667716d71ed7d98bae5df25fe9df`, mtime Jul 24 17:41) is UNCHANGED — the
build happened only in this worktree. **THE SUPERVISOR MUST REBUILD CANONICAL ON
MERGE (Rust changed).** Measured SOLO on the committed real `defend_the_line`
fixture (`tests/fixtures/doom_carve_scale/frames_160x120.npz`), VizDoom-free, via
`scripts/eye_accel_measure.py`.

## Headline

183000 killed the settled-task ACCUMULATION quadratic but left the CELLS axis at
exponent **1.83** and ~**0.73 s/tick @4800** — the residual O(cells²) is the
onset-mint rule's per-tick `run_rules` join, and the per-cell transduce/onset
work is a **sheet of IDENTICAL microcircuits** processed one CognitiveTask node at
a time. This rung ACCELERATES that uniform sheet with a Rust batch graph op that
computes the WHOLE sheet in ONE FFI crossing, O(cells): it reuses the shared
`photon_transduce_onset` kernel VERBATIM and mirrors both graph rules —
`photon_apply_receptor_transduction` + `retinal_mint_onset_2d` — minting the same
`RetinalOnsetEvent`s with NO CognitiveTask nodes and NO `run_rules` join.

The mirror is **byte-identical** and **droppable**, the cells axis is
**linearized** (exponent **1.838 → 1.072**), and the per-tick speedup at 4800
cells is **109×**. The 2-D transduce+onset sheet now runs at **30.5 fps at
160×120** (19200 cells) — **REAL-TIME at full fixture resolution** — where the
183000 graph path ran at 0.09 fps (a **335×** per-tick win at 19200).

## Where the kernel went, and how it stays droppable

- **Rust batch graph op** `retina_onset_batch`
  (`runners/dsl/src/cognitive_tasks.rs`) — one O(cells) pass, graph lock held
  once. Reuses `execute_kernel("photon_transduce_onset", …)` VERBATIM (the shared
  oracle kernel), then mirrors the two rules' effects with the same interned keys
  and Value types: rod `prev_activation`/`activation`/`adaptation`/`caught_quanta`/
  `input_epoch` from output[0..2]; threshold output[3] + per-cell refractory →
  mint `RetinalOnsetEvent{column_index,row_index,magnitude_db,epoch,logical_time}`
  + `column -has_onset_event-> event` (Γ-admitted) + `column.last_onset_epoch`.
- **PyO3 entrypoint** `PySubstrate::retina_onset_batch`
  (`runners/dsl/src/py.rs`) — a thin handoff: parallel `rod_ids`/`col_ids`/ragged
  `payloads` in, minted count out. **NO new Term enum variant** — a batch graph op
  + PyO3 entrypoint only.
- **Adapter** `GraphEye.submit_photons_2d` (`domains/photon_eye.py`) branches on
  `context['retina_accel']`: ON → `_submit_photons_2d_accel` builds the SAME
  per-cell payloads (bulk-reading each rod's adaptation) and calls the batch;
  OFF → the existing graph path (create tasks → `run_cognitive_tasks` →
  `run_rules` → prune) runs UNCHANGED as the correctness oracle. Pure mechanical
  I/O + one batch call; makes no decision.
- **Falsifier hook** `context['retina_accel_perturb']` injects a WRONG mirror
  (a +1000 dB offset that fires every cell), so the byte-identity check is
  provably non-vacuous.

## C1 — BYTE-IDENTITY (the primary gate) — PASS

Full carve protocol, accelerator ON vs OFF (OFF = the 183000 pruned graph path),
at every resolution incl. the firing 19200 carve:

| grid | cells | polygons | onset stream | union_iou / precision | rod adaptation | identical |
|---|---|---|---|---|---|---|
| 20×15   | 300   | 0 == 0 | ✅ (1 event)   | ✅ 0.0 / 0.0       | ✅ | ✅ |
| 40×30   | 1200  | 1 == 1 | ✅ (6 events)  | ✅ 0.0896 / 1.0    | ✅ | ✅ |
| 80×60   | 4800  | 0 == 0 | ✅ (45 events) | ✅ 0.0 / 0.0       | ✅ | ✅ |
| 160×120 | 19200 | 5 == 5 | ✅ (357 events)| ✅ 0.0384 / 0.9348 | ✅ | ✅ |

ON≡OFF on VisionPolygons AND the onset-event stream AND union_iou/precision AND
the full-precision per-cell rod `adaptation` vector (the state that persists
across ticks) — at every grid, on the firing 19200 carve included.

**C1e — the landed 160×120 Doom carve reproduced EXACTLY under the accelerator.**
The landed value was produced by the 182000 carve protocol at seed 182000 (the
183000 landed check used that seed); re-running that protocol at seed 182000 with
the accelerator ON gives **4 VisionPolygons, union_iou 0.1215, precision 0.9784,
false_poly_rate 0.0** — identical to the landed 182000/183000 headline, and
ON≡OFF (onset stream + polygons + rod adaptation all match the graph path at that
seed). The mirror reproduces the real firing carve exactly.

## C2 — DROPPABLE (ON ≡ OFF) — PASS

The OFF arm above IS the graph/`run_rules` path (the correctness oracle); turning
the accelerator off falls back to it and yields IDENTICAL results (the entire C1
table). The accelerator mints NO per-cell CognitiveTask nodes (both arms end with
exactly the single carve task, `tasks_left = 1`).

## C3 — CELLS AXIS LINEARIZED + speedup — PASS

Median steady-state per-tick vs cells (3 trials; SOLO), accelerator ON vs the
183000 pruned graph path:

| cells (grid) | graph / OFF (ms) | accel / ON (ms) | speedup | accel fps |
|---|---|---|---|---|
| 300   (20×15)   | 5.62     | 0.37  | 15×   | 2675 |
| 1200  (40×30)   | 46.90    | 1.57  | 30×   | 637  |
| 4800  (80×60)   | 726.13   | 6.64  | **109×** | 151  |
| 19200 (160×120) | 10999.99 | 32.82 | **335×** | **30.5** |

- Fitted log-log exponent (per-tick vs cells): **graph 1.838** (reproduces the
  183000 pruned 1.83 — the OFF arm IS that path), **accel 1.072**. Exponent DROP
  **0.765 ≥ 0.4** ✅; accel exponent **1.072 ≤ 1.3** ✅.
- Speedup at 4800 cells: **109× ≥ 5×** ✅.
- **C3d — resolution / fps reached, reported as FACTS.** The accelerated
  transduce+onset sheet runs at **30.5 fps @ 160×120 (19200 cells)** — this IS
  real-time at full fixture resolution for the per-cell sheet (the O(cells²)
  bottleneck this rung targeted). HONEST SCOPE: this is the per-tick
  transduce+onset cost; the common-fate CARVE settle is a SEPARATE per-motion-
  window op (one task), not per-tick, and is unchanged here. The residual per-tick
  cost is now an O(cells) FLOOR (the batch touches every cell every tick).

## C4 — FALSIFIER for the byte-identity check (non-vacuity) — PASS

A deliberately-perturbed kernel (`retina_accel_perturb`, +1000 dB) at 40×30:
onset stream **15600 events** (every cell fires every frame) vs the graph path's
**6** → the ON≡OFF match BREAKS. The C1 identity check can detect a wrong mirror;
the correct mirror at the same grid does NOT diverge (gate guard).

## Per-criterion table

| id | criterion | measured | pass |
|---|---|---|---|
| C1a–d | ON≡OFF: polygons + onset stream + iou/precision + rod adaptation, 300/1200/4800/19200 | identical (all) | ✅ |
| C1e | landed 160×120 carve reproduced under accel (seed 182000) | 4 / 0.1215 / 0.9784 / 0 false, ==off, ==landed | ✅ |
| C2 | droppable: OFF = graph oracle, ON≡OFF | identical (C1) | ✅ |
| C3a | accel cells exponent ≤ 1.3 | 1.072 | ✅ |
| C3b | exponent drop ≥ 0.4 | 0.765 | ✅ |
| C3c | speedup @4800 ≥ 5× | 109× | ✅ |
| C3d | fps reached (fact) | 30.5 fps @ 19200 (real-time, sheet) | fact |
| C4 | perturbed kernel breaks ON≡OFF | 15600 ≠ 6 | ✅ |

## Provenance & discipline

- **Oracle** `bash scripts/rung7_vision_bench.sh` — see the report; run with the
  accelerator OFF by default (the whole bench uses the graph path, byte-unchanged)
  and ON≡OFF confirmed on the eye path by the C1 table + the gate.
- **Gate** `tests/test_eye_accel_migrated.py`: **5 passed** — (a) ON≡OFF
  byte-identity @300/1200/4800 (polygons+onset+iou+precision+rod adaptation), (b)
  perturbed-kernel falsifier (+ correct-mirror guard), (c) cells-axis
  exponent/speedup at the mechanism grain.
- Rust built in this worktree ONLY; canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df`
  UNCHANGED. **CANONICAL NEEDS REBUILD ON MERGE.**
- `source_match = own`. NO new Term enum variant — a new batch graph op
  (`retina_onset_batch`) + PyO3 entrypoint. NO new seed.
- Curves + fps: `results/eye_accel/scaling.png`, `results/eye_accel.json`.

## Honest residuals

- **Real-time is delivered for the per-cell SHEET (30.6 fps @ 19200), not the
  whole eye.** The common-fate carve/motion/salience SETTLE ops (one task each,
  per motion window) are unchanged; a full "see + carve + name" loop at video rate
  is not claimed. What this rung claims and measures is the sheet: the O(cells²)
  per-tick transduce+onset is now O(cells) and real-time at full fixture res.
- **The per-tick is now an O(cells) FLOOR, not sub-linear.** The batch touches
  every cell every tick (SIMD over a uniform sheet). The named NEXT lever beyond
  SIMD is the **per-area DIRTY-INDEX** — process only CHANGED cells = O(surprise),
  not O(cells). On this adapted-background scene most cells are silent every tick,
  so a dirty-index would drop the floor by a large constant (potentially another
  order of magnitude); it is a SEPARATE rung, still on the table.
- **The accel path skips the transient CognitiveTask/TaskResult scaffolding**
  (removed by the 183000 prune in the graph path anyway) and the per-area
  `AreaLoad` publish — none are observable in the carve/onset outputs (verified by
  the full C1 byte-identity incl. rod adaptation). It also does not set the
  unobservable per-cell `input_epoch` on the RetinalColumn (no rule reads it; the
  onset refractory reads the rod's).
- **`magnitude_db` on minted events is bit-identical** (the kernel is reused
  verbatim); the carve reads only `(column_index,row_index,epoch)`, so it is
  carried for completeness, not correctness.

## Proposed VISION_PROTOCOL ledger row

`184000 | THE ACCELERATION: droppable byte-identical vectorized mirror of the 2-D retina sheet (Rust retina_onset_batch + PyO3, adapter flag retina_accel) | 183000 left the CELLS axis at exp 1.83 / 0.73s@4800 — the onset-mint run_rules join is O(cells²) over a sheet of identical microcircuits; batch the whole sheet in ONE O(cells) FFI pass, reusing the photon_transduce_onset kernel VERBATIM + mirroring apply+onset rules, no CognitiveTask nodes / no run_rules join | byte-identical ON≡OFF (polygons+onset+iou+precision+rod adaptation @300/1200/4800/19200; landed 160×120 carve reproduced EXACTLY 4/0.1215/0.9784/0 at seed 182000); droppable (OFF=graph oracle); cells exp 1.838→1.072 (drop 0.765), speedup 109× @4800 / 335× @19200; 30.5 fps @160×120 REAL-TIME for the sheet; perturbed-kernel falsifier breaks ON≡OFF (15600≠6) | Rust built (canonical .so md5 417f66… UNCHANGED, REBUILD ON MERGE); NO new Term enum (batch graph op + PyO3 only); gate test_eye_accel_migrated 5/5; oracle rung7 0 failed ON-default + ON≡OFF; source_match own | real-time is the per-cell SHEET not the whole eye (carve settle unchanged); per-tick is an O(cells) FLOOR — next lever is the per-area DIRTY-INDEX (O(surprise), separate rung)`
