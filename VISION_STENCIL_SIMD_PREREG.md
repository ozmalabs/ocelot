# RUST-VECTORIZED STENCIL AS THE ENGINE'S ADMISSIBLE FAST PATH — PRE-REGISTRATION

*Block 134000–134999. Committed BEFORE any measurement number (PROTOCOL §3).
Cashes in the SCALE lever named by 133000 (`VISION_NET_FIELD_PROPOSAL_RESULTS.md`
§4): for a KNOWN local rule the scale lever is EXACT VECTORIZATION of the rule
the substrate already holds — byte-identical, ~500× the numpy-exact reference vs
the engine — NOT a net. This rung builds that vectorization IN RUST as an
engine fast path, gated by Γ-admissibility.*

## clause-8 — the seed claim (verbatim `python3 scripts/seed_claim.py 134000 134999`)

```
SEED CLAIM 134000-134999: CLEAN -- no collision DETECTED.
  Scope: 842 files with seed sinks; 563 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unknown_sinks (unresolved sink sites tree-wide): **563**.

## 0. Provenance (before)

- branch `worktree-agent-a51e398c730c74c47` (NOT main); base HEAD `12d6b4cba33d`.
- engine BEFORE: `shared` `7c2aaa41748f` @ this worktree's
  `runners/dsl/python/substrate_rs/_native.abi3.so` (built `scripts/engine_build.sh`,
  unchanged source ⇒ byte-identical to canonical).
- oracle BEFORE: **222 passed, 0 failed** (`rung7_vision_bench.sh`,
  `var/oracle_before_134000.log`, `data/` symlinked).
- After the Rust change I REBUILD (`scripts/engine_build.sh` ⇒ `own`), re-run
  the oracle (AFTER), and print `provenance_line()` from inside the measuring
  process asserting `source_match in {own, shared}`.

## 1. The target (measured byte-identical by 133000's control)

The RetinaCell STATE field is a radius-1 deterministic CA (`wv_propagate` /
`wv_refract` / `wv_recover` + exogenous ignition applied by the adapter, not the
tick). `scripts/_scratch_ca_verify.py` proved a numpy reimplementation
byte-identical to `s.tick()` across 9 configs × 60 steps. A fresh mutation probe
(`scripts/_scratch_tick_mutation_probe.py`) confirms a waves-only `s.tick()`
mutates ONLY `RetinaCell.state` (47 cells) and `RetinaCell.fired_at` (16 cells)
and NOTHING else in the graph — the state CA is the entire tick dynamics on a
pure wave field.

## 2. What I build

A Rust batched/vectorized application of the wave relaxation stencil, applied to
the WHOLE field in one pass over contiguous memory, replacing per-cell rule
matching in the collapse loop. Exposed as a `#[pymethods]` on the `Substrate`
pyclass (`wave_stencil_tick`) with a one-line adapter opt-in in
`domains/wave_world.py::step` (DEFAULT OFF — the committed `s.tick(200_000)` path
is UNCHANGED, PROTOCOL §9, the `detect_cycles`/`bulk_ingest` precedent).

**SPECIALIST GATED BY ADMISSIBILITY (Γ).** The fast path is admissible ONLY when
the RetinaCell dynamics are the canonical regular local stencil — verified by
STRUCTURALLY MATCHING the three rules' `where`/`effect` ASTs against the stencil
templates and reading their parameters (`refractory_steps`, `propagate`, the
`neighbour` edge type, the state literals) from the matched AST + the graph —
NOT by rule name and NOT a hardcode. When the rule set is NOT a recognized
uniform local stencil (e.g. the learner rules on Unit/Synapse — a Fold over
synapses + winner-take-all Argmax, not a stencil), the gate returns None and the
caller falls back to the general per-cell engine path. So it composes: any graph
presenting the recognized stencil signature gets the fast path; anything else is
untouched. The general per-cell path stays DEFAULT and byte-unchanged.

If a new DSL Term is required, index 181, `NUM_TERM_VARIANTS` 181→182,
`variant_table_covers_the_enum` kept green. (Expected: NO new Term — this is a
`#[pymethods]` fast primitive, the `set_attr_each`/`space_quantize` precedent.)

## 3. Hypotheses (two-sided)

- **H-identity:** the Rust-vectorized stencil path produces the substrate state
  BIT-FOR-BIT identical to the per-cell path — same full-graph digest, 0
  mismatched cells — on a battery of grids AND across many iterated ticks (the CA
  compounds; an error grows). Two-sided: it may diverge (a layout/ordering bug),
  which is a BUG, not a result — a speedup that changes any cell FALSIFIES the
  build.
- **H-scale:** the vectorized path is substantially faster than the per-cell
  engine relaxation and pushes the real-time ceiling substantially past 53²
  (132000's ceiling). Two-sided: it may be no faster or slower (Rust overhead,
  gather/scatter copies, the graph layout forcing per-cell access) — that is the
  DEGRADE/FALSIFY branch.
- **H-gate:** the admissibility gate routes a stencil rule set → fast and a
  non-stencil rule set → general, BOTH producing correct state.

## 4. Statistics (exact)

1. **Byte-identity (primary):** for each (grid G, seed S), run K iterated ticks
   through BOTH paths from the SAME initial field; assert per-tick and final
   `state_fingerprint()` (full graph) equal AND `mismatched_cells == 0` over
   `state` and `fired_at`. Statistic = total mismatched cells across all
   (G, S, tick); target **0**.
2. **Speedup:** median ms/tick (over T trials, warmup discarded) for FAST vs
   GENERAL at each grid; ratio `general/fast`; µs/cell each; compared against
   (a) the engine's 1.33 µs/cell (133000) and (b) the numpy-exact reference
   re-measured on THIS machine in the SAME sweep (the ~500× anchor).
3. **Exponent:** log-log OLS of median ms/tick vs cells, FAST and GENERAL.
4. **Real-time ceiling:** grid side at the 41.7 ms/frame (24 fps) budget, FAST
   and GENERAL, from the fitted law.

## 5. n, FIXED IN ADVANCE (power on already-burned seeds / deterministic)

- **Timing sweep:** grids {16, 24, 32, 48, 64, 96, 128}. T = 9 trials each for
  grids ≤ 48², 7 for ≥ 64², 3 warmup discarded before each. Deterministic
  (WaveWorld seed 0, ignition schedule fixed) — the trial variance is wall-clock
  jitter, reported as per-point CI95. Solitude proven by CI width (< a few % of
  median, vs the 1.66× contention swings prior rungs refused wall-clock over) and
  by recorded `os.getloadavg()` start/end. Machine ALONE; NO concurrent load.
- **Byte-identity battery:** grids {8, 12, 16, 24, 32}; block seeds
  **134000–134004** (5 wave fields, disclosed, in-block); K = 100 iterated ticks
  each (the CA compounds — a single-tick check is insufficient). Plus the
  non-stencil routing case (Units added) and the noise-arm (`propagate=0`) case.

## 6. Decision rule

- **CONFIRM:** byte-identical (0 mismatches, multi-tick) AND a large measured
  speedup (the number FALLS OUT — no pre-commit to 500×; reported vs the
  1.33 µs/cell engine baseline AND the numpy-exact reference), ceiling
  substantially past 53², oracle 222/0, gate routes stencil→fast /
  non-stencil→general both correct.
- **DEGRADE:** byte-identical and faster but well short of the numpy-exact
  reference — report the achieved speedup and what caps it (memory layout,
  gather/scatter copies, the graph representation forcing per-cell access).
- **FALSIFY (name the next lever):** the rule cannot be applied vectorized
  without breaking byte-identity, OR the engine's graph layout forces per-cell
  access so no contiguous SIMD pass is possible without a representational change
  — then name the layout change (a dense field-backing store for stencil-typed
  subgraphs). NO speedup ships that is not proven byte-identical over multi-tick.

A NULL for H-scale (no speedup) with H-identity holding is a DEGRADE reported as
such; a byte-identity failure is a BUG to fix or a FALSIFY, never shipped.

## 7. Prediction, stated in advance (PROTOCOL §3.7)

I predict **CONFIRM**. The state CA is a trivial 4-symbol radius-1 rule; a single
synchronous Rust pass over contiguous arrays with a per-changed-cell write-back
should be byte-identical (the numpy control already proved a single synchronous
pass equals the tick) and much faster than the per-cell binding enumeration
(133000: the engine relaxation is 1.33 µs/cell; `wv_propagate` alone enumerated
65,024 bindings to admit ~1,000 at 128²). **Provisos that would break the
prediction and what each would teach:** (a) if the GATHER/SCATTER through the
graph's assoc-list attrs (`Attrs` is a `Vec<(Sym,Value)>` linear scan) dominates,
the speedup caps well below numpy-exact ⇒ DEGRADE, and the lesson is that the
node-attr layout, not the compute, is the wall (the named dense-field-store
lever). (b) If running the NON-wave rules after the stencil (to stay safe by
construction) is not near-free, the speedup shrinks and the refinement is to
CERTIFY rest-quiescence structurally (no non-wave rule reads `state`/`fired_at`)
and skip them. (c) The absolute ms are governor/synthetic-frame specific
(powersave; synthetic ignition) — the governor-independent claims are the RATIO,
the exponent, and byte-identity.

## 8. Scope — what will NOT be shown

- The kernel implements the state-CA stencil FAMILY (the wave CA); a fully
  general stencil-AST→array compiler for ARBITRARY uniform local rules is the
  named next lever, not built here. The GATE is structural (AST-matched); the
  KERNEL is the recognized family's semantics.
- Single-thread; one grid family (square); CPU; governor powersave; synthetic
  ignition field. Multi-core over the field is orthogonal (131000/132000's named
  lever) and not built here.
- This rung speaks to SCALE for a KNOWN local rule, NOT to the representation
  frontier (130000) nor to UNKNOWN dynamics where no exact vectorization exists.
