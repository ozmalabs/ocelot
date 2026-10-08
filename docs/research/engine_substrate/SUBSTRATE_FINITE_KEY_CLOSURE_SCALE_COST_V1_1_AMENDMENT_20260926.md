# Finite-key closure scale cost v1.1 — confirmation amendment

**Status: preregistered after the first capture and before the confirmation run.**
The v1 raw capture remains immutable. It passed all 147 per-run checks; this
amendment addresses whether its semantic result is stable across a fresh
interpreter process on the same checkout/native artifact.

## Confirmatory procedure

- Run the same locked 7×3×7 matrix from a second fresh process using a versioned
  runner whose workload, schedule seed, warmups, and timed regions are identical.
- Preserve the second raw output separately.
- Independently compare case IDs, exact projected graph digests, terminal node
  and edge counts, analyzer bounds, progress steps, fixed-point statuses, and
  per-cell replicate counts across processes.
- Treat timing as two descriptive process-level distributions; do not require
  per-sample timing equality or pool them as independent hardware environments.
- Require identical non-runner source and native artifact digests. Runner hashes
  differ by version as expected and are recorded for provenance.

## Claim boundary

Confirmation strengthens reproducibility only for the fixed recursive schema,
cycle topology, sizes, and signature counts. It does not broaden the rule
fragment, establish a general timing exponent, or estimate natural graph
distributions.
