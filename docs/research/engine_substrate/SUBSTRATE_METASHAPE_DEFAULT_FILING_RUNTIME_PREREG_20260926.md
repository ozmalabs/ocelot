# Default MetaShape filing runtime probe v1 — preregistration

**Status: locked before execution.** This is a bounded integration probe for the
open default-filing census. It does not measure semantic quality or production
frequency.

## Question

When the four in-repository `teach()` call expressions with no visible
`category=` or `categorise=` are exercised through their owning actor-goal
codebook helpers on a fresh default `WorldAdapter`, do they reach
`categorise_by_shape`, and what filing value does that consumer return?

## Fixed method

- Fresh default `WorldAdapter()`; do not load additional seeds or enable any
  optional faculty.
- Set `OZMA_SEED_PERSIST_DISABLED=1` before importing application modules.
- Wrap the module global `domains.teach.categorise_by_shape` with a recorder
  that calls the original function and records each input and result.
- Invoke, once each and in this order, `seed_epistemic_codebook` with its
  default signals and `forced_choices=[]`, `seed_class_baseline_codebook` with
  default rows, and `seed_legal_hedging_codebook` with default rows.
- Preserve all observations in order; report helper attribution, type,
  attribute keys, returned category, loaded MetaShape count, and runtime/source
  provenance. Do not infer semantic correctness from the returned value.
- Repeat in a new process using the same locked code and compare the ordered
  observations byte-for-byte after excluding run-specific elapsed time.

## Admissibility

The probe is admissible only if persistence is disabled, no seed files change,
all three helper calls return, the wrapper records every default-classifier
invocation, and the independent comparison finds exact ordered equality across
two fresh processes. Failure or zero invocations is retained as evidence; do
not alter defaults or synthesize observations to force a successful path.

## Claim boundary

This samples three helper entrypoints on one default boot. It cannot establish
their production call frequency, external callers, behavior under a richer seed
profile, or MetaShape filing accuracy. Those require separate measurements.
