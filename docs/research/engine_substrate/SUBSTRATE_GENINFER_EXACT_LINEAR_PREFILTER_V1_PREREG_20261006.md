# Exact 2-D linear prefilter for GenInfer v1

## Question

Can GenInfer avoid exhaustive 2×2 matrix enumeration when an identity-aligned
full-rank training frame uniquely determines the only possible integer linear
map, while preserving the historical search result and its fallback behavior
on ambiguous or rank-deficient frames?

The v2.2 partial quadratic capture found 7,115,520 linear candidate attempts
and 13.4 seconds of training closure for one bounded coupled-quadratic worker.
Its high-range cubic control reached a 300-second timeout before the quadratic
solver ran. The legacy search bound was B=64, giving 129^4 matrices per base
per `GenInfer` evaluation. The exact source-locked result is
[`SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_2_RESULTS_20261006.md`](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_2_RESULTS_20261006.md).

## Proposed feature boundary

Add an opt-in Cargo feature `geninfer_linear_exact_prefilter` and runtime
`agent.gen_linear_exact_enabled`; both default off. Keep the quadratic-only
build as the direct control and preserve the prior v2.2 binary/result as a
separate historical high-bound reference.

For each 2-D base, the fast path may skip enumeration only when all of these
facts are proved: predicate-plus-`id` keys align every source and target row
uniquely; the source coordinate displacements have rank two; all coordinate
values are integers; checked exact elimination either recovers the unique
integer matrix within the existing data-derived bound, or proves no integer
matrix can satisfy the aligned rows up to the existing uniform residual.
Recovered matrices must pass the existing `apply_linear_once` and
`build_candidate` validators. Rank deficiency, missing/ambiguous identity
keys, non-total identity values, or any case whose impossibility is not proved
must use the historical exhaustive search unchanged. An exact identity result
retains the existing identity exclusion.

Candidate selection, residual semantics, matrix bounds, and mint rules remain
unchanged. The feature must not claim exactness from only a selected basis:
verify every aligned row. Use checked rational arithmetic; never enumerate
coefficient tuples in the new path.

## Frozen evaluation design

Three source-matched release builds:

1. Feature-off historical engine.
2. `geninfer_quadratic_map_solver` only (the current v2 behavior).
3. Both `geninfer_quadratic_map_solver` and
   `geninfer_linear_exact_prefilter`.

For the main semantic panel, compare all three builds on eight conditions,
ten fresh repeats, and matched audit-off/audit-on workers (480 total): linear
positive, coupled quadratic, cross-term quadratic, rank-deficient geometry,
corrupted training, duplicate identity, missing identity, and a bounded
centered-cubic out-of-family control. The cubic function is
`T(x,y)=(x,y+(x-2)^3)` on frame-local training coordinates; it preserves the
out-of-family test while keeping the search bound small enough to complete the
whole panel. The v2.2 `x^3` timeout remains the high-bound stress reference and
must not be relabeled as a completed refusal.

For the high-bound stress subgate, run one audit-off `x^3` worker with the
prefilter build. It must finish training, record a proof of linear no-fit,
continue to bounded quadratic refusal, and leave the quadratic codebook
unchanged. Compare it only against the v2.2 measured `>300 s` baseline as a
separate-source historical lower bound; do not pool that timing with the
matched main-panel measurements.

Before these workers, run an exhaustive differential corpus over all integer
2×2 matrices with entries in `[-2,2]` on several full-rank point sets. Require
the exact prefilter and historical enumerator to return the same explained
decision, selected matrix, base, residual transforms, and checked output for
every map. Include non-integer affine relations, cubic/nonlinear relations,
multiple identities, missing IDs, duplicate IDs, ambiguous predicates, and
rank-deficient sources. Freeze that oracle and its outputs before the native
capture.

## Measures and admission

Lock implementation source, features, both runtime gates, source seed closure,
runner, analyzer, oracle, Cargo inputs, and all three native binaries. Record
for each worker: candidate attempts, prefilter attempts/proofs, fallback
enumeration count, identity comparisons, exact arithmetic/refusal counters,
generator payloads, transfer statuses, `DimInfer` receipts, graph
serialization/reload, closure CPU/wall time, peak RSS, and audit-on/off
semantic parity. Do not include audit-on timings in clean performance
summaries.

Admission requires exact differential parity for the finite exhaustive matrix
corpus, all three builds to agree on semantic outputs for shared conditions,
the v2 quadratic positives to reuse after reload, all negative controls to
abstain without quadratic minting, counter conservation, complete schedule and
source stability, and successful completion of the high-bound stress subgate
within its frozen 300-second limit. Performance improvement is reported only
if all semantic and parity gates pass.

This establishes only a finite 2-D integer-map optimization under uniquely
identifiable frames. It does not establish tractability for rank-deficient,
identity-ambiguous, higher-dimensional, natural, or general learning tasks.
