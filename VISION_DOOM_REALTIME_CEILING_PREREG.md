# PREREG — the Doom real-time rung (seed block 201000-201999)

**Base commit:** `0f2eb74a41` (LEDGER 200000 — held-prediction/decay/demotion on
the real Doom eye). Isolated worktree.
**Canonical engine `.so` md5:** `793ce09ed498a749abb79aeaea44b92e`
(`runners/dsl/python/substrate_rs/_native.abi3.so`). This rung is PURE MEASUREMENT
+ DESIGN/SIMULATION — **no Rust, no Term, no seed edit, no eye code change** — so
`term.rs` diff is EMPTY and the `.so` md5 is byte-identical BEFORE==AFTER by
construction. Byte-identity is therefore trivial (nothing is touched).

**Seed claim (verbatim `check_claim`, run at prereg time):**

```
SEED CLAIM 201000-201999: CLEAN -- no collision DETECTED.
  Scope: 901 files with seed sinks; 612 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Seed used by the runner: **201000** (fixed, reproducible; the single measured draw).

---

## THE QUESTION

What uniform receptor budget does the real Doom eye afford at real-time, and what
layout recovers the most scene within it?

- **PART A (primary, gate-able):** the post-195000 uniform real-time CEILING on the
  shipped photon eye — end-to-end ms/frame vs uniform receptor (cell) count, and the
  cell count that fits the **28.5 ms (35 fps)** and **33 ms (30 fps)** Doom budgets.
- **PART B (secondary, build-or-spec):** the foveated / log-polar layout sized to
  the Part-A budget.

## THE INSTRUMENT (Part A) — the SHIPPED photon-eye per-frame loop

The measured object is the shipped eye's `_tick` (byte-for-byte the loop in
`scripts/doom_carve_scale_measure.py::_tick`, which is the 182000 carve-scale
harness over the 181000 photon eye, 191000 event path, 195000-linearised,
184000-accelerator available):

```
eye.submit_photons_2d(dpw.photon_packets(luma, rng))   # transduce ingest
eye.substrate._inner.run_cognitive_tasks(1)            # onset transduce tasks
eye.substrate._inner.run_rules()                       # the fixpoint (was O(cells^2) pre-195000)
eye.prune_settled_tasks()                              # settled-task housekeeping
```

Eye built via `doom_carve_scale_measure.build_eye(n_el, n_az)` — the shipped
defaults (`retina_2d`, `synchronous`, `onset_threshold_db=6`, `visual_carve`,
`carve_min_coherence=0.5`, `carve_min_events=2.5`), **accelerator OFF** (the
graph path is the correctness oracle AND the path where the 195000 run_rules
linearisation lives). Feed = **real VizDoom frames** (`defend_the_line`, still
camera + laterally-moving monsters — the same differential-motion regime the
182000/eye-on-Doom lineage uses; captured once via
`doom_carve_scale_measure.capture`). E1M1 (`capture_e1m1`) reported as a
cross-content check if it captures cleanly.

**MEASUREMENT (Part A):**

1. Capture N real motion frames once (fixed seed 201000).
2. Sweep uniform grids over the prompt's range: `n_az x n_el` in
   `[(20,15),(28,21),(40,30),(56,42),(80,60),(113,85),(160,120)]`
   = cells **300 → 19,200** (160×120), a 64× span, geometric.
3. Per grid: warmup W ticks (background adaptation), then time the **steady-state
   per-tick end-to-end ms** over a real-motion stream (cycled), **median over ≥5
   solo reps**, report the spread (min/max, IQR). SOLO, machine otherwise idle.
4. Cross-check: with `scale_audit` ON, record the deterministic WORK-COUNT
   (`cand_enum`, `term_evals_total`) per tick at each grid.
5. Decompose the wall into `submit_photons_2d` (Python transduce ingest, O(cells))
   vs `run_cognitive_tasks+run_rules` (the fixpoint) so the dominant component is
   visible.
6. Fit log-log exponents for wall-ms, cand_enum, term_evals vs cells.

**Liveness gate (lesson: a dead tick is infinitely fast):** at every grid,
`cand_enum > 0` and onsets fire on the motion stream (non-frozen). A grid whose
instrument reads zero work is discarded, not reported as "fast".

**SECONDARY (held-scene uplift):** the eye's `dirty` change-report path
(`submit_photons_2d(..., dirty=...)`, block 185000) + adaptation make a STABLE
scene cheaper (compute ∝ surprise). Measure the per-tick cost of a HELD (static,
adapted) frame stream vs the every-frame-changing stream at the same grid, and
report the ratio as the held-scene uplift on the ceiling. The every-frame
uniform ceiling (Part A primary) is the CONSERVATIVE number; the held uplift is
reported as a secondary, not the headline.

## GATES (pre-registered BEFORE any number)

- **G1 — LINEARITY AT SCALE (the real gate):** across cells 300→19,200, both the
  wall-clock ms/frame AND the work-count (`cand_enum`, `term_evals_total`) scale
  ~LINEARLY, **log-log exponent ≤ ~1.3**, confirming 195000's scheduler
  linearisation holds at the scales that matter (pre-195000 run_rules was ~2.0).
  If the counter exponent is ~1 but wall is superlinear, that is an incomplete
  counter / a residual Python-side quadratic — reported straight, not hidden.
  If run_rules itself is superlinear, that is a FINDING (residual quadratic) —
  reported straight.
- **G2 — THE CEILING:** the uniform cell count at **28.5 ms** and **33 ms**,
  median + spread over ≥5 solo reps, with history context (vs ~700 receptors
  @30 fps pre-195000). Reported for the graph path (primary) and, as a secondary,
  the 184000-accelerator path.
- **G3 — THE FOVEATED LAYOUT:** FIRST report honestly whether the eye admits
  non-uniform receptor layouts. **Predicted answer from source read: NO** — the
  2-D retina is built as a strictly uniform `az×el` grid (`photon_eye.py` nested
  `for row in range(n_el): for col in range(n_az)`, evenly-spaced az/el, no
  per-receptor position table, no log-polar), and `submit_photons_2d` indexes
  cells by `flat = row*n_az + col` with a uniform-grid bounds check. So Part B is
  **SPEC + SIMULATE**: a compute-model of a foveated layout (dense 1:1 foveal
  patch matching Doom's pixel grid + log-polar periphery ~1/eccentricity) sized to
  the Part-A budget — foveal patch size + ring schedule + total receptors + the
  scene-coverage it recovers vs a uniform grid of the same receptor count — and a
  HONEST naming of the exact eye change a live build needs (a per-receptor
  position/az-el table replacing the uniform nested loop, and a matching
  `submit_photons_2d` scatter). NOT a faked live foveated eye.
- **G4 — byte-identity / default-OFF:** PURE MEASUREMENT + SPEC, no eye code
  change, `term.rs` empty, `.so` md5 `793ce09e…` untouched BEFORE==AFTER. Stated,
  trivially holds.

## PREDICTED CEILING RANGE (pre-registered, honest)

From the 2-point pilot (random-luma worst case: 300 cells → 5.6 ms, 1200 cells →
20.3 ms on the graph path; `cand_enum`/`term_evals` scaled exactly ×4.0 for ×4
cells): the graph-path every-frame ceiling is predicted at roughly **1,300–1,900
uniform cells @ 28.5 ms** and **1,600–2,300 @ 33 ms** — i.e. **~2–3× the ~700
pre-195000 figure**, dominated by the O(cells) Python transduce ingest as much as
the (now-linear) run_rules. Prediction stated so the measurement can falsify it.
The real-content ceiling may be HIGHER than the random-luma pilot (adapted
background → fewer onsets). If the ceiling lands materially below ~700, or the
exponent is superlinear, that is the finding and it is reported straight.

## DISCIPLINE

- Measure module IMPORT-INERT (scoped; timing in a context the import does not
  trigger). Solo, median over ≥5 reps, spread reported (lessons 7/11/149).
- No agent decisions in Python — the runner is a mechanical measure-adapter over
  the shipped eye (CLAUDE.md).
- Oracle `bash scripts/rung7_vision_bench.sh` BEFORE==AFTER, run ONCE after the
  timing pass (so it does not contend). Engine/eye suite green. `source_match`.
- No merge to main; VISION_PROTOCOL.md untouched.
