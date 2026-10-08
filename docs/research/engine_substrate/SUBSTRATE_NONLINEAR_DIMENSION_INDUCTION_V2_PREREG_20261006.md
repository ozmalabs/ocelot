# Bounded quadratic GenInfer v2

## Question and status

Can the native shape-decode learning path acquire, graph-mint, persist, reload,
and reuse a bounded 2-D integer quadratic coordinate map with exact held-out
transfer, while preserving the default linear-only behavior?

This protocol is frozen before the v2 implementation. The feature is
experimental and must remain disabled by default. The v2 design and exact
fixture identifiability preflight are documented in
[`SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_DESIGN_20261006.md`](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_DESIGN_20261006.md).
The pre-capture correction and matched audit-parity extension are recorded in
the versioned [v2.1 amendment](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_1_AMENDMENT_20261006.md).
The launcher failure handling for the source-locked evaluation is specified
in the [v2.2 amendment](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V2_2_AMENDMENT_20261006.md).

## Hypothesis family and fixtures

Fit each output coordinate as an integer combination of
`[x, y, x², xy, y²]` over normalized input coordinates. There is no constant
term; the existing rung-1 residual stage handles a uniform translation.
Require full feature rank 5, stable unique predicate+`id` alignment, exact
training agreement, checked integer arithmetic, and coefficients in `[-8,8]`.
The solver must abstain on rank deficiency, identity ambiguity, non-integral or
out-of-bound coefficients, overflow, or any residual mismatch. It must solve
the fixed-size system directly; exhaustive coefficient-tuple enumeration is
out of protocol.

Use five basis points `(1,0),(2,0),(0,1),(0,2),(1,1)` plus two
overdetermining training-validation points `(3,1),(4,1)`. Solve on
coordinate differences from the first aligned relation so a uniform output
translation remains a residual; require the difference design to have rank 5
and require every aligned training residual to be the same translation. The
solver must validate all seven before minting; the extra rows prevent arbitrary
targets or the cubic control from being interpolated by a degree-2 map. Use ten fresh
replicates per cell, each with feature-off and feature-on arms:

1. Linear positive control: `T(x,y)=(x+y,2y)`.
2. Coupled quadratic: `T(x,y)=(x+xy,y+x²)`.
3. Quadratic cross-term transfer: `T(x,y)=(x,y+xy)`.
4. Rank-deficient coupled-quadratic training geometry.
5. One corrupted coupled-quadratic training relation.
6. Duplicate identity keys in training.
7. Missing/disjoint identity key in training.
8. Out-of-family cubic map: `T(x,y)=(x,y+x³)`.

Positive fixtures use the full-rank training points, both redundant validation
points, and disjoint transfer points in the linked preflight. Keep target
coordinates hidden from analysis until exact predictions are scored. For each
worker, train, capture the minted
operator and generator count, serialize and reload the graph, then present the
held-out base and target through the ordinary observation/closure path.

## Required source behavior

- `geninfer_quadratic_map_solver` is an opt-in Cargo feature and acquisition is
  additionally controlled by a runtime flag; both default off.
- A learned operator carries an explicit kind and coefficient payload through
  `GenInfer`, the seed mint rule, `DimensionGenerator` loading, composition,
  `DimInfer` application, and persistence. Do not overload the linear `matrix`
  attribute with polynomial coefficients.
- Feature-off results, generator attrs, and linear positive behavior match the
  pre-feature control. Feature-on prefers a valid linear fit over a quadratic
  fit and does not add quadratic search work when the linear fit already wins.
- Rank-deficient, identity-ambiguous, corrupted, and out-of-family controls do
  not mint a quadratic generator. An abstention must leave the prior generator
  codebook unchanged; novelty-axis behavior is recorded separately.
- Native work counters reconcile eligible bases, exact solver attempts,
  rank/identity/overflow refusals, training validation, and held-out reuse.

## Measures and admission gates

Record for every arm: source/native provenance, initial/final generator
payloads, training/held-out statuses, exact predictions, residuals, quanta,
codebook changes, candidate work, checked arithmetic work, closure CPU/wall
time, allocation/RSS, and counter totals. Separately record matched
audit-enabled and audit-disabled runs; do not use instrumented latency as clean
performance evidence.

Admission requires all of the following:

1. Frozen protocol, runner, analyzer, generated schedule, source tree, build
   manifest, native binaries, and seed manifest before capture.
2. Exactly 160 fresh workers, exact schedule, stable source/binary inputs, and
   repeat parity.
3. Feature-off linear acquisition/transfer remains exact in all replicates;
   feature-off nonlinear arms do not acquire the quadratic payload.
4. Feature-on linear control remains exact and selects the linear kind.
5. Both positive quadratic families acquire exactly one typed quadratic
   generator and predict every disjoint held-out relation exactly after graph
   serialization/reload.
6. Every negative control abstains from quadratic minting, does not mutate the
   pre-existing generator codebook, and records the specified refusal reason.
7. Coefficient payloads are canonical, within bounds, exactly equal to the
   independent oracle, and reusable by ordinary `DimInfer` (not a runner-side
   prediction shortcut).
8. Counter conservation and audit-on/off semantic parity pass. Performance is
   reported only if matched clean runs and semantic gates pass.

Any failure is preserved and analyzed; do not edit implementation or analyzer
after capture and continue calling the same run confirmatory. A changed solver,
fixture, feature boundary, or counter schema requires a versioned protocol.

## Scope boundary

A passing result establishes only these bounded 2-D integer polynomial
families, identity semantics, coefficient bound, and registered fixture sizes.
It does not establish arbitrary nonlinear induction, noisy or floating-point
learning, sequence-map induction, natural-task prevalence, or general
intelligence. Keep the solver opt-in until broader task prevalence and scaling
are measured.
