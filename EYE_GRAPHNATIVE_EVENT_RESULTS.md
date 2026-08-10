# EYE GRAPH-NATIVE EVENT PATH — RESULTS (seed block 191000–191999)

Prereg: `EYE_GRAPHNATIVE_EVENT_PREREG.md` (committed alone, `0d371e3536`, before
any number). `check_claim(191000,191999)` CLEAN (verbatim in the prereg commit).

## TL;DR — the fix is correct and byte-identical; the headline premise does NOT reproduce

- **The fix works and is byte-identical.** The six carve/motion/salience settle
  methods no longer marshal `RetinalOnsetEvent`s out of the graph one node at a
  time in Python. One in-Rust op (`retina_event_task_batch`) sweeps the event
  stream, builds the `CognitiveTask` payload + node in Rust, mints the retina
  edge. Outputs are float-exact identical to the old Python loop (kept as the
  `event_native=False` oracle) — synthetic 20×15 / 40×30 / 80×60, a real-Doom
  carve crop, AND the **landed full-res 160×120 carve: 4 polys / union_iou
  0.1215 / precision 0.9784 / 0 false, reproduced byte-identically on BOTH
  paths.** A wrong-read `perturb` falsifier breaks the digest (non-vacuous).
- **The event-path exponent drops** as designed: settle-stage cost exponent (ms
  vs receptors) **1.17 → 0.86**, and settle is **14–47× cheaper** in absolute
  terms.
- **BUT the marshalling was never the dominant cost, measured cleanly.** With the
  184000 receptor sheet accelerated (the shipped config) and the graph in
  steady state, the eye's per-frame cost is dominated by **`run_rules()`, which
  is O(cells²)** — the end-to-end frame exponent is **~1.95 on BOTH the old and
  new event path**, and at 160×120 `run_rules` is **99.8% of the frame** while
  the settle marshalling is **0.14%**. **The orphaned 190000 claim ("99.7% of
  the frame is Python event marshalling", "526 receptors @30 fps") does NOT
  reproduce** — the ceiling is set by `run_rules`, not by the marshalling. This
  is the pre-registered NEGATIVE + re-point outcome, and it is the most valuable
  output of the rung.

## The fix (what changed)

- **Rust — `runners/dsl/src/cognitive_tasks.rs::retina_event_task_batch`** (new;
  the event-consumer analogue of 184000's `retina_onset_batch`). One
  `nodes_of_type("RetinalOnsetEvent")` sweep reads `(column_index, [row_index,]
  epoch)` off the graph, filters by the host `since_epoch` window, sorts by the
  SAME deterministic key the Python used, packs the payload, and mints the
  `CognitiveTask` node + retina edge — replicating byte-for-byte the node the
  Python `add_node` built (`Str`/`Int`/`Float`/`Tuple`, verified against
  `py_to_value`). `perturb` injects `col+1000` (the falsifier).
- **Rust — `runners/dsl/src/py.rs`** exposes it as one PyO3 entrypoint. **NO new
  Term enum variant; `term.rs` diff is EMPTY.**
- **Python — `domains/photon_eye.py`**: the six `settle_*` methods lost their
  `for node in self.substrate.nodes("RetinalOnsetEvent")` loops and now call a
  shared `_settle_event_task` helper. Default `event_native=True` (shipped) calls
  the Rust op; `event_native=False` runs the old Python loop, retained as the
  byte-identity oracle (the ONE remaining event-node loop in the file). The
  `run_rules` mint rules + kernels are UNCHANGED.

Six call sites removed (old line numbers): `settle_carve_2d` ~614,
`settle_motion_2d` ~691, `settle_salience_2d` ~760, `settle_motion` ~911,
`settle_carve` ~977, `settle_salience` ~1054.

## Measurements (SOLO, median of steady-state frames; `results/eye_graphnative_event/curves.json`)

Shipped config: `retina_accel=True` (receptor sheet O(cells) on BOTH arms) +
carve+motion+salience on. The ONLY difference between arms is the event path.
Scene: full-field moving random texture (events scale with cells). Per-frame ms:

| grid | cells | ev/frame | submit | **settle (native)** | **settle (oracle)** | kernel = run_cog+run_rules | FRAME (native) | FRAME (oracle) |
|---|---|---|---|---|---|---|---|---|
| 20×15   | 300   | 30   | 0.30 | **0.016** | **0.232** | 6.1     | 6.45     | 7.12 |
| 40×30   | 1200  | 163  | 1.38 | **0.037** | **0.854** | 88      | 89.5     | 91.2 |
| 80×60   | 4800  | 686  | 5.9  | **0.082** | **3.561** | 1444    | 1451     | 1427 |
| 160×120 | 19200 | 7016 | 26   | **0.668** | **31.43** | 22941   | 22979    | 22907 |

**Exponents (log-log slope of ms vs cells):**

| stage | oracle (old Python loop) | native (graph-native fix) |
|---|---|---|
| settle (the EVENT PATH — what this rung fixes) | **1.17** | **0.86** |
| frame (end-to-end) | 1.95 | 1.97 |

**Max receptors at the real-time budget (from the frame curve):**

| | @30 fps | @60 fps |
|---|---|---|
| oracle (= current-main event behavior, RE-MEASURED) | 686 | 480 |
| native (191000) | 705 | 496 |

The ceiling moves **+2.8% @30 fps / +3.3% @60 fps** — negligible, because
`run_rules` dominates. (The @60 fps figures bracket the orphaned 190000 "526"
number; that ballpark is real, but its *cause* was misattributed to the
marshalling.)

## Per-stage split of the "kernel" column (isolation)

Splitting `run_cognitive_tasks(1)` from `run_rules()` shows the quadratic lives
entirely in `run_rules`, and it is intrinsic (present even carve-only):

| grid | run_cognitive_tasks | run_rules (carve-only) | run_rules (all 3) |
|---|---|---|---|
| 40×30 | ~0.35 ms | 32.4 ms | 87.2 ms |
| 80×60 | ~1.1 ms  | 530.6 ms | 1441.6 ms |

`run_rules` scales 32→531 (carve-only) and 87→1442 (all 3) for a 4× cell
increase — **exponent ≈ 2.0**. **This is the new dominant cost.** It is the
known engine debt (the un-indexed `run_rules` fixpoint / per-area matcher), not
the event path, and it is out of scope for this rung.

## Byte-identity (primary gate)

- `tests/test_eye_graphnative_event_migrated.py` **7/7**: float-exact
  native==oracle for VisionPolygons + RetinalMotionPercepts + RetinalSalience at
  20×15/40×30/80×60; real-Doom carve crop identical and firing; `perturb`
  breaks the digest; graph-native settle ≥3× cheaper (measured ~40×); source
  audit (exactly one remaining Python event-node loop — the oracle).
- Full-res **160×120 landed carve** (`results/eye_graphnative_event/landed_carve_identity.json`):
  native = oracle = **4 polys / union_iou 0.1215 / precision 0.9784 / 0 false**,
  `byte_identical=True`.

## Oracle + regression (BEFORE == AFTER)

- **`rung7_vision_bench.sh`**: worktree = **214 passed / 10 skipped / 0 failed**
  (matches the worktree-without-`data/` baseline; main is 224/0). No regression.
- **`per_area_settlement_regression.sh` (34 files)**: **identical failing-id set
  BEFORE (base `photon_eye`) and AFTER — 23 nodes, byte-for-byte the same set**
  (`diff` empty). Every failure is a pre-existing flaky conversation/cognitive
  test (`composer_driver` 1, `cortices_tick` 3, `elaboration` 5, `gap_awareness`
  5, `topic_route_selfheal` 9) — **ZERO eye/vision/carve/motion/salience/onset/
  retina/2d/accel/dirty failures**. (A first pass exposed a real bug — the new
  flag was set only on the 2-D construction branch, `AttributeError` on 1-D
  eyes; fixed by moving it before the 1-D/2-D branch; the 64-file eye suite is
  green.)

## Provenance / build safety

- `source_match = own`. `term.rs` diff EMPTY (no new Term variant).
- Canonical `.so` md5 `9b6a0bf36181649e6934ae22307fa7ad` verified UNCHANGED
  before/after every `cp` and at commit; worktree `.so` a real file, built ONLY
  in this worktree (`runners/dsl/target/release/libsubstrate_rs.so` →
  `_native.abi3.so`, worktree md5 `8c88057080b17e1b58a590a911355cee`).
- **CANONICAL NEEDS A REBUILD ON MERGE** (the fix adds a Rust op; the canonical
  `.so` does not contain `retina_event_task_batch`).

## Honest residuals

- **End-to-end fps barely moves.** The correct read is: the marshalling fix is a
  real, byte-identical efficiency win on the settle stage (14–47×, exponent
  1.17→0.86), but it recovers <1% of the frame because `run_rules` (O(cells²))
  dwarfs it. The eye's real-time ceiling is a `run_rules` problem.
- **The steady-state regime is the fair one.** With per-frame pruning the old
  marshalling is ~linear per frame (exponent ~1.17), not the ~1.85 the orphaned
  doc implied. The ">quadratic marshalling" reading only arises if onset events
  are allowed to ACCUMULATE unpruned across frames (settle then marshals
  O(frames×cells)); the fix helps there too, but that is not the shipped tick.
- **Synthetic scene carves 0 polygons** (random texture is incoherent — correct
  refusal); byte-identity there is carried by the salience stream (172/715
  identical nodes) and the motion stream, plus the real-Doom carve fixtures.
- The `run_rules` O(cells²) is named, not fixed — a separate rung (the engine's
  per-area matcher index).

## Proposed VISION_PROTOCOL ledger row

> **191000–191999 (`check_claim` CLEAN; SEPARATE prereg commit BEFORE build)** —
> **FIX THE EYE'S EVENT PATH TO BE GRAPH-NATIVE (the onset stream never leaves
> Rust) — DONE, byte-identical; the 190000 "99.7% marshalling / 526@30fps"
> premise DOES NOT REPRODUCE.** One in-Rust op (`retina_event_task_batch`, the
> event-consumer twin of 184000's `retina_onset_batch`) replaces six Python
> per-event `nodes("RetinalOnsetEvent")` marshalling loops; run_rules mint rules
> + kernels unchanged; **NO new Term variant, `term.rs` EMPTY.** **Byte-identical
> VisionPolygon/RetinalMotionPercept/RetinalSalience** (synthetic 20×15/40×30/
> 80×60 + real-Doom crop + **landed 160×120 carve 4 polys / IoU 0.1215 / prec
> 0.9784 / 0 false, native==oracle**); `perturb` falsifier bites. **Settle
> exponent 1.17→0.86, settle 14–47× cheaper.** **NEW DOMINANT COST NAMED:
> `run_rules` is O(cells²) (frame exponent ~1.95 both arms; 99.8% of the frame
> at 160×120); max receptors 686→705 @30fps / 480→496 @60fps — the marshalling
> was <1% of the frame.** Gate `test_eye_graphnative_event_migrated` **7/7**;
> oracle `rung7_vision_bench` 214/10/0 worktree (BEFORE==AFTER); 34-file
> regression **identical 23-node failing set** (pre-existing flaky conversation,
> zero eye/vision); §10 `source_match=own`; canonical `.so`
> `9b6a0bf3…` UNCHANGED — **CANONICAL NEEDS REBUILD ON MERGE.**
