# Exact-linear GenInfer prefilter v1.3 instrumentation amendment (2026-10-06)

## Measurement definitions

Before the three-build capture, make the v1 work accounting explicit:

- `identity_key_value_comparisons` counts each `Value` equality invoked by
  typed predicate-plus-ID hash-key lookup, duplicate detection, and exact key
  confirmation. Implement key equality in a small wrapper that preserves
  `Value` equality/hash semantics and increments only when scale audit is on.
- `exact_arithmetic_primitive_checks` counts checked integer multiply,
  subtract, remainder/division, and checked conversion attempts in the basis
  solve and all-row validation. No audit counter update runs when audit is off.
- Every prefilter proof/refusal records a stable reason in
  `proven_no_fit_reason:<name>` or `fallback_reason:<name>` in addition to the
  aggregate outcome counters. Relation-count mismatch, arithmetic
  nonintegrality, coefficient bound, and row residual are proven-no-fit
  reasons; malformed/missing/ambiguous identity, rank deficiency, unsupported
  coordinates, and overflow are fallback reasons.

These counters are observational only and must not affect candidate ranking or
runtime state. The full unit oracle and build checks must be rerun after the
instrumentation source change, and the oracle report/source hashes refreshed
before the main lock. All v1 semantic conditions and performance gates remain
unchanged.
