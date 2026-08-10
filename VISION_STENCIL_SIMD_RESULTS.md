# RUST-VECTORIZED STENCIL AS THE ENGINE'S ADMISSIBLE FAST PATH — RESULTS

*Pre-registration: `VISION_STENCIL_SIMD_PREREG.md`, committed `8b27ced9ad`
BEFORE any number (§3). Block 134000–134999. Cashes the SCALE lever 133000
named (`VISION_NET_FIELD_PROPOSAL_RESULTS.md` §4: for a KNOWN local rule the
scale lever is EXACT VECTORIZATION of the rule the substrate already holds,
byte-identical, NOT a net).*

## VERDICT: **CONFIRM on the built lever** — a Rust-vectorized stencil, gated by Γ-admissibility, is BYTE-IDENTICAL over multi-tick and **×61–84 faster** than the per-cell engine relaxation, pushing the waves-only real-time ceiling **177² → 2082²** — **with a first-class DEGRADE vs the numpy-exact reference**: the graph's assoc-list node-attr layout forces a per-cell gather/scatter, so the pure-field specialist is ~2.6× SLOWER than byte-identical numpy-exact at 128² and the gap WIDENS with N. Named lever: a dense field-backing store for stencil-typed subgraphs.

The RetinaCell state field (a radius-1 deterministic CA — `wv_propagate` /
`wv_refract` / `wv_recover`) is now applied by a **Rust `#[pymethods]`
`wave_stencil_tick`** in ONE vectorized pass over the contiguous field, gated by
a STRUCTURAL admissibility check (the three rules' `where`/`effect` ASTs matched,
NOT by name), with the general per-cell path unchanged as the default (§9). Two
findings, both honest:

- **The vectorized stencil is a huge win, and byte-identical.** In BARE mode
  (`run_rest=False`, the pure wave field) it costs **0.016–0.023 µs/cell** vs the
  engine's **1.28–1.40 µs/cell** (re-earning 133000's 1.33) = **×61–84**,
  SUBLINEAR (exponent 0.921), byte-identical over 100-tick runs on grids
  {8..32} × 5 seeds × both modes (0 mismatched cells). Real-time ceiling
  **2082²** (4.34M cells @ 24 fps) vs the engine's 177² — and ×39/side past
  132000's assembled-eye 53².
- **The graph node-attr layout — NOT the compute — is the remaining wall.** The
  same byte-identical numpy-exact reference (pure dense-array compute, no graph
  I/O) is SUBLINEAR at exponent 0.48; BARE mode beats it at ≤32² (Rust has no
  Python/alloc overhead) but is **2.0–2.6× SLOWER at ≥64²** because BARE must
  GATHER each cell's `state`/`activated_at`/`fired_at` (a linear scan of every
  node's `Attrs` Vec) and SCATTER each changed cell (`set_attr` + index
  maintenance), which numpy's dense arrays never pay. **The gap WIDENS with N
  (bare 0.921 vs numpy 0.480), so at 256² the graph-layout tax dominates.** The
  named extension: a **dense field-backing store for stencil-typed subgraphs**,
  so the gather/scatter becomes a contiguous view (closing the ~2.6× to
  numpy-exact).
- **The SAFE default (`run_rest=True`) is only ×1.6–1.7** — because it still runs
  the engine's general dirty-scan over the ~20 INERT cognition rules the
  waves-only boot carries (they fire zero times but are re-scanned each tick).
  The ×84 win is specifically **skipping that inert general machinery for a pure
  stencil field**, which is only sound in BARE mode (the gate refuses BARE when
  learners are present).

## 0. Provenance / engine / oracle

| item | value |
|---|---|
| branch | `worktree-agent-a51e398c730c74c47` (NOT main); base HEAD `12d6b4cba33d`; prereg commit `8b27ced9ad` |
| engine | `own` **`d072fc1b212d`** @ this worktree's `runners/dsl/python/substrate_rs/_native.abi3.so` (built `scripts/engine_build.sh`) |
| Rust added | **`runners/dsl/src/wave_stencil.rs`** (the gate + kernel + orchestration) + one `#[pymethods]` `wave_stencil_tick` on the `Substrate` pyclass (`py.rs`) + `pub mod wave_stencil` (`lib.rs`) + a wrapper delegation (`__init__.py`). **NO new DSL Term; `NUM_TERM_VARIANTS` = 181 unchanged; variant-table invariant trivially preserved (no enum variant added).** |
| adapter | `domains/wave_world.py::step` — a NEW opt-in `stencil_fast` branch, **DEFAULT OFF** (the `detect_cycles`/`bulk_ingest` precedent; committed `tick` path byte-unchanged). |
| re-verify after run | `source_match = own` asserted IN-PROCESS at the START and END of the measure script (`provenance_stamp()`); `provenance_line()` printed from inside the measuring process |
| oracle BEFORE | **222 passed, 0 failed** (`rung7_vision_bench.sh`, `var/oracle_before_134000.log`, engine `7c2aaa41748f`, `data/` symlinked) |
| oracle AFTER | **222 passed, 0 failed** (`var/oracle_after_134000.log`, 209 s, engine `d072fc1b212d`) |
| byte-identity gate | `tests/test_stencil_simd_migrated.py` **19 passed** |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed** |
| `check_claim` | `SEED CLAIM 134000-134999: CLEAN -- no collision DETECTED.` — unresolved sinks **563**, verbatim in prereg clause-8 |
| block seeds | byte-identity battery **134000–134004** (5 wave fields); timing sweep deterministic (WaveWorld seed 0) |

## 1. Solitude & timing rigor — PROVEN by CI width (machine ALONE)

| item | value |
|---|---|
| machine | AMD Ryzen, 12 logical; governor **powersave** (depresses absolute ms; the RATIOS and exponents are governor-independent) |
| threads | single-thread throughout (Rust engine, numpy boolean ops, the measure loop) |
| loadavg (run 2, reported) | start **[1.35, 0.92, 0.49]** → end **[1.91, 1.19, 0.64]** — the rise is the single measuring thread itself (~1 busy core); no competing job launched |
| **solitude proof (per-point CI width)** | run 2: every per-point CI95 is **≤ 1.36 %** of its median (16²–128² GEN: 0.30 %–1.36 %) — one to two orders of magnitude below the 1.66× (66 %) contention swings prior rungs refused wall-clock over |
| replication | TWO independent runs; FAST-BARE ×61–84 (run 1) / ×61–84 (run 2); ceiling 2074² / 2082²; exponent 0.920 / 0.921 — reproduced. **Run 1 had ONE wide point (32² CI 4.72 %, a transient from ~7 stray Jul-20 poll-shells waking); run 2 tightened it to 1.18 %** — I report run 2 and flag the transient (§6). |

Stray processes: ~7 orphaned zsh poll-loops from a Jul-20 session (`bdd81d70`,
not mine) were sleeping at 0.0 % CPU. Per §11 I did not touch another session's
processes; solitude is instead PROVEN by the tight CIs and replication.

## 2. The target (measured byte-identical)

`scripts/_scratch_tick_mutation_probe.py` (this rung) confirms a waves-only
`s.tick()` mutates ONLY `RetinaCell.state` (47 cells) and `RetinaCell.fired_at`
(16 cells) — the state CA is the ENTIRE tick dynamics on a pure field. The kernel
reproduces the exact `ca_tick` the numpy control (`scripts/_scratch_ca_verify.py`,
byte-identical to `s.tick()` across 9 configs × 60 steps) proved: a single
synchronous pass, recover-before-propagate, writing `state` as the SAME interned
`Value::Str` and `fired_at` as the SAME `Value::Float(step)`.

## 3. BYTE-IDENTITY — 0 mismatches, multi-tick, both modes (§9, non-negotiable)

`state_digest` = a full-graph digest (every node's type + sorted attrs). FAST
(`wave_stencil_tick`) vs GENERAL (`tick`), from the SAME initial field:

| battery | grids | seeds | ticks | modes | mismatched cells |
|---|---|---|---|---|---|
| pure field | {8,12,16,24,32} | {134000–134004} | 100 iterated | BARE + REST | **0** |
| noise arm (`propagate=0`) | 16 | 134020 | 80 | BARE | **0** |
| composition (Units present) | 12 | 134030 | 40 | REST | **0** |

`tests/test_stencil_simd_migrated.py` **19 passed**: byte-identity per grid ×
100 ticks (both modes); noise arm; learner composition; the routing gate (below);
the §9 default (an un-opted world is byte-unchanged); and a source audit (the
adapter's only stencil line is `if flag and s.wave_stencil_tick(...)` — no
conditional over graph state; the DECISION is the Rust gate).

## 4. SCALE — the measured speedup (median ms/tick, run 2, machine ALONE)

| grid | cells | GEN ms (CI95) | µs/cell | **FAST-BARE ms** | µs/cell | **×GEN** | ×numpy | FAST-REST ms | ×GEN | NUMPY ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | 256 | 0.3591 (0.30 %) | 1.403 | **0.0059** | 0.0230 | **×61.0** | 0.40 | 0.2136 | ×1.7 | 0.01458 |
| 24 | 576 | 0.7744 (0.44 %) | 1.345 | **0.0118** | 0.0205 | **×65.6** | 0.68 | 0.4631 | ×1.7 | 0.01731 |
| 32 | 1024 | 1.3338 (1.18 %) | 1.303 | **0.0165** | 0.0161 | **×81.0** | 0.90 | 0.8079 | ×1.7 | 0.01837 |
| 48 | 2304 | 2.9455 (0.79 %) | 1.278 | **0.0361** | 0.0157 | **×81.6** | 1.47 | 1.8461 | ×1.6 | 0.02454 |
| 64 | 4096 | 5.3009 (0.87 %) | 1.294 | **0.0687** | 0.0168 | **×77.1** | 2.02 | 3.3104 | ×1.6 | 0.03403 |
| 96 | 9216 | 11.7901 (0.97 %) | 1.279 | **0.1429** | 0.0155 | **×82.5** | 1.98 | 7.5590 | ×1.6 | 0.07229 |
| 128 | 16384 | 22.5735 (1.36 %) | 1.378 | **0.2693** | 0.0164 | **×83.8** | 2.62 | 14.4794 | ×1.6 | 0.10281 |

| quantity | GENERAL | FAST-BARE | FAST-REST | NUMPY-EXACT |
|---|---|---|---|---|
| exponent (log-log ms vs cells) | 0.991 | **0.921** | 1.012 | 0.480 |
| real-time ceiling @ 41.7 ms (24 fps) | **177²** | **2082²** (4.34M cells) | 221² | ~256²→~500× regime |

- **vs the 1.33 µs/cell engine baseline (133000):** FAST-BARE is **0.016–0.023
  µs/cell = ×61–84**. GEN re-earns 133000's 1.33 (1.28–1.40 µs/cell, same object,
  waves-only tick).
- **vs the numpy-exact ~500× reference:** FAST-BARE BEATS numpy at ≤32²
  (×0.40–0.90 = faster) but is **2.0–2.6× SLOWER at ≥64²** — the crossover is
  ~48². The numpy re-measurement here reaches ×24–220 over the engine (16²→128²)
  at exponent 0.48, consistent with 133000's ~500× at 256² (out of my
  pre-registered grid range). **FAST-BARE's exponent 0.921 vs numpy's 0.480 means
  the graph-layout tax GROWS with N** — this is the DEGRADE facet.
- **Ceiling:** the waves-only real-time ceiling moves **177² → 2082²** (×11.6 per
  side, ×136 in cells), and is ×39/side past 132000's assembled-eye 53².

## 5. THE ADMISSIBILITY GATE — routes stencil→fast, non-stencil→general (both correct)

`wave_stencil::admissible` reads the routing from graph STRUCTURE:
- **STRUCTURAL AST match** of the three stencil rules' `where`/`effect` (state
  literals, the `Minus(step,fired_at) ≥ refractory_steps` recover test, the
  `propagate` guard, the `neighbour` match-edge) — NOT rule names. Parameters
  (`refractory_steps`, `propagate`) read from the graph's `WaveParams`.
- **Safety condition (b):** no OTHER active rule may READ or WRITE the CA's
  outputs (`state`/`fired_at`) — so the vectorized pass cannot race or be raced
  by any non-stencil rule. Then CA-first-then-rest ≡ the interleaved fixpoint.
- **Strict (BARE) mode** additionally refuses when learner nodes (Unit/Synapse)
  are present (their rules fire and mutate during a tick — skipping them would
  diverge).

Verified live (`test_stencil_simd_migrated.py`):

| config | verdict | result |
|---|---|---|
| pure wave field | admissible (both modes) → **fast**, byte-identical | ✓ |
| noise arm (`propagate=0`) | admissible → **fast**, no recruitment, byte-identical | ✓ |
| learners present, `run_rest=True` | admissible → stencil fast, learners run UNTOUCHED via general pass, **byte-identical** (the "irregular rules untouched" composition) | ✓ |
| learners present, `run_rest=False` | **INADMISSIBLE** (strict) → False → caller falls back to `tick` (general) | ✓ |
| a NON-stencil rule writing `state` | **INADMISSIBLE** (4th state-writer fails the template) → False → general | ✓ |
| a foreign rule READING `state` | **INADMISSIBLE** (condition b) → False → general | ✓ |

## 6. WHAT I GOT WRONG

1. **I under-predicted how the SAFE default caps.** My prereg predicted CONFIRM
   with a large speedup, and proviso (b) named "if running the rest is not
   near-free the speedup shrinks" — but I under-weighted it: the "rest" (the
   engine's dirty-scan over ~20 inert cognition rules the waves-only boot
   carries) is **~98 % of the general tick, not a small tail**, so `run_rest=True`
   is only ×1.6–1.7. The ×84 requires BARE mode. The huge win is as much
   "skip the inert general machinery" as "vectorize the stencil."
2. **I predicted FAST would approach numpy-exact; it does not at scale.** I rated
   the gather/scatter wall (proviso (a)) as the less-likely branch. In fact
   FAST-BARE is 2.0–2.6× SLOWER than numpy at ≥64² and the gap WIDENS with N
   (exp 0.921 vs 0.480) — the assoc-list node-attr layout, not the compute, is
   the wall, and it is a bigger wall than I expected. This is a real, first-class
   DEGRADE facet and it names the next lever precisely (a dense field-backing
   store).
3. **The first gate version was a footgun.** It admitted the learner config for
   BARE mode (returns True); with `run_rest=False` that SKIPS the learner rules
   and DIVERGES (measured: `gen==fast(run_rest=False)` False with learners). I
   caught it in testing and added the STRICT (no-learner) guard for BARE mode
   before any measurement — but the honest record is that the naive gate would
   have silently produced wrong results for a learner-laden bare call.
4. **Run 1 had a contaminated point I nearly reported.** The 32² CI was 4.72 %
   (vs ~0.5–1.4 % elsewhere) — a transient from stray poll-shells. I re-ran
   (run 2: 1.18 %) rather than quote the wide point; the protocol's "a number
   whose CI is wide is reading contention" applied to my own instrument.

## 7. SCOPE — what is NOT shown (§8)

- **The kernel implements the state-CA stencil FAMILY (the wave CA).** The GATE
  is structural (AST-matched, parameters read from the graph, so it composes over
  grid size and `refractory_steps`/`propagate`); the KERNEL is that family's
  semantics. A fully general stencil-AST→array compiler for ARBITRARY uniform
  local rules is the named next lever, NOT built here.
- **The graph-layout wall is NAMED, not removed.** The measured DEGRADE vs
  numpy-exact is the assoc-list node-attr gather/scatter; a dense field-backing
  store for stencil-typed subgraphs is the extension that would close it. Not
  built (it is a representational change, deferred for review per the
  refinement-depth precedent).
- Single-thread; one grid family (square); CPU; governor powersave; synthetic
  ignition field. Multi-core over the field (131000/132000's lever) is orthogonal
  and not built. Grids capped at 128² (pre-registered); the numpy ~500× regime
  is at 256², out of range but consistent with the fitted exponent.
- This speaks to SCALE for a KNOWN local rule, NOT the representation frontier
  (130000) nor UNKNOWN dynamics where no exact vectorization exists.

## 8. Bench state — no new instrument-seams red

`tests/test_instrument_seams_migrated.py`: **3 failed / 19 passed — ALL THREE
PRE-EXISTING, verified NOT mine:**

1. `test_the_preamble_gate_binds_NEW_violations_only` → `pa.new_violations() ==
   ['scripts/codec_decision_probe.py']` — the task's NAMED baseline red. My three
   scripts each CALL `engine_preamble()` (not a bare import), so I add **no new
   preamble violation** (verified directly).
2. `test_the_measured_ledger_record_is_CURRENT` → the committed seed-record is
   stale (`committed=165 live=168` blocks; the diff includes **133000–133999**,
   the PRIOR rung's block). Regenerating (`domains.seed_record --write`) would
   sweep other rungs' changes into a commit — **§11 forbids me touching a shared
   ledger I do not own; the supervisor sequences it.** My block draws only
   in-block seeds 134000–134004.
3. `test_every_new_prereg_records_its_check_claim_output` →
   `['VISION_CLOSURE_PREREG.md', 'VISION_EYEVIEW_PREREG.md',
   'VISION_MOTIONENERGY_PREREG.md']` — three OTHER rungs' preregs.
   **`VISION_STENCIL_SIMD_PREREG.md` is NOT in the list** — my prereg records its
   `check_claim` verbatim (clause-8).

`cargo test` for the variant-table test does not LINK in this crate (PyO3
`extension-module` — a test binary can't resolve the Python symbols); this is
pre-existing and independent of my change, which adds **no Term variant**
(`NUM_TERM_VARIANTS` = 181 unchanged), so the variant-table invariant is
structurally preserved. All pytest gates and both oracle runs pass.

## 9. Ledger row (transcribe to VISION_PROTOCOL.md — do NOT edit it here)

| block | outcome |
|---|---|
| **134000–134999 (byte-identity battery seeds 134000–134004; timing deterministic WaveWorld seed 0; `check_claim` CLEAN, unknown_sinks 563; Rust `wave_stencil.rs` added — a vectorized stencil fast path + structural admissibility gate + one `#[pymethods]` `wave_stencil_tick`, NO new Term, NUM_TERM_VARIANTS 181 unchanged; adapter opt-in `stencil_fast` DEFAULT OFF)** | **RUST-VECTORIZED STENCIL AS THE ENGINE'S ADMISSIBLE FAST PATH — CONFIRM on the built lever, DEGRADE vs numpy-exact.** The RetinaCell state CA (verified radius-1, byte-identical to `s.tick()`; a waves-only tick mutates ONLY state/fired_at) is now applied in ONE vectorized Rust pass, GATED by a STRUCTURAL admissibility check (the three rules' where/effect ASTs matched — NOT by name — params read from the graph; safety condition: no other active rule reads/writes state/fired_at; strict BARE mode refuses learner subgraphs). BYTE-IDENTICAL: 0 mismatched cells over grids {8..32}×5 seeds×100 iterated ticks×both modes, noise arm, and learner composition (`test_stencil_simd_migrated` 19/19). SPEEDUP: BARE mode (pure field) 0.016–0.023 µs/cell vs the engine's 1.28–1.40 (re-earns 133000's 1.33) = **×61–84**, SUBLINEAR (exp 0.921), real-time ceiling **177² → 2082²** (×11.6/side; ×39/side past 132000's 53²). The SAFE default (run_rest=True, byte-identical in ALL admissible configs incl. learners-untouched) is only ×1.6–1.7 — the general dirty-scan over the ~20 INERT cognition rules the boot carries is ~98% of the tick; the ×84 is BARE mode SKIPPING that inert machinery for a pure stencil field. **DEGRADE vs numpy-exact:** BARE beats byte-identical numpy at ≤32² but is 2.0–2.6× SLOWER at ≥64² and the gap WIDENS (exp 0.921 vs 0.480) — the graph's assoc-list node-attr GATHER/SCATTER, NOT the compute, is the wall. NAMED lever (not built): a dense field-backing store for stencil-typed subgraphs. Gate routes: stencil→fast, learners+bare→general, non-stencil-state-rule→general, foreign-field-reader→general (all correct). WHAT I GOT WRONG: (1) under-weighted that the SAFE default is capped ×1.7 by the inert-rule scan; (2) predicted FAST would approach numpy — it is SLOWER at scale, the layout tax GROWS with N; (3) the first gate admitted learners for bare mode (footgun) — caught, strict guard added; (4) run 1's 32² CI was 4.72% (stray-shell transient) — re-ran, run 2 1.18%. Engine `own` `d072fc1b212d` re-verified `own` in-process; oracle `rung7_vision_bench` **222/0 BEFORE and AFTER**; `check_claim` verbatim in prereg clause-8; per-point CI ≤1.36% PROVING solitude; governor powersave; NO new instrument-seams red. Raw: `results/stencil_simd.json` (+ `_run1.json`); instrument `scripts/stencil_simd_measure.py`; gate `tests/test_stencil_simd_migrated.py`; CA control `scripts/_scratch_ca_verify.py`; mutation probe `scripts/_scratch_tick_mutation_probe.py`. |
