# Automatic recognition of the evidence-accumulation generator — PREREG

Base: `main @ 5ccbe3b` ("Merge logodds-generator: causal-strength dimension +
item 4 graded Hebbian reweighting, GO"), verified via `git log --oneline -1
main` immediately before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/logodds-diminfer`, branch
`logodds-diminfer`.

**Charter.** `LOGODDS_GENERATOR_RESULTS.md` §7.1 named, precisely, what it
left un-built: *"`DimInfer`/`TimeInfer` automatic recognition of this
generator from a raw observation trajectory (rather than explicit
declaration) is named as separate, un-sized follow-on work."* This document
closes that named gap: decide which of the two mechanisms actually fits,
register the decision criteria and the exact live-demonstration scenario
BEFORE writing any seed/rule code, per house discipline.

---

## 1. What was read before this decision (source, not recollection)

1. `CLAUDE.md`'s "BASE-AS-DIMENSION + the frame/continuum invariant" and
   "SHAPES, NOT NUMBERS" sections — the governing invariant (in-frame is
   integer, cross-frame is the map) and the standing rule that a new
   subsystem should compose with the sd loop's `DimInfer`/mint ladder or the
   admissibility grammar, not invent a parallel mechanism.
2. `LOGODDS_GENERATOR_RESULTS.md` in full — the `translate` generator design,
   the PER-DIRECTION evidence-ledger convention (`evidence_confirm`/
   `evidence_disconfirm` as two attrs on ONE `Coactivation` node), the item-4
   Hebbian reweight rule, and the exact §7.1 gap this rung closes.
3. `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §5-7 — why `logodds` was chosen as
   a `translate`-shaped generator (count in-frame, log-odds cross-frame) and
   why the source-rank/kind taxonomy stays untouched.
4. `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` — orthogonal (mean-field
   solver limits), read for completeness; no direct bearing on this rung's
   decision, confirmed by reading it in full.
5. `runners/dsl/src/shape_decode.rs`, read end-to-end for the relevant
   functions: `Generator`/`load_generators`/`apply_translate_once`/
   `apply_generator_once`/`apply_generator_k` (`:389-867`), `build_candidate`
   (`:1758-1930`, the shared rung-1 consistency check both `TransformDecode`
   and `DimInfer` reduce to), `eval_dim_infer` (`:2259-2527`, the RUNG-2
   candidate-generator loop: for every held PART, every applicable
   GENERATOR, every `k` in its `params`, apply the generator and run
   `build_candidate` on the transformed candidate vs the GOAL — a two-frame
   comparison, PART vs GOAL, never a multi-frame trajectory), and
   `eval_time_infer` (`:3510-3697`, the SEQUENCE-shaped sibling: infers a
   transition generator `G` from the first pair, then VERIFIES it carries
   EVERY consecutive pair by exact equality, with an order-N finite-
   difference fallback when the order-1 exact-equality path fails but the
   offset stream is itself regular).
6. `seeds/time_axis.json`, `seeds/f16_flight_path_control.json` (the
   `f16_sample_axis_margins`/`f16_project_axis_clocks` rule pair) and
   `seeds/shape_decode_loop.json` (`sd_infer_dimension`/`sd_recognize_dim`)
   — the two existing, live, working idioms for (a) accumulating a rolling
   sample-window `Tuple` attr via `Append`/`ListDrop`/`Count` and feeding it
   to `TimeInfer` via `MapList`, and (b) minting a `DimensionGenerator`/
   `LatentDimension` pair from a Term's field-selected output via
   `add_node_if_absent` (content-keyed, per `DEDUP_ADOPTION_SWEEP_RESULTS.md`
   v1.9.0).
7. `tests/test_can_native_reimplementation.py` (item 4's own tests) — the
   exact harness idiom (`_loaded_substrate`, `_isolated_pair`,
   `_coact_between`, `_log_odds_term`) this rung's new tests reuse
   unmodified.

---

## 2. The DimInfer-vs-TimeInfer decision, registered

**Claim A (checked against source, not assumed): `DimInfer`'s rung-2
generator-selection loop is architecturally UNREACHABLE for a single
`(evidence_confirm, evidence_disconfirm)` relation compared pairwise against
a held base.** `build_candidate`'s tier-1 consistency check (`:1833-1930`)
requires a per-dimension delta to be UNIFORM ACROSS ALL ALIGNED PAIRS — and
for a signature made of exactly ONE relation (a single Coactivation ledger's
current `(confirm, disconfirm)` state), there is only one aligned pair, so
the "uniform" check is vacuously true for ANY delta on ANY slot. This means
`TransformDecode`'s rung-1 (which calls `build_candidate` directly on the
part's RAW signature, no generator applied at all) already reports
`explained=true` for literally any single-relation two-slot delta, with zero
residual left for `DimInfer` (rung 2) to add value over. Per the sd loop's
own Occam ordering (`sd_recognize` → `sd_transform_decode` →
`sd_infer_dimension` → `sd_mint_quantum`), rung 2 is never reached for this
representation at all — not because `DimInfer` is broken, but because there
is nothing for it to explain that rung 1 hasn't already explained trivially.
**Prediction, registered before any code is written**: a direct probe
(`TransformDecode` on a single-relation goal with a confirm+disconfirm
delta, against a held base with no generator at all) will report
`explained=true` with a plain per-dim `transforms` list and no
`DimensionGenerator` ever consulted — confirming this claim live, not merely
by source-reading.

**Claim B: `TimeInfer` is the correct mechanism for the temporal,
sequence-shaped half of this problem, but its single-constant-generator
requirement means it explains a PURE, single-axis reinforcement run and
correctly (not defectively) REFUSES to explain a genuinely coupled,
event-conditional confirm/disconfirm trajectory.** `eval_time_infer` requires
ONE transition generator `G` to carry EVERY consecutive frame pair by exact
equality (`:3645-3665`); a real evidence trajectory where SOME ticks bump
`confirm` and OTHER ticks bump `disconfirm` (exactly
`LOGODDS_GENERATOR_RESULTS.md` §4(a)'s own tested trajectory: `(1,0)` delta
for three ticks, then `(0,1)` for one tick) has a CHANGING per-tick offset,
which is not a single constant `G` and is not (per `order_n_translate_
verdict`) a regular polynomial-order sequence either — it is event-driven,
not smoothly accelerating. **Prediction, registered**: `TimeInfer` on the
FULL 2-D `(confirm, disconfirm)` window across a mixed run will report
`explained=false`. `TimeInfer` on a 1-D PROJECTION of just the `confirm`
axis, during a WINDOW where every sampled tick is a genuine confirming
observation (a "pure reinforcement run" — exactly the four leading ticks of
`LOGODDS_GENERATOR_RESULTS.md`'s own item-4(c) demonstration), will report
`explained=true, kind="translate", offset=(1,)` — a real, live, un-forced
positive case matching that document's own already-tested scenario, with
automatic recognition now on top of it.

**Decision: build on `TimeInfer`, not `DimInfer`, for the positive
half — because the problem is genuinely a TRAJECTORY (repeated observations
across ticks), which is `TimeInfer`'s stated territory ("the TEMPORAL
sibling of `GenInfer`"), not a two-frame spatial comparison — and it does
not need the generator pre-declared: `TimeInfer` infers `kind`/`offset`
fresh from the data (generate-and-test on the first pair), exactly satisfying
the task's "WITHOUT the logodds/translate-based generator being explicitly
pre-declared" requirement with zero codebook lookup needed at all.** No new
Rust Term. No modification to `DimInfer`'s core logic (out of scope and
unneeded — `DimInfer` is not the mechanism doing the work here). The only
new code is graph data: one tiny codebook `Part` (`EvidenceAxisSample`,
mirroring `F16AxisSample`'s exact shape) plus two seed rules (a window
sampler, mirroring `f16_sample_axis_margins`; and an inference/mint rule,
mirroring `sd_recognize_dim`'s `add_node_if_absent` idiom applied to
`TimeInfer`'s field-selected output instead of `DimInfer`'s).

**Registered NULL, stated up front rather than discovered after the fact**:
the FULL, genuinely-coupled, event-conditional 2-D evidence trajectory is
**not** a shape either `DimInfer` or `TimeInfer` can automatically recognize
as a single dimension, by design (not a bug) — `DimInfer` because there is
no residual left for it to explain (Claim A), `TimeInfer` because the
trajectory is not a constant-velocity (or regular finite-difference) orbit
(Claim B). This is a real, informative scope boundary this document reports
as a **standing finding**, not a failure to be patched around: it directly
validates why `LOGODDS_GENERATOR_RESULTS.md` tracks `evidence_confirm`/
`evidence_disconfirm` as separate, PER-DIRECTION, independently-steppable
counters on the same node rather than as one coupled 2-vector — only the
per-direction decomposition is automatically inferable at all via the
existing sd-loop machinery.

---

## 3. The exact live-demonstration scenario, registered before building

All demonstrations run on `tests/test_can_native_reimplementation.py`'s own
harness (`_loaded_substrate`/`_isolated_pair`/`_coact_between`), loading
`seeds/can_native_reimplementation.json` **plus** the new
`seeds/evidence_axis_infer.json` — and critically, **NEVER**
`seeds/inference_knowledge.json` (so the pre-declared `logodds_evidence`
`DimensionGenerator`/`latent:causal_strength` `LatentDimension` from that
seed are simply absent from the graph — the cleanest possible "without the
generator pre-declared" condition, not a synthetic exclusion).

1. **Zero-mint-once-recognized / correct-mint-on-recurrence (the positive
   case).** Drive an isolated pair through a pure reinforcement run (mint +
   3-4 further confirming ticks, no disconfirming tick — mirroring item-4(c)
   exactly). Predict: after enough samples accumulate in the window
   (`Count >= 3`), the new `evidence_axis_infer` rule fires and mints
   `DimensionGenerator{name:"logodds_evidence_inferred", kind:"translate",
   coord_dims:(0,), offset:(1,)}` + `LatentDimension{name:
   "latent:causal_strength_inferred", generator:"logodds_evidence_inferred"}`
   + a `has_inferred_axis` edge from the `Coactivation` node — **exactly
   once**, confirmed by continuing to run rules for several more ticks (the
   window keeps satisfying `explained=true`) and asserting node/edge counts
   stay flat after the first mint (the `has_inferred_axis`-edge guard is the
   idempotence mechanism, the same shape `sd_recognize_dim`'s
   `has_transform`-edge guard already uses).
2. **No-spurious-mint on an unrelated/irregular trajectory.** A second
   isolated pair whose `b` concept's state is DELIBERATELY zero on some
   ticks (a real, not synthetic, way to make `can_native_hebbian_reweight`'s
   own guard skip a tick — `Not(Eq(b.state,0))`), producing a window with
   genuine GAPS (flat-then-jump, not constant velocity). Predict:
   `TimeInfer(explained)` reports `0` on this window and the mint rule never
   fires — confirmed by asserting no `DimensionGenerator` named
   `logodds_evidence_inferred` and no `has_inferred_axis` edge exist after
   running rules to convergence.
3. **The registered null, demonstrated directly.** Feed `TimeInfer` the FULL
   2-D `(confirm, disconfirm)` window from `test_evidence_counters_are_real_
   integers_stepping_across_ticks`'s own trajectory (`(0,0)→(1,0)→(2,0)→
   (3,0)→(3,1)`) and confirm `explained=0` — the coupled pair is genuinely
   not recognized as one dimension. Separately, probe `TransformDecode`
   directly on a single-relation two-slot goal (Claim A) and confirm
   `explained=1` with a plain per-dim `transforms` list, no
   `DimensionGenerator` consulted — demonstrating rung 2 is architecturally
   unreached for that representation, live, not by source-reading alone.
4. **Composition with the Hebbian mechanism (item 4).** After the mint in
   (1), evaluate the EXISTING, UNCHANGED `_log_odds_term()`
   (`Log(Div(Plus(confirm,1),Plus(disconfirm,1)))`) on the SAME
   `Coactivation` node and confirm it renders the same value it would
   without the new seed loaded — the inferred generator is read-accessible
   graph data alongside the counters, not a parallel, disconnected
   mechanism, and the counters/render are UNTOUCHED by the new rules (no
   `evidence_confirm`/`evidence_disconfirm`/render key ever written by
   `evidence_axis_infer.json`'s own effects — confirmed by diffing node
   attrs before/after the new rules fire, the same discipline
   `LOGODDS_GENERATOR_RESULTS.md` §4(b) used).

---

## 4. Explicitly out of scope (restated, not re-derived)

`translate`'s existing generator semantics and the log-odds rendering
formula are untouched. `can_ops.rs` and its real consumers
(`domains/insight_detection.py` et al.) are untouched — nothing in this rung
touches those files. No new Rust Term: `TimeInfer` (existing) is the only
Term this rung calls; if a live probe during §3 finds a genuine gap in
`TimeInfer`'s existing signature, this document commits to reporting that
gap and stopping rather than adding a Term unregistered here.

---

## 5. What a GO looks like

All four demonstrations in §3 pass with real, printed numbers (window
contents, `TimeInfer` output dicts, node/edge counts before and after).
Regression: `tests/test_can_native_reimplementation.py` (all existing tests,
byte-unchanged) plus the CAN scoped regression bundle
(`test_can_belief_quantization.py`, `test_bigville_can_integration.py`,
`test_causal_attitude_networks.py`, `test_can_ops.py`, `test_can_migration.py`,
`test_can_crossover_point.py`) stay green. No `.rs` files touched
(`git diff --stat main -- '*.rs'` empty) — if this document's Claim A/B
decision holds, as predicted, no Rust build or `cargo test` run is needed,
matching `LOGODDS_GENERATOR_RESULTS.md`'s own precedent.
