# EYE GRAPH-NATIVE EVENT PATH — PRE-REGISTRATION (seed block 191000–191999)

## The defect (already located; this rung verifies + fixes it)

The photon eye's receptor sheet was made O(cells) graph-native in block 184000
(`retina_onset_batch`). The **event-consumer path was never fixed.** In
`domains/photon_eye.py` the six settle methods —

- `settle_carve_2d`   (~line 614)  → `retinal_common_fate_carve_2d`
- `settle_motion_2d`  (~line 691)  → `retinal_event_motion_2d`
- `settle_salience_2d` (~line 760) → `retinal_residual_salience_2d`
- `settle_motion`     (~line 911)  → `retinal_event_motion`
- `settle_carve`      (~line 977)  → `retinal_common_fate_carve`
- `settle_salience`   (~line 1054) → `retinal_residual_salience`

each do `for node in self.substrate.nodes("RetinalOnsetEvent"):` and, per event,
cross the PyO3 boundary with `self.substrate.node(node)["attrs"]` to read
`(column_index, [row_index,] epoch)`, building a Python list. That list is then
serialised into a `CognitiveTask.payload` and consumed by a Rust kernel via
`run_rules`. **The onset events are minted by a Rust rule and consumed by Rust
kernels — they should never round-trip through Python.** The per-EVENT Python
marshalling is O(events), repeated for carve AND motion AND salience each frame,
and events ∝ cells, so the event path is ~quadratic in receptors. The end-to-end
integration finding (orphaned block 190000, RE-MEASURED here — not trusted)
reported the eye real-time only at ~526 receptors @30 fps, with ~99.7% of the
frame in this Python event serialisation.

## The fix (graph-native, "the architecture rule properly")

Add ONE in-Rust batched read of the `RetinalOnsetEvent` stream, exposed as a
single PyO3 entrypoint (`retina_event_task_batch`), that sweeps the event nodes
with a single in-Rust `nodes_of_type` pass, reads `(column_index, row_index,
epoch)` directly off the graph, filters by the host observation window
(`since_epoch`), sorts by the SAME deterministic key the Python used, builds the
`CognitiveTask.payload`, and mints the `CognitiveTask` node + its retina edge —
all in Rust, replicating byte-for-byte the node the Python path built (same
attr Value types: `Str`/`Int`/`Float`/`Tuple`, verified against `py_to_value`).
The existing `run_rules` mint rules + kernels are UNCHANGED. The Python settle
methods stop touching individual event nodes: they call the one batched op and
read back the minted `VisionPolygon` / `RetinalMotionPercept` / `RetinalSalience`
results (a small, O(results) read — legitimate emit). **NO new Term enum
variant** — a new PyO3 entrypoint + graph op only. The old Python loop is kept,
reachable via `event_native=False`, as the byte-identity ORACLE.

This is the exact analogue of 184000's `retina_onset_batch` for the event
consumers.

## Headline (falsifiable)

1. **BYTE-IDENTICAL OUTPUTS (primary gate).** The graph-native path produces
   IDENTICAL `VisionPolygon`s, `RetinalMotionPercept`s and `RetinalSalience`s to
   the current Python-serialise path — proven with full float-exact digests AND
   the landed 160×120 Doom carve (**4 polys / IoU 0.1215 / precision 0.9784 / 0
   false**), at 20×15 / 80×60 / 160×120, and on a partially-changing scene. A
   `perturb` falsifier (a wrong in-Rust read) must break the digest — the check
   is non-vacuous.
2. **THE EVENT-PATH EXPONENT DROPS.** Fit event-path ms/frame vs receptors
   BEFORE (`event_native=False`, the current Python loop) and AFTER
   (`event_native=True`); BEFORE ≈ the ~1.85 the 190000 finding claims, AFTER ≈
   1. Report both, controlled on the same binary + machine.
3. **MAX RECEPTORS @30 fps / @60 fps, before vs after.** Reproduce the ~526 @30
   fps baseline myself on the current-main path (RE-MEASURED, not trusted from
   the orphaned doc), then report the new figure and state plainly how much it
   moved.

## Scope + honesty (binding)

- This is **SEEING, not PLAYING** — the act loop is out of scope. No "plays
  Doom" claim.
- The shipped sensor is **Poisson**; the DEFAULT/shipped config is the headline.
- **Name the NEW dominant cost.** After removing the marshalling, if the
  dominant cost has moved (into a Rust kernel that is itself O(cells²), into
  `run_rules` settle, into the receptor sheet, or into the one bulk result
  read), report a per-stage breakdown and say WHERE the time now is. Do not stop
  at "it got faster".
- **Allow the negative.** If the Python marshalling turns out NOT to be the
  dominant cost once measured cleanly (the 190000 doc was orphaned mid-write),
  report that plainly and re-point at the true dominant stage.

## Method

- **Harness** `scripts/eye_graphnative_event_measure.py` (mechanical measure
  adapter; no agent decision, no new seed). Synthetic laterally-moving-object
  scene at 20×15 / 80×60 / 160×120 (and a partial-change scene), plus the
  committed Doom carve fixture for the landed-carve identity. Drives warmup →
  motion → settle(carve+motion+salience) → `run_cognitive_tasks` → `run_rules` →
  readout. Per-stage wall-clock, multiple trials, median + spread, warm-up
  discarded.
- **Controlled before/after** on the same AFTER binary: `event_native=False`
  (old Python loop) vs `True` (Rust op), plus a sanity confirmation that
  `event_native=False` reproduces the base-commit binary's number.
- **Curves** under `results/eye_graphnative_event/`.

## Gates + discipline

- **Gate** `tests/test_eye_graphnative_event_migrated.py`: pins float-exact
  byte-identity (old-path vs new-path outputs, incl. the landed carve), the
  `perturb` non-vacuity falsifier, and a coarse cost-SHAPE claim at the
  mechanism grain (robust, not a fragile absolute-ms assertion).
- **Oracle** `bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE == AFTER.
- **Cross-domain regression** `scripts/per_area_settlement_regression.sh` (34
  files), failing-id SET compared BEFORE/AFTER — the engine's event consumers
  are changing.
- **Build safety (LESSON 9b).** Canonical `.so` md5 `9b6a0bf36181649e6934ae22307fa7ad`
  verified before the first `cp`, after every `cp`, at final commit; worktree
  `.so` verified a REAL FILE each time. Build ONLY in this worktree. `term.rs`
  diff MUST be empty (no new Term enum variant). CANONICAL NEEDS REBUILD ON
  MERGE — flagged loudly.
- **Provenance §10:** `source_match in ("own","shared")`.

## Pre-registered decision gates

- **ADOPT** iff: byte-identity holds at all three resolutions + partial-change +
  landed carve; perturb falsifier bites; event-path exponent drops materially
  (AFTER meaningfully below BEFORE); oracle 0-failed both sides; regression
  failing-id set unchanged.
- **NARROW** (ship the 2-D path only, the Doom-relevant one) if a 1-D path shows
  any digest mismatch I cannot resolve.
- **ABANDON / RE-POINT** if byte-identity cannot be achieved, OR if the clean
  measurement shows the Python marshalling was NOT the dominant cost — in which
  case the deliverable is the corrected per-stage attribution.

Seed block: **191000–191999**. `python3 scripts/seed_claim.py 191000 191999` →
CLEAN (verbatim in the commit message).
