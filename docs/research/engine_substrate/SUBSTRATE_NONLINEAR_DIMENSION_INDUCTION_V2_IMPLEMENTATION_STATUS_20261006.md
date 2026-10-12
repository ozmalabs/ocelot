# Bounded quadratic GenInfer v2 implementation status

## Status

The opt-in native quadratic acquisition path is implemented and has passed a
single end-to-end smoke worker. The amended 320-worker confirmation has not yet
run. This document records implementation evidence, not a capability claim.

## Implemented

- Cargo feature `geninfer_quadratic_map_solver` gates the learner and is off by
  default. A second runtime gate, `agent.gen_quadratic_enabled`, must also be
  enabled.
- `GenInfer` exposes the discovered `kind` and `coefficients`; its evaluation
  cache key includes the runtime gate.
- The learner aligns relations by predicate and stable identity slots, fits
  the fixed basis `[x, y, x^2, xy, y^2]` with exact rational elimination,
  requires rank five, bounds integer coefficients to `[-8,8]`, and validates
  all registered training rows including the two overdetermining rows.
- The seed has a separate quadratic mint rule. It writes `kind="quadratic2"`
  and a dedicated coefficient payload; the existing linear mint rule retains
  its linear name and attribute schema.
- Generator loading, application, composition and `DimInfer` accept the typed
  quadratic payload. Coefficients are not stored in the linear `matrix` field.
- Counters distinguish feature/runtime eligibility, solver attempts,
  validation rejects, survivors, and refusal reasons.

## Verification so far

- `cargo check --lib` passed with the default feature set.
- `cargo check --lib --features geninfer_quadratic_map_solver` passed.
- `cargo build --release --lib --features geninfer_quadratic_map_solver` passed.
- A manually run feature-on worker trained on the seven preregistered points
  for `T(x,y)=(x+xy,y+x^2)`. The normal observation and closure path minted
  exactly one `quadratic2` generator with coefficients
  `[1,0,0,1,0,0,1,1,0,0]`; the observation reached
  `recognized_transformed` on re-decode.
- A second worker with the runtime quadratic gate absent minted no quadratic
  generator. It followed the existing fallback path (`status="minted"`), so
  this verifies only the quadratic gate, not semantic parity with a separately
  compiled feature-off engine.
- The temporary feature-enabled extension installation was restored. The
  package extension is back to SHA-256
  `7fdfe5ea884bc5e8305b208a9c6657dac16d0684b53c376c8a6b48c359c4c511`.
  For the v2.2 partial run, the feature-off release binary is currently at
  `runners/dsl/target/release/libsubstrate_rs.so`, SHA-256
  `e7b91728dcc5a4c9581726617b5b10a1584e5d9b19ab950655bda0aeec05b5bc`; the
  locked feature-on binary is at the path recorded in the v2.2 lock and has
  SHA-256 `1c572f55be18d0ee7400f141e0725d96de27b0f0ceac05e43710ecb5ad886210`.

## Still required before confirmation

The v2.1 runner and analyzer produced no raw capture. The v2.2 launcher added
per-worker progress, timeouts, and durable checkpoints. Its source/native
locked capture completed nine of 320 workers before the high-range cubic
control timed out after 300 seconds in feature-off training closure. The
partial capture and analyzer output are preserved in the v2.2 results report.
The nine completed rows verify the registered linear/quadratic positive
examples and no-quadratic-mint controls individually; the incomplete schedule
does not verify repeat parity or protocol admission. In particular, audit
parity and clean performance admission remain unproven.

The newly measured cost centre is the pre-existing 2x2 linear matrix search:
the cubic target's normalized extent produced `B=64`, so the legacy path
attempted up to `129^4` matrices per eligible base before the quadratic solver
could reject the map. The coupled-quadratic positive worker also spent about
13.4 seconds and recorded 7.1 million matrix attempts before acquiring its
quadratic generator. The next gate is to preregister and measure a proved
exact-linear prefilter for full-rank, uniquely identity-aligned bases. No
change to the search or default feature set has yet been made.

## Exact-linear prefilter implementation status

The preregistered v1 work has started in the current worktree. Cargo feature
`geninfer_linear_exact_prefilter` and the separate optional `GenInfer` term
field `linear_prefilter_enabled` are present; the `shape_decode_loop` seed
binds that field to `agent.gen_linear_exact_enabled`. Both gates default off.

The feature path now performs a typed predicate-plus-id keyed join, requires a
full-rank 2-D source basis, solves the unique integer matrix with checked
`i128` arithmetic, verifies every aligned row, then sends a recovered matrix
through the existing transform and candidate validators. Proven no-fit skips
the exhaustive matrix loop; unsupported, ambiguous, rank-deficient, or
arithmetic-overflow cases fall back to the historical enumerator. Key joining
and rank-basis discovery are expected O(n); the fixed-size solve is constant
work, and full-row verification is O(n). This is an algorithmic path claim,
not yet a benchmark result.

`cargo check --lib` and `cargo check --lib --features
geninfer_linear_exact_prefilter` pass. Three feature-gated Rust tests pass for
exact linear recovery, nonlinear refusal, conservative duplicate-key and
rank-deficient fallback, and the complete 625-matrix corpus with coefficients
in `[-2,2]`. The PyO3 test binary requires Python 3.13 shared-library flags in
this environment. The finite unit corpus tests exact-map recovery, not the
full GenInfer result against its historical enumerator.

A paired runtime pilot then completed 20 workers: ten audit-off timing pairs
and ten audit-on counter pairs on one linear-positive case. All gate-on/off
semantic projections matched, as did audit-on/off semantics. Median clean
closure was 75.49 ms with the prefilter off and 27.31 ms with it on; audited
matrix attempts fell from 39,360 to 19,683. Three of six base attempts solved
and three fell back. The pilot is documented separately and is not the
preregistered three-build admission capture. The v2.2 locked artifacts remain
historical and must not be interpreted as measuring this modified source.

Remaining work for the v1 gate: build and lock the three matched engine
variants; execute the finite differential corpus and semantic panel; run the
separate high-bound stress worker; analyze results and update the overall
capability plan. Until those gates pass, the optimization is implemented but
not admitted, and the pilot's single-condition speedup must not be generalized.

## v1.1 high-bound amendment outcome

The first prefilter build still exceeded 300 seconds on the high-bound cubic
control. The v1.1 amendment added one exact early proof: the existing candidate
validator rejects every matrix if relation counts differ, and a linear map
preserves that count. After implementing that proof, the audit-off worker
finished in 0.32 s process wall time; its audit-on sibling finished in 0.30 s.
Audit counters show two no-fit proofs, zero matrix attempts, two quadratic
attempts, zero quadratic survivors, and no generator payload before or after
held-out transfer. This addresses the specific high-bound control; the full
three-build preregistered panel and general scaling claim remain open. See the
[v1.1 high-bound result](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_HIGHBOUND_RESULTS_20261006.md).

## v1.2 integer-domain correction and frozen differential oracle

The expanded differential suite found that generic `Value::as_i64()` truncates
floats. The exact prefilter now accepts coordinates only when they are
`Value::Int`; noninteger coordinate frames fall back to the historical search.
The refreshed source-locked oracle passes six feature-gated tests, including comparison
with the historical enumerator over four full-rank point sets and all 625
matrices in [-2,2] (2,500 cases). The selected-output digest is
`a8529e7d68e1c625`. Tests also cover rank deficiency, nonlinear targets,
missing/duplicate identities, relation-count no-fit, floats, and multi-ID
alignment. The sixth test checks that identity-value comparisons and checked
arithmetic counts are audit-gated. The implementation now reports stable
proven-no-fit and fallback reasons. The refreshed capture is
`evaluation/reports/geninfer_exact_linear_prefilter_oracle_v1_2_20261006.json`,
SHA-256 `6912a03015273e70b1a7d4dd17fd267c54e2a0711ec2546a4e3ea22df08f6b9c`.
See the [v1.3 instrumentation amendment](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_3_AMENDMENT_20261006.md)
and [oracle result](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_ORACLE_V1_RESULTS_20261006.md).

## v1 three-build panel outcome

The main source-locked capture completed 480/480 workers with zero failures;
the independent analyzer passed all 15 gates. It verified held-out oracle
rows, positive quadratic acquisition and transfer, no quadratic false mints,
prefilter/quadratic semantic parity, and audit-on/off parity. The prefilter's
80 audited workers recorded 30 exact solves, 220 proven no-fits, and 30
fallbacks with reason counters conserving exactly.

Across ten clean repeats per condition, median training-plus-held-out closure
fell from 78 ms to 2.5 ms on the linear positive, from 7.9–13.7 seconds to
1.3–2.6 ms on several controls and quadratic positives, and from 111 seconds
to 70 seconds on rank-deficient geometry. These measurements show substantial
benefit when cheap proof applies, while rank-deficient and ambiguous-identity
fallbacks remain costly. The exact solves occurred in the linear-positive
condition; most gains came from sound no-fit proofs. This bounded synthetic
panel does not establish natural-task prevalence, general graph tractability,
or rung-three learning. See the [v1 results](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_RESULTS_20261006.md)
and its source-linked capture and analysis.

## v1.4 soundness repair, exact fallback stages, and prevalence (2026-10-06)

An exploratory differential run found that the v1 prefilter diverged from the
historical enumerator on two-predicate, id-bearing inputs at `max_dims=2`
(145–701 of 1,488 cases per family, including 253 exact linear images): the
enumerator accepts per-predicate shift residuals that the affine proof does
not model. The v1 panel's parity result is therefore scoped to its
single-predicate fixtures. v1.4 guards the affine proof (single predicate,
identity-only prefix before the coordinates) and adds two exact stages before
the enumerator: a row-factorized search for unique-prefix frames and a
correspondence-complete generator for frames without one. A 37,500-case
finite census (all 625 matrices in [-2,2], ten families, six point sets)
matched the enumerator in every case. The frozen v1.2 oracle digest is
unchanged. 914/914 real and production-shaped pairs matched on/off.

Prevalence: no production `dim_types` declaration has an identity slot, so
the exact solve is reachable only from experiment fixtures. On
production-shaped inputs the gains come from fast refusal (relation-count
proof, correspondence no-candidate) and from the correspondence stage on
`sdloop_vision` bars (16×16: 17.8 s → 93 ms; 27.8 s → 373 ms). The panel's
expensive fallbacks now resolve at Term level in under 1 ms (rank-deficient
73 s, missing identity 4.0 s, duplicate identity 3.1 s off). The
correspondence stage grows with the cube of the block size (12.6 s at 324
relations). See the
[v1.4 results](SUBSTRATE_GENINFER_PREFILTER_PREVALENCE_V1_4_RESULTS_20261006.md).
