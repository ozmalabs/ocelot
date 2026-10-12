# Exact-linear prefilter finite differential oracle v1.2 (2026-10-06)

The source-locked Rust oracle passes six feature-gated tests. Its exhaustive
test compares the selected result of the fast path against the historical
bounded matrix enumerator for four full-rank point sets and all 625 integer
2x2 matrices with coefficients in `[-2,2]` (2,500 generated cases). The
comparison covers the selected matrix, residual dimension count, and residual
transforms. A deterministic FNV-1a digest of those selected outputs is
`a8529e7d68e1c625`. The sixth test verifies that identity-value comparison and
checked-arithmetic work counters remain zero with scale audit disabled and
become positive when it is enabled. Identity comparisons use a wrapper with
the same `Value` equality and hash behavior as the prior vector key. Outcome
reason counters distinguish relation-count mismatch, nonintegral coefficients,
coefficient bounds, row residuals, and the fallback causes exercised by the
unit corpus.

The other tests cover nonlinear refusal; exact fallback on rank-deficient
geometry, duplicate or missing identities, and missing identity schema;
proven no-fit for relation-count mismatch; float-coordinate refusal; and
successful matching with multiple typed identity slots. The expanded oracle
found a bug before native comparison: the runtime's generic `as_i64()` truncates
floats. The prefilter was changed to accept only `Value::Int`, and the rerun
passed all five tests.

Artifacts:

- [Oracle runner](../../../evaluation/substrate_capability/run_geninfer_exact_linear_prefilter_oracle_v1.py)
- [Oracle capture](../../../evaluation/reports/geninfer_exact_linear_prefilter_oracle_v1_2_20261006.json), SHA-256 `6912a03015273e70b1a7d4dd17fd267c54e2a0711ec2546a4e3ea22df08f6b9c`
- [v1.3 instrumentation amendment](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_3_AMENDMENT_20261006.md)

The refreshed capture records source stability and includes the v1.3 amendment
in its manifest. This is finite differential evidence for the registered integer 2-D family.
It does not cover every `Value` structure, natural frame, alternate candidate
ordering, or general nonlinear induction. Its capture predates the three-arm
native main panel; the main lock must include the oracle report hash.
